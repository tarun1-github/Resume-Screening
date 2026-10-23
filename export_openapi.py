"""
FITMENT.AI - OpenAPI and Swagger Spec Exporter for Power Platform
Derives authoritative OpenAPI 3.0.3 and Swagger 2.0 schemas directly from FastAPI application.
Ensures 100% compatibility with Microsoft Power Platform Custom Connectors and Copilot Studio.
"""

from __future__ import annotations

import copy
import json
import os
import sys
from typing import Any, Dict

from api import app


def _clean_schema_30(obj: Any) -> Any:
    """Recursively converts OpenAPI 3.1.0 constructs (anyOf nullables) to OpenAPI 3.0.x."""
    if isinstance(obj, dict):
        # Convert 3.1 anyOf [{type: X}, {type: "null"}] to 3.0 nullable: true
        if "anyOf" in obj and len(obj["anyOf"]) == 2:
            types = obj["anyOf"]
            null_item = next((item for item in types if item.get("type") == "null"), None)
            val_item = next((item for item in types if item.get("type") != "null"), None)
            if null_item and val_item:
                cleaned = copy.deepcopy(val_item)
                cleaned["nullable"] = True
                if "title" in obj:
                    cleaned["title"] = obj["title"]
                if "description" in obj:
                    cleaned["description"] = obj["description"]
                return _clean_schema_30(cleaned)

        cleaned_dict = {}
        for k, v in obj.items():
            if k == "exclusiveMinimum":
                continue
            cleaned_dict[k] = _clean_schema_30(v)
        return cleaned_dict
    elif isinstance(obj, list):
        return [_clean_schema_30(item) for item in obj]
    return obj


def _add_powerplatform_metadata(schemas: Dict[str, Any]) -> None:
    """Enriches schemas with x-ms-summary annotations for Power Automate dynamic content."""
    summary_map = {
        "candidate_name": "Candidate Name",
        "match_score": "Match Score (0-100)",
        "score_type": "Scoring Methodology",
        "verdict": "Screening Verdict",
        "recommendation": "Recruitment Recommendation",
        "skills_matched": "Skills Matched",
        "missing_skills": "Missing Skills",
        "supporting_evidence": "Supporting Evidence Quotes",
        "total_experience_detected": "Total Experience Detected",
        "experience_assessment": "Experience Assessment",
        "certifications_detected": "Certifications Detected",
        "interview_questions": "Targeted Interview Questions",
        "human_review_required": "Human Review Required Flag",
        "metadata": "Candidate Profile Metadata",
        "status": "Response Status",
        "skill_gaps_analysis": "Skill Gaps Breakdown",
        "grounded_recommendation": "Grounded Recommendation Details",
        "job_description": "Job Description Text",
        "resume_text": "Candidate Resume Plain Text",
        "weights": "Scoring Weights (Optional)",
    }

    for schema in schemas.values():
        if isinstance(schema, dict) and "properties" in schema:
            for prop_name, prop in schema["properties"].items():
                if isinstance(prop, dict) and prop_name in summary_map:
                    prop["x-ms-summary"] = summary_map[prop_name]


def generate_openapi_30() -> Dict[str, Any]:
    """Generates valid OpenAPI 3.0.3 specification from FastAPI app."""
    raw = copy.deepcopy(app.openapi())
    spec = _clean_schema_30(raw)

    spec["openapi"] = "3.0.3"
    spec["info"] = {
        "title": "FITMENT.AI Screening API",
        "version": "1.0.0",
        "description": (
            "FITMENT.AI deterministic resume screening service integrated with Microsoft Power Platform, "
            "Power Automate, and Copilot Studio. 100% offline rule-based scoring with zero external LLM dependencies."
        ),
        "contact": {
            "name": "FITMENT.AI Architecture Team",
            "url": "https://github.com/tarun1-github/Resume-Screening",
        },
    }

    spec["servers"] = [
        {
            "url": "http://127.0.0.1:8001",
            "description": "Local FITMENT.AI Service (Default Port 8001)",
        },
        {
            "url": "http://localhost:8000",
            "description": "Local FITMENT.AI Service (Alternative Port 8000)",
        },
    ]

    # Operation IDs and Power Platform metadata
    paths = spec.get("paths", {})
    if "/api/v1/screen-text" in paths and "post" in paths["/api/v1/screen-text"]:
        op = paths["/api/v1/screen-text"]["post"]
        op["operationId"] = "ScreenCandidateText"
        op["summary"] = "Screen Candidate Text"
        op["description"] = (
            "Evaluates candidate resume text against job description text deterministically. "
            "Returns score, matched/missing skills, citations, and interview probes."
        )
        op["x-ms-visibility"] = "important"

    if "/health" in paths and "get" in paths["/health"]:
        op = paths["/health"]["get"]
        op["operationId"] = "GetHealthStatus"
        op["summary"] = "Health Check"
        op["description"] = "Verifies service availability and zero-LLM operational mode."

    schemas = spec.get("components", {}).get("schemas", {})
    _add_powerplatform_metadata(schemas)

    return spec


