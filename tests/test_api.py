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

    def test_missing_required_fields_schema_validation(self):
        """Verify missing required body fields returns HTTP 422 Unprocessable Entity."""
        # Missing resume_text completely
        payload = {
            "job_description": self.valid_jd,
        }
        response = self.client.post("/api/v1/screen-text", json=payload)
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
