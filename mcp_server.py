"""
MCP Server for FITMENT.AI Resume Screening Agent
Exposes candidate evaluation as a standard Model Context Protocol (MCP) tool.
"""

from __future__ import annotations

import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from agent_engine import MultiAgentEngine, AgentEngineError

# Load environment variables (.env)
load_dotenv()

# Create the MCP server instance
mcp = FastMCP("ResumeScreeningAgent")


@mcp.tool()
def screen_candidate(resume_text: str, job_description: str) -> str:
    """
    Analyzes a candidate resume against a target job description using multi-agent intelligence.
    Returns a comprehensive executive scorecard containing:
      - Overall fitment score (0-100) and verdict
      - Technical alignment and strengths
      - Critical competency gaps and missing skills
      - Red flags and career trajectory anomalies
      - 3 targeted interview probing questions
    """
    try:
        # Determine provider based on configured API keys
        if os.getenv("OPENAI_API_KEY"):
            provider = "OpenAI"
        elif os.getenv("GROQ_API_KEY"):
            provider = "Groq"
        else:
            provider = "OpenAI"

        engine = MultiAgentEngine(provider=provider)
        report = engine.run_evaluation(jd_text=job_description, resume_text=resume_text)
        return report.raw_markdown
    except AgentEngineError as agent_err:
        return f"Fitment Agent Error: {agent_err}"
    except Exception as exc:
        return f"Unexpected error during candidate screening: {exc}"


if __name__ == "__main__":
    mcp.run()
