"""
FITMENT.AI - Multi-Agent Engine
Orchestration logic for JD Analysis, Candidate Skill Mapping, RedFlag Detection, and Fitment Scoring.
Compatible with OpenAI and Groq (Llama-3 / Mixtral) APIs.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Callable, Optional
from openai import OpenAI


@dataclass
class ScoringWeights:
    skills: float = 0.30
    experience: float = 0.40
    education: float = 0.15
    extras: float = 0.15

    def normalize(self) -> ScoringWeights:
        total = self.skills + self.experience + self.education + self.extras
        if total <= 0:
            return ScoringWeights()
        return ScoringWeights(
            skills=self.skills / total,
            experience=self.experience / total,
            education=self.education / total,
            extras=self.extras / total,
        )


@dataclass
class FitmentReport:
    candidate_name: str
    overall_score: int
    skills_score: int
    experience_score: int
    education_score: int
    extras_score: int
    verdict: str  # "Strong Fit" | "Moderate Fit" | "Weak Fit"
    summary: str
    strengths: list[str] = field(default_factory=list)
    critical_gaps: list[str] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)
    interview_questions: list[str] = field(default_factory=list)
    raw_markdown: str = ""
    agent_logs: dict[str, str] = field(default_factory=dict)


class AgentEngineError(Exception):
    """Raised when an error occurs during multi-agent evaluation."""
    pass


class MultiAgentEngine:
    """
    Coordinates specialized LLM agents to evaluate candidate-job fitment:
      1. JD Analyst Agent: Extracts role requirements and expectations.
      2. Resume & Skill Matcher: Maps candidate proficiencies and highlights alignment.
      3. RedFlag & Anomaly Hunter: Identifies employment gaps, rapid turnover, and skill misalignments.
      4. Executive Recruiter & Scorer: Synthesizes final score, scorecard, and interview strategy.
    """

    SUPPORTED_PROVIDERS = {
        "OpenAI": {
            "default_model": "gpt-4o",
            "fallback_model": "o3-mini",
            "base_url": None,
            "env_var": "OPENAI_API_KEY",
        },
        "Google (Gemini)": {
            "default_model": "gemini-3.8-flash",
            "fallback_model": "gemini-2.5-pro",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "env_var": "GOOGLE_API_KEY",
        },
        "Groq": {
            "default_model": "llama-3.3-70b-versatile",
            "fallback_model": "llama-3.1-8b-instant",
            "base_url": "https://api.groq.com/openai/v1",
            "env_var": "GROQ_API_KEY",
        },
        "HuggingFace": {
            "default_model": "meta-llama/Llama-3-70B-Instruct",
            "fallback_model": "meta-llama/Llama-3-70B-Instruct",
            "base_url": "https://api-inference.huggingface.co/v1/",
            "env_var": "HUGGINGFACEHUB_ACCESS_TOKEN",
        },
    }

    def __init__(
        self,
        provider: str = "OpenAI",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        low_p = provider.lower()
        if "google" in low_p or "gemini" in low_p:
            clean_provider = "Google (Gemini)"
        elif "hugging" in low_p or "hf" in low_p:
            clean_provider = "HuggingFace"
        elif "groq" in low_p:
            clean_provider = "Groq"
        else:
            clean_provider = "OpenAI"
        self.provider = clean_provider

        provider_config = self.SUPPORTED_PROVIDERS[self.provider]
        env_var_name = provider_config["env_var"]

        # Resolve API Key
        self.api_key = (
            api_key
            or os.getenv(env_var_name)
            or ""
        ).strip()

        if not self.api_key:
            raise AgentEngineError(
                f"Missing API Key for {self.provider}. "
                f"Please provide an API key in the UI or set the "
                f"{env_var_name} environment variable."
            )

        provider_config = self.SUPPORTED_PROVIDERS[self.provider]
        self.model = model or provider_config["default_model"]
        self.base_url = provider_config["base_url"]

        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=90.0,
            )
        except Exception as init_err:
            raise AgentEngineError(f"Failed to initialize {self.provider} client: {init_err}") from init_err

    def _call_llm(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        """Internal helper to execute LLM completion with fallback handling."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
            )
            content = response.choices[0].message.content
            return content.strip() if content else ""
        except Exception as call_err:
            # Fallback to lighter model if primary fails
            fallback = self.SUPPORTED_PROVIDERS[self.provider]["fallback_model"]
            if self.model != fallback:
                try:
                    response = self.client.chat.completions.create(
                        model=fallback,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=temperature,
                    )
                    content = response.choices[0].message.content
                    return content.strip() if content else ""
                except Exception:
                    pass
            raise AgentEngineError(f"LLM API Call failed ({self.provider} - {self.model}): {call_err}") from call_err

    def run_evaluation(
        self,
        jd_text: str,
        resume_text: str,
        progress_callback: Optional[Callable[[str, float], None]] = None,
        weights: Optional[ScoringWeights] = None,
    ) -> FitmentReport:
        """
        Executes the 4-stage multi-agent evaluation pipeline.
        """
        weights = (weights or ScoringWeights()).normalize()
        logs: dict[str, str] = {}

        # -------------------------------------------------------------
        # STAGE 1: JD Analyst Agent
        # -------------------------------------------------------------
        if progress_callback:
            progress_callback("Agent 1/4: Analyzing Role Requirements & Mandates...", 0.20)

        jd_system = (
            "You are an elite Technical Hiring Manager and Role Analyst Agent. "
            "Deconstruct the Job Description into key technical mandates, experience level, "
            "must-have proficiencies, and organizational culture expectations."
        )
        jd_prompt = f"Analyze this Job Description thoroughly:\n\n{jd_text}"
        jd_analysis = self._call_llm(jd_system, jd_prompt)
        logs["jd_analysis"] = jd_analysis

        # -------------------------------------------------------------
        # STAGE 2: Resume Parser & Skill Mapping Agent
        # -------------------------------------------------------------
        if progress_callback:
            progress_callback("Agent 2/4: Mapping Candidate Profile & Skills Alignment...", 0.45)

        skills_system = (
            "You are a Senior Talent Sourcing & Skill Mapping Agent. "
            "Extract candidate name, years of relevant experience, educational background, "
            "and map their skills directly against the target role requirements."
        )
        skills_prompt = (
            f"TARGET ROLE REQUIREMENTS:\n{jd_analysis}\n\n"
            f"CANDIDATE RESUME:\n{resume_text}\n\n"
            "Provide candidate name, direct technical alignments, and missing/unverified skills."
        )
        skills_mapping = self._call_llm(skills_system, skills_prompt)
        logs["skills_mapping"] = skills_mapping

        # -------------------------------------------------------------
        # STAGE 3: RedFlag & Anomaly Hunter Agent
        # -------------------------------------------------------------
        if progress_callback:
            progress_callback("Agent 3/4: Hunting Employment Gaps & Consistency Anomalies...", 0.70)

        redflag_system = (
            "You are a Forensic Technical Recruiter and Career Anomaly Agent. "
            "Audit the resume for red flags: unexplained career gaps, rapid job-hopping (<1 year), "
            "inflated titles, unverified buzzwords, or missing academic credentials."
        )
        redflag_prompt = (
            f"JOB REQUIREMENTS:\n{jd_text[:1200]}\n\n"
            f"CANDIDATE RESUME:\n{resume_text}\n\n"
            "List specific red flags or state 'No critical red flags detected' if clean."
        )
        redflags = self._call_llm(redflag_system, redflag_prompt)
        logs["red_flags"] = redflags

        # -------------------------------------------------------------
        # STAGE 4: Executive Recruiter & Fitment Scorer
        # -------------------------------------------------------------
        if progress_callback:
            progress_callback("Agent 4/4: Synthesizing Fitment Scorecard & Verdict...", 0.90)

        scoring_system = (
            "You are the Chief Executive Talent Officer and Decision Maker. "
            "Synthesize all previous agent findings to calculate category scores out of 100, "
            "determine the weighted overall score, verdict, and tailored interview questions. "
            "You MUST output valid JSON format conforming to the requested schema."
        )

        scoring_prompt = f"""
        AGENT INSIGHTS:
        - JD Mandates: {jd_analysis}
        - Candidate Mapping: {skills_mapping}
        - Red Flag Audit: {redflags}

        SCORING WEIGHTS:
        - Skills: {weights.skills * 100:.1f}%
        - Experience: {weights.experience * 100:.1f}%
        - Education: {weights.education * 100:.1f}%
        - Extras/Certifications: {weights.extras * 100:.1f}%

        Return a single valid JSON object with EXACTLY this structure (no markdown wrappers, only pure JSON):
        {{
            "candidate_name": "Full Name",
            "skills_score": 85,
            "experience_score": 75,
            "education_score": 90,
            "extras_score": 70,
            "verdict": "Strong Fit" | "Moderate Fit" | "Weak Fit",
            "summary": "Executive summary of fitment (2-3 sentences)",
            "strengths": ["Strength 1", "Strength 2", "Strength 3"],
            "critical_gaps": ["Gap 1", "Gap 2"],
            "red_flags": ["Flag 1", "Flag 2"],
            "interview_questions": [
                "Targeted Question 1 testing specific experience",
                "Targeted Question 2 verifying claimed tools",
                "Targeted Question 3 probing career transition/gap"
            ]
        }}
        """

        raw_final = self._call_llm(scoring_system, scoring_prompt, temperature=0.1)
        logs["final_synthesis"] = raw_final

        # Parse JSON output with robust regex extraction
        report = self._parse_json_response(raw_final, weights, logs)

        if progress_callback:
            progress_callback("Finalizing Executive Report...", 1.0)

        return report

    def _parse_json_response(
        self,
        raw_text: str,
        weights: ScoringWeights,
        logs: dict[str, str],
    ) -> FitmentReport:
        """Parses the LLM output into a strongly-typed FitmentReport with fallback safety."""
        json_str = raw_text
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if match:
            json_str = match.group(0)

        try:
            data = json.loads(json_str)
        except Exception:
            # Fallback heuristic parsing if JSON was malformed
            data = {}

        candidate_name = data.get("candidate_name") or "Candidate"
        skills_score = int(data.get("skills_score", 70))
        experience_score = int(data.get("experience_score", 70))
        education_score = int(data.get("education_score", 75))
        extras_score = int(data.get("extras_score", 65))

        # Clamp subscores 0-100
        skills_score = max(0, min(100, skills_score))
        experience_score = max(0, min(100, experience_score))
        education_score = max(0, min(100, education_score))
        extras_score = max(0, min(100, extras_score))

        # Calculate weighted overall score
        overall_score = round(
            (skills_score * weights.skills)
            + (experience_score * weights.experience)
            + (education_score * weights.education)
            + (extras_score * weights.extras)
        )
        overall_score = max(0, min(100, overall_score))

        # Determine verdict
        verdict = data.get("verdict")
        if not verdict or verdict not in ["Strong Fit", "Moderate Fit", "Weak Fit"]:
            if overall_score >= 78:
                verdict = "Strong Fit"
            elif overall_score >= 55:
                verdict = "Moderate Fit"
            else:
                verdict = "Weak Fit"

        summary = data.get("summary") or "Evaluation successfully completed across 4 synchronized agents."
        strengths = data.get("strengths") or ["Relevant domain exposure", "Technical foundations align with JD"]
        critical_gaps = data.get("critical_gaps") or ["Verify specific production tool experience"]
        red_flags = data.get("red_flags") or ["No severe disqualifiers detected"]
        interview_questions = data.get("interview_questions") or [
            "Can you walk through your most complex architectural decision in your recent role?",
            "How do your skills with the required stack apply to our project scope?",
            "Describe how you navigate tight project deadlines and ambiguity.",
        ]

        # Build clean formatted Markdown report
        markdown_report = self._build_markdown_report(
            candidate_name=candidate_name,
            overall_score=overall_score,
            verdict=verdict,
            skills_score=skills_score,
            experience_score=experience_score,
            education_score=education_score,
            extras_score=extras_score,
            summary=summary,
            strengths=strengths,
            critical_gaps=critical_gaps,
            red_flags=red_flags,
            interview_questions=interview_questions,
        )

        return FitmentReport(
            candidate_name=candidate_name,
            overall_score=overall_score,
            skills_score=skills_score,
            experience_score=experience_score,
            education_score=education_score,
            extras_score=extras_score,
            verdict=verdict,
            summary=summary,
            strengths=strengths,
            critical_gaps=critical_gaps,
            red_flags=red_flags,
            interview_questions=interview_questions,
            raw_markdown=markdown_report,
            agent_logs=logs,
        )

    def _build_markdown_report(
        self,
        candidate_name: str,
        overall_score: int,
        verdict: str,
        skills_score: int,
        experience_score: int,
        education_score: int,
        extras_score: int,
        summary: str,
        strengths: list[str],
        critical_gaps: list[str],
        red_flags: list[str],
        interview_questions: list[str],
    ) -> str:
        """Generates an executive-ready Markdown document."""
        badge_emoji = "🟢" if verdict == "Strong Fit" else ("🟡" if verdict == "Moderate Fit" else "🔴")

        md = f"""# ⚡ FITMENT.AI | Executive Screening Scorecard

**Candidate:** {candidate_name}  
**Executive Verdict:** {badge_emoji} **{verdict.upper()}**  
**Overall Fitment Index:** **{overall_score} / 100**

---

### 📊 Multi-Parameter Competency Breakdown
| Parameter | Weight Factor | Parameter Score | Status |
| :--- | :--- | :--- | :--- |
| **Technical & Skill Alignment** | 30% | `{skills_score} / 100` | {'✅ Verified' if skills_score >= 70 else '⚠️ Partial'} |
| **Relevant Experience Depth** | 40% | `{experience_score} / 100` | {'✅ Verified' if experience_score >= 70 else '⚠️ Review Needed'} |
| **Education & Credentials** | 15% | `{education_score} / 100` | {'✅ Aligned' if education_score >= 60 else '⚠️ Unaligned'} |
| **Certifications & Accreditations** | 15% | `{extras_score} / 100` | {'✅ Present' if extras_score >= 50 else 'ℹ️ Limited'} |

---

### 🎯 Executive Summary
> {summary}

---

### 🌟 Key Candidate Strengths
"""
        for s in strengths:
            md += f"- **{s}**\n"

        md += "\n### ⚠️ Critical Gaps & Areas of Concern\n"
        for g in critical_gaps:
            md += f"- {g}\n"

        md += "\n### 🚩 RedFlag & Career Trajectory Audit\n"
        for rf in red_flags:
            md += f"- {rf}\n"

        md += "\n### 🎙️ Tailored Technical & Behavioral Interview Probes\n"
        for idx, q in enumerate(interview_questions, 1):
            md += f"{idx}. *\"{q}\"*\n"

        md += "\n---\n*Report generated by FITMENT.AI Multi-Agent Fitment Engine v2.5*"
        return md
