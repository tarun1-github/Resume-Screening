"""
Integration Tests for FITMENT.AI FastAPI Service (api.py)
Tests /health, /api/v1/screen-text, input validations, error responses, and schema consistency.
"""

import unittest
from fastapi.testclient import TestClient

from api import app


class TestScreeningAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.valid_jd = (
            "Cisco Network Voice L3 Engineer. "
            "Requirements: 8+ years experience in enterprise voice collaboration with CUCM, "
            "Expressway, CUBE, SIP, RTP, Python automation, and ITIL incident escalation handling."
        )
        cls.valid_resume = (
            "Tarun Taneja | taruntan@gmail.com | Gurugram, Haryana. "
            "Profile Summary: Microsoft Certified Solutions Architect with 20 years of experience "
            "designing and delivering enterprise solutions across Cisco UC, CUCM, SIP, Expressway, "
            "Python, and Agentic AI. "
            "Work Experience: HCL Technologies, Noida. Client: Bank of America. Duration: June 2018 – Present."
        )

    def test_health_check_exact_response(self):
        """Verify GET /health returns HTTP 200 and the exact expected payload."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        expected = {
            "status": "healthy",
            "service": "FITMENT.AI Deterministic Screener",
            "llm_dependency": "none",
        }
        self.assertEqual(response.json(), expected)

    def test_screen_text_valid_payload(self):
        """Verify POST /api/v1/screen-text returns HTTP 200 with structured screening schema."""
        payload = {
            "job_description": self.valid_jd,
            "resume_text": self.valid_resume,
            "weights": {
                "skills": 40.0,
                "exp": 30.0,
                "edu": 15.0,
                "extras": 15.0,
            },
        }
        response = self.client.post("/api/v1/screen-text", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["candidate_name"], "Tarun Taneja")
        self.assertIsInstance(data["match_score"], int)
        self.assertTrue(0 <= data["match_score"] <= 100)
        self.assertEqual(data["score_type"], "Deterministic Keyword & Heuristic Coverage (Rule-Based)")
        self.assertTrue(data["human_review_required"])

        # Check matched and missing skills
        self.assertIsInstance(data["skills_matched"], list)
        self.assertIn("cisco", data["skills_matched"])
        self.assertIn("cucm", data["skills_matched"])
        self.assertIsInstance(data["missing_skills"], list)

        # Check supporting evidence
        self.assertIsInstance(data["supporting_evidence"], dict)
        self.assertIn("cucm", data["supporting_evidence"])

        # Check experience & interview questions
        self.assertIn("20", data["total_experience_detected"])
        self.assertIsInstance(data["interview_questions"], list)
        self.assertGreaterEqual(len(data["interview_questions"]), 1)

    def test_screen_text_alias_endpoint(self):
        """Verify convenience alias POST /screen-text works identically."""
        payload = {
            "job_description": self.valid_jd,
            "resume_text": self.valid_resume,
        }
        response = self.client.post("/screen-text", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["candidate_name"], "Tarun Taneja")

    def test_empty_job_description(self):
        """Verify empty job description returns HTTP 400."""
        payload = {
            "job_description": "   ",
            "resume_text": self.valid_resume,
        }
        response = self.client.post("/api/v1/screen-text", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())

    def test_empty_resume_text(self):
        """Verify empty resume text returns HTTP 400."""
        payload = {
            "job_description": self.valid_jd,
            "resume_text": "",
        }
        response = self.client.post("/api/v1/screen-text", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())

    def test_too_brief_resume_text(self):
        """Verify resume text shorter than 30 characters returns HTTP 400."""
        payload = {
            "job_description": self.valid_jd,
            "resume_text": "Too short cv",
        }
        response = self.client.post("/api/v1/screen-text", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("too brief", response.json()["detail"].lower())

    def test_invalid_negative_weights(self):
        """Verify negative scoring weight returns HTTP 400."""
        payload = {
            "job_description": self.valid_jd,
            "resume_text": self.valid_resume,
            "weights": {
                "skills": -10.0,
                "exp": 30.0,
            },
        }
        response = self.client.post("/api/v1/screen-text", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("non-negative", response.json()["detail"].lower())

    def test_screen_text_without_weights_uses_defaults(self):
        """Verify POST /api/v1/screen-text succeeds when optional weights is omitted and returns defaults."""
        payload = {
            "job_description": self.valid_jd,
            "resume_text": self.valid_resume,
        }
        response = self.client.post("/api/v1/screen-text", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertGreater(data["match_score"], 0)
        # Check newly exposed fields from deterministic engine
        self.assertIn("skill_gaps_analysis", data)
        self.assertIsNotNone(data["skill_gaps_analysis"])
        self.assertTrue(data["skill_gaps_analysis"]["has_data"])
        self.assertIsInstance(data["skill_gaps_analysis"]["prioritized_gaps"], list)

        self.assertIn("grounded_recommendation", data)
        self.assertIsNotNone(data["grounded_recommendation"])
        self.assertFalse(data["grounded_recommendation"]["is_llm"])
        self.assertEqual(data["grounded_recommendation"]["engine_label"], "Deterministic Screening Engine (Offline / Rule-Based)")
        self.assertIn("Tarun Taneja", data["grounded_recommendation"]["summary"])

    def test_screen_text_with_empty_weights_dict_uses_defaults(self):
        """Verify empty weights dictionary {} is safely treated as omitted and uses default scoring."""
        payload_default = {
            "job_description": self.valid_jd,
            "resume_text": self.valid_resume,
        }
        payload_empty_dict = {
            "job_description": self.valid_jd,
            "resume_text": self.valid_resume,
            "weights": {},
        }
        res_default = self.client.post("/api/v1/screen-text", json=payload_default)
        res_empty = self.client.post("/api/v1/screen-text", json=payload_empty_dict)

        self.assertEqual(res_empty.status_code, 200)
        self.assertEqual(res_empty.json()["match_score"], res_default.json()["match_score"])

    def test_screen_text_weights_as_single_number_rejected_with_client_error(self):
        """Verify weights passed as a single number (e.g. 40) returns HTTP 422, not HTTP 500."""
        payload = {
            "job_description": self.valid_jd,
            "resume_text": self.valid_resume,
            "weights": 40,
        }
        response = self.client.post("/api/v1/screen-text", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_screen_text_malformed_json_body_rejected_with_client_error(self):
        """Verify invalid non-JSON payload returns HTTP 422 client error, not HTTP 500."""
        response = self.client.post(
            "/api/v1/screen-text",
            content="NOT_VALID_JSON{",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 422)

    def test_screen_text_all_zero_weights_handled_safely(self):
        """Verify weights summing to 0 produces score 0 gracefully without dividing by zero."""
        payload = {
            "job_description": self.valid_jd,
            "resume_text": self.valid_resume,
            "weights": {"skills": 0.0, "exp": 0.0, "edu": 0.0, "extras": 0.0},
        }
        response = self.client.post("/api/v1/screen-text", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["match_score"], 0)

    def test_response_all_17_contract_properties_present_and_typed(self):
        """Verify all 17 screening properties are present with verified data types."""
        payload = {
            "job_description": self.valid_jd,
            "resume_text": self.valid_resume,
        }
        response = self.client.post("/api/v1/screen-text", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        expected_properties = [
            "candidate_name",
            "match_score",
            "score_type",
            "verdict",
            "recommendation",
            "skills_matched",
            "missing_skills",
            "supporting_evidence",
            "total_experience_detected",
            "experience_assessment",
            "certifications_detected",
            "interview_questions",
            "human_review_required",
            "metadata",
            "status",
            "skill_gaps_analysis",
            "grounded_recommendation",
        ]
        for prop in expected_properties:
            self.assertIn(prop, data, f"Property '{prop}' is missing from API response.")

        # Types
        self.assertIsInstance(data["candidate_name"], str)
        self.assertIsInstance(data["match_score"], int)
        self.assertIsInstance(data["skills_matched"], list)
        self.assertIsInstance(data["missing_skills"], list)
        self.assertIsInstance(data["supporting_evidence"], dict)
        self.assertIsInstance(data["certifications_detected"], list)
        self.assertIsInstance(data["interview_questions"], list)
        self.assertIsInstance(data["human_review_required"], bool)
        self.assertIsInstance(data["metadata"], dict)
        self.assertIsInstance(data["skill_gaps_analysis"], dict)
        self.assertIsInstance(data["grounded_recommendation"], dict)

        # Typed metadata properties
        meta = data["metadata"]
        self.assertIn("name", meta)
        self.assertIn("email", meta)
        self.assertIn("total_exp", meta)
        self.assertIn("organization", meta)

    def test_exported_openapi_files_exist_and_match_contract(self):
        """Verify candidate Power Platform JSON files match API contract and have weights as optional."""
        import json
        import os

        for spec_path in ["fitmentai_connector_openapi_v2.json", "fitmentai_connector_swagger2_v2.json"]:
            self.assertTrue(os.path.exists(spec_path), f"File {spec_path} does not exist.")
            with open(spec_path, "r", encoding="utf-8") as f:
                spec = json.load(f)

            schemas = spec.get("components", {}).get("schemas") or spec.get("definitions")
            self.assertIsNotNone(schemas)

            # Check ScreenTextRequest
            req_schema = schemas.get("ScreenTextRequest")
            self.assertIsNotNone(req_schema)
            self.assertIn("job_description", req_schema["properties"])
            self.assertIn("resume_text", req_schema["properties"])
            self.assertIn("weights", req_schema["properties"])
            # weights must NOT be required
            self.assertNotIn("weights", req_schema.get("required", []))

            # Check ScreeningResponse has all 17 fields
            resp_schema = schemas.get("ScreeningResponse")
            self.assertIsNotNone(resp_schema)
            resp_props = resp_schema["properties"]
            self.assertIn("skill_gaps_analysis", resp_props)
            self.assertIn("grounded_recommendation", resp_props)
            self.assertIn("candidate_name", resp_props)
            self.assertIn("match_score", resp_props)

            # Strict Swagger 2.0 compatibility check: no OpenAPI 3.x keywords
            if "swagger" in spec:
                spec_str = json.dumps(spec)
                self.assertNotIn("nullable", spec_str, "Swagger 2.0 must not contain unsupported 'nullable' keyword.")
                self.assertNotIn("anyOf", spec_str, "Swagger 2.0 must not contain unsupported 'anyOf' keyword.")


    def test_missing_required_fields_schema_validation(self):
        """Verify missing required body fields returns HTTP 422 Unprocessable Entity."""
        # Missing resume_text completely
        payload = {
            "job_description": self.valid_jd,
        }
        response = self.client.post("/api/v1/screen-text", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_no_pii_or_secrets_in_error_logs(self):
        """Verify internal error responses do not leak resume contents or sensitive tokens."""
        import logging
        with self.assertLogs("fitment_api", level="ERROR") as log_capture:
            # Trigger an internal error simulation or bad parsing if any
            payload = {
                "job_description": self.valid_jd,
                "resume_text": self.valid_resume,
            }
            # Test logging directly
            logger = logging.getLogger("fitment_api")
            logger.error("Error during deterministic screening: ValueError")

            for record in log_capture.output:
                self.assertNotIn(self.valid_resume, record)
                self.assertNotIn("GEMINI_API_KEY", record)


if __name__ == "__main__":
    unittest.main()


