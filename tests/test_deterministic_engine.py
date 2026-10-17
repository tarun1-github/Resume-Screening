"""
Unit Tests for FITMENT.AI Deterministic Screening Engine
Tests rule-based scoring, keyword matching, seniority analysis, and zero-LLM boundaries.
"""

import os
import unittest
import pytest

import parser
from deterministic_engine import (
    compute_candidate_experience,
    extract_candidate_metadata,
    find_evidence_snippets,
    evaluate_candidate_deterministically,
)


class TestDeterministicEngine(unittest.TestCase):

    def setUp(self):
        self.sample_jd = (
            "Cisco Network Voice L3 / Voice T2 Engineer. "
            "Requirements: 8-10 years of experience in enterprise networks with minimum 8+ years "
            "specifically in Cisco UC, CUCM, Expressway, CUBE, SIP, RTP, and Python automation. "
            "Strong knowledge of ITIL incident escalation handling."
        )
        self.sample_resume = (
            "Tarun Taneja | taruntan@gmail.com | Gurugram, Haryana. "
            "Profile Summary: Microsoft Certified Business Solutions Architect with 20 years of experience "
            "designing and delivering enterprise solutions across Cisco UC, CUCM, SIP, Expressway, "
            "and Python automation. "
            "Work Experience: "
            "Company Name: HCL Technologies, Noida. Client: Bank of America. Duration: June 2018 – Present. "
            "Earlier experience with CSC India from Dec'04 to Dec'05. "
            "Education: HSC, CBSE from Shiva Shiksha School in 1999. BA from Delhi University in 2009."
        )

    def test_matched_and_missing_skills(self):
        """Verify matched skills appear in intersection and unmentioned skills in missing list."""
        result = evaluate_candidate_deterministically(self.sample_jd, self.sample_resume)

        self.assertIn("skills_matched", result)
        self.assertIn("missing_skills", result)

        matched = result["skills_matched"]
        missing = result["missing_skills"]

        # Expected matches
        for expected in ["cisco", "cucm", "expressway", "python", "sip"]:
            self.assertIn(expected, matched, f"Expected '{expected}' to be in skills_matched")

        # Expected missing keywords
        for missing_kw in ["cube", "incident", "itil", "rtp"]:
            self.assertIn(missing_kw, missing, f"Expected '{missing_kw}' to be in missing_skills")

    def test_score_consistency_and_bounds(self):
        """Verify scores are deterministic (identical runs yield identical score) and within [0, 100]."""
        run1 = evaluate_candidate_deterministically(self.sample_jd, self.sample_resume)
        run2 = evaluate_candidate_deterministically(self.sample_jd, self.sample_resume)

        self.assertEqual(run1["match_score"], run2["match_score"])
        self.assertEqual(run1["verdict"], run2["verdict"])
        self.assertTrue(0 <= run1["match_score"] <= 100)
        self.assertEqual(run1["score_type"], "Deterministic Keyword & Heuristic Coverage (Rule-Based)")
        self.assertTrue(run1["human_review_required"])

    def test_wise_experience_calculation_filters_academic_years(self):
        """Verify schooling/degree years (1999) do NOT falsely compute 27 years, and detects 20+ years."""
        num_yrs, total_str, relevant_str = compute_candidate_experience(self.sample_resume)

        # Must detect 20+ years from 'with 20 years of experience' / 2004 timeline, NOT 27
        self.assertIn("20", total_str)
        self.assertNotIn("27", total_str)
        self.assertIn("Years", total_str)

    def test_candidate_metadata_extraction(self):
        """Verify candidate name, contact, employer, and location extraction."""
        meta = extract_candidate_metadata(self.sample_resume)

        self.assertEqual(meta["name"], "Tarun Taneja")
        self.assertEqual(meta["email"], "taruntan@gmail.com")
        self.assertIn("Gurugram", meta["location"])
        self.assertIn("HCL", meta["organization"])
        self.assertIn("20", meta["total_exp"])

    def test_evidence_snippets_extraction(self):
        """Verify supporting evidence contains contextual sentence snippets."""
        snippets = find_evidence_snippets("CUCM", self.sample_resume)
        self.assertGreater(len(snippets), 0)
        self.assertTrue(any("CUCM" in s for s in snippets))

    def test_empty_and_invalid_inputs(self):
        """Verify empty or excessively brief inputs raise EmptyDocumentError."""
        with self.assertRaises(parser.EmptyDocumentError):
            evaluate_candidate_deterministically("", self.sample_resume)

        with self.assertRaises(parser.EmptyDocumentError):
            evaluate_candidate_deterministically(self.sample_jd, "")

        with self.assertRaises(parser.EmptyDocumentError):
            evaluate_candidate_deterministically("too short", "short")

    def test_zero_external_llm_calls(self):
        """Verify that evaluation succeeds even when all LLM API environment keys are absent."""
        orig_openai = os.environ.get("OPENAI_API_KEY")
        orig_groq = os.environ.get("GROQ_API_KEY")
        try:
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]
            if "GROQ_API_KEY" in os.environ:
                del os.environ["GROQ_API_KEY"]

            result = evaluate_candidate_deterministically(self.sample_jd, self.sample_resume)
            self.assertEqual(result["status"], "success")
            self.assertIsInstance(result["match_score"], int)
        finally:
            if orig_openai is not None:
                os.environ["OPENAI_API_KEY"] = orig_openai
            if orig_groq is not None:
                os.environ["GROQ_API_KEY"] = orig_groq


if __name__ == "__main__":
    unittest.main()
