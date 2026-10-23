"""
FITMENT.AI - Local FastAPI Service
Exposes deterministic resume screening endpoints for local testing and workflow integration.
Zero external LLM API dependencies.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import parser
from deterministic_engine import evaluate_candidate_deterministically


# Setup structured logging without exposing sensitive resume data
logger = logging.getLogger("fitment_api")
logger.setLevel(logging.INFO)

app = FastAPI(
    title="FITMENT.AI Screening API",
    version="1.0.0",
    description="Deterministic resume screening and keyword evidence extractor. 100% offline rule-based scoring.",
)

# Enable CORS for local cross-origin testing with secure origin regex
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScreenTextRequest(BaseModel):
    job_description: str = Field(..., description="Target Job Description text.")
    resume_text: str = Field(..., description="Candidate Resume plain text.")
    weights: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional scoring weights: skills, exp, edu, extras.",
    )


class CandidateMetadata(BaseModel):
    name: str = "Candidate Profile"
    mobile: Optional[str] = "Not available in CV"
    email: Optional[str] = "Not Specified"
    location: Optional[str] = "Not Specified"
    dob: Optional[str] = "Not Specified"
    total_exp: Optional[str] = "Not Specified"
    relevant_exp: Optional[str] = "Not Specified"
    organization: Optional[str] = "Not Detected (Requires human verification)"
    current_designation: Optional[str] = "Not Detected (Requires human verification)"
    previous_organizations: List[str] = Field(default_factory=list)
    education: Optional[str] = "Not Detected (Requires human verification)"
    certifications: List[str] = Field(default_factory=list)

    model_config = {"extra": "allow"}


class SkillGapItem(BaseModel):
    skill: str
    rationale: str
    tier: Optional[str] = None

    model_config = {"extra": "allow"}


class SkillGapsAnalysis(BaseModel):
    has_data: bool
    message: Optional[str] = None
    mandatory_gaps: List[SkillGapItem] = Field(default_factory=list)
    preferred_gaps: List[SkillGapItem] = Field(default_factory=list)
    core_gaps: List[SkillGapItem] = Field(default_factory=list)
    matched_skills: List[str] = Field(default_factory=list)
    undetermined_skills: List[str] = Field(default_factory=list)
    prioritized_gaps: List[SkillGapItem] = Field(default_factory=list)

    model_config = {"extra": "allow"}


class GroundedRecommendation(BaseModel):
    status: str
    action: str
    score: int
    summary: str
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    interview_probes: List[str] = Field(default_factory=list)
    is_llm: bool = False
    engine_label: str

    model_config = {"extra": "allow"}


class ScreeningResponse(BaseModel):
    candidate_name: str
    match_score: int
    score_type: str
    verdict: str
    recommendation: str
    skills_matched: List[str]
    missing_skills: List[str]
    supporting_evidence: Dict[str, List[str]]
    total_experience_detected: str
    experience_assessment: str
    certifications_detected: List[str]
    interview_questions: List[str]
    human_review_required: bool
    metadata: CandidateMetadata = Field(default_factory=CandidateMetadata)
    status: str
    skill_gaps_analysis: Optional[SkillGapsAnalysis] = None
    grounded_recommendation: Optional[GroundedRecommendation] = None

    model_config = {"extra": "allow"}



@app.get("/health", status_code=status.HTTP_200_OK)
def health_check() -> Dict[str, str]:
    """Health check endpoint confirming service status and zero LLM dependency."""
    return {
        "status": "healthy",
        "service": "FITMENT.AI Deterministic Screener",
        "llm_dependency": "none",
    }


def _process_screen_text(payload: ScreenTextRequest) -> Dict[str, Any]:
    """Core request processor validating inputs and invoking the deterministic engine."""
    # 1. Validate Job Description
    if not payload.job_description or not payload.job_description.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description cannot be empty.",
        )

    try:
        clean_jd = parser.sanitize_job_description(payload.job_description, min_characters=20)
    except parser.EmptyDocumentError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    # 2. Validate Resume Text
    if not payload.resume_text or not payload.resume_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume text cannot be empty.",
        )

    clean_resume = parser.clean_text(payload.resume_text)
    if len(clean_resume) < 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Resume content too brief ({len(clean_resume)} chars). Minimum 30 characters required.",
        )

    # 3. Validate Optional Weights
    weights = payload.weights
    if weights is not None:
        if not isinstance(weights, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Weights must be a dictionary with numeric keys: skills, exp, edu, extras.",
            )
        # An empty dictionary {} indicates weights were omitted in form/connector -> use defaults
        if len(weights) == 0:
            weights = None
        else:
            for k, v in weights.items():
                if not isinstance(v, (int, float)) or v < 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Weight for '{k}' must be a non-negative number.",
                    )

    # 4. Execute Deterministic Evaluation
    try:
        result = evaluate_candidate_deterministically(
            jd_text=clean_jd,
            resume_text=clean_resume,
            weights=weights,
        )
        return result
    except parser.EmptyDocumentError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except Exception as exc:
        logger.error(f"Error during deterministic screening: {type(exc).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during deterministic screening evaluation.",
        )


@app.post(
    "/api/v1/screen-text",
    response_model=ScreeningResponse,
    status_code=status.HTTP_200_OK,
)
def screen_text(payload: ScreenTextRequest) -> Dict[str, Any]:
    """
    Evaluates candidate resume text against job description text.
    Returns deterministic score, matched/missing skills, evidence citations, and interview probes.
    """
    return _process_screen_text(payload)


@app.post(
    "/screen-text",
    response_model=ScreeningResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def screen_text_alias(payload: ScreenTextRequest) -> Dict[str, Any]:
    """Convenience alias for root /screen-text."""
    return _process_screen_text(payload)


if __name__ == "__main__":
    import os
    import uvicorn
    host = os.getenv("FITMENT_API_HOST", "127.0.0.1")
    port = int(os.getenv("PORT", os.getenv("FITMENT_API_PORT", "8000")))
    uvicorn.run("api:app", host=host, port=port, reload=True)