def _clean_schema_20(obj: Any) -> Any:
    """Recursively converts schemas to strict Swagger 2.0 (OpenAPI 2.0).
    Strips 'nullable' and converts anyOf constructs unsupported by Swagger 2.0 meta-schema.
    In Swagger 2.0, optional fields are defined without nullable and omitted from required.
    """
    if isinstance(obj, dict):
        if "anyOf" in obj:
            options = [item for item in obj["anyOf"] if item.get("type") != "null"]
            if options:
                first_opt = copy.deepcopy(options[0])
                cleaned_opt = _clean_schema_20(first_opt)
                if "title" in obj and "title" not in cleaned_opt:
                    cleaned_opt["title"] = obj["title"]
                if "description" in obj and "description" not in cleaned_opt:
                    cleaned_opt["description"] = obj["description"]
                return cleaned_opt
            return {"type": "string"}

        cleaned_dict = {}
        for k, v in obj.items():
            if k == "nullable":
                continue
            if k in ("exclusiveMinimum", "exclusiveMaximum") and not isinstance(v, bool):
                continue
            cleaned_dict[k] = _clean_schema_20(v)
        return cleaned_dict
    elif isinstance(obj, list):
        return [_clean_schema_20(item) for item in obj]
    return obj


def generate_swagger_20() -> Dict[str, Any]:
    """Generates valid Swagger 2.0 (OpenAPI 2.0) specification from FastAPI app."""
    openapi_spec = generate_openapi_30()

    swagger_spec: Dict[str, Any] = {
        "swagger": "2.0",
        "info": openapi_spec["info"],
        "host": "127.0.0.1:8001",
        "basePath": "/",
        "schemes": ["http"],
        "consumes": ["application/json"],
        "produces": ["application/json"],
        "paths": {},
        "definitions": {},
    }

    # Convert schemas to Swagger 2.0 definitions (rewriting $ref)
    schemas_raw = openapi_spec.get("components", {}).get("schemas", {})
    schemas_str = json.dumps(schemas_raw).replace("#/components/schemas/", "#/definitions/")
    definitions = json.loads(schemas_str)
    swagger_spec["definitions"] = _clean_schema_20(definitions)

    # Convert paths
    for path, path_item in openapi_spec.get("paths", {}).items():
        swagger_path_item: Dict[str, Any] = {}
        for method, operation in path_item.items():
            swagger_op: Dict[str, Any] = {
                "operationId": operation.get("operationId", f"{method}_{path}"),
                "summary": operation.get("summary", ""),
                "description": operation.get("description", ""),
                "parameters": [],
                "responses": {},
            }
            if "x-ms-visibility" in operation:
                swagger_op["x-ms-visibility"] = operation["x-ms-visibility"]

            # Convert requestBody to body parameter
            if "requestBody" in operation:
                rb = operation["requestBody"]
                schema = (
                    rb.get("content", {})
                    .get("application/json", {})
                    .get("schema", {})
                )
                schema_str = json.dumps(schema).replace("#/components/schemas/", "#/definitions/")
                cleaned_body_schema = _clean_schema_20(json.loads(schema_str))
                swagger_op["parameters"].append(
                    {
                        "name": "body",
                        "in": "body",
                        "required": rb.get("required", True),
                        "description": "Screening request payload containing job description and resume text.",
                        "schema": cleaned_body_schema,
                    }
                )

            # Convert responses
            for status_code, resp in operation.get("responses", {}).items():
                swagger_resp: Dict[str, Any] = {
                    "description": resp.get("description", "Response"),
                }
                if "content" in resp and "application/json" in resp["content"]:
                    content_schema = resp["content"]["application/json"].get("schema", {})
                    content_schema_str = json.dumps(content_schema).replace(
                        "#/components/schemas/", "#/definitions/"
                    )
                    swagger_resp["schema"] = _clean_schema_20(json.loads(content_schema_str))
                swagger_op["responses"][status_code] = swagger_resp

            swagger_path_item[method] = swagger_op
        swagger_spec["paths"][path] = swagger_path_item

    return _clean_schema_20(swagger_spec)



def export_specs(output_dir: str = ".") -> Tuple[str, str]:
    """Generates and writes both OpenAPI 3.0 and Swagger 2.0 specifications."""
    oa30 = generate_openapi_30()
    sw20 = generate_swagger_20()

    oa30_path = os.path.join(output_dir, "fitmentai_connector_openapi_v2.json")
    sw20_path = os.path.join(output_dir, "fitmentai_connector_swagger2_v2.json")

    with open(oa30_path, "w", encoding="utf-8") as f:
        json.dump(oa30, f, indent=2)

    with open(sw20_path, "w", encoding="utf-8") as f:
        json.dump(sw20, f, indent=2)

    return oa30_path, sw20_path


if __name__ == "__main__":
    from typing import Tuple
    p1, p2 = export_specs(".")
    print(f"Successfully generated Power Platform OpenAPI specs:\n - {p1}\n - {p2}")
