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

# Enable CORS for local cross-origin testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    metadata: Dict[str, str]
    status: str


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
    if payload.weights is not None:
        if not isinstance(payload.weights, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Weights must be a dictionary with numeric keys: skills, exp, edu, extras.",
            )
        for k, v in payload.weights.items():
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
            weights=payload.weights,
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
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
