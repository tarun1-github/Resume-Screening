"""
Unit Tests for FITMENT.AI Deterministic Screening Engine
Tests rule-based scoring, keyword matching, seniority analysis, zero-LLM boundaries,
and Stage 2 reliability enhancements (no score floors, cert isolation, factual evidence).
"""

import os
import unittest

import parser
from deterministic_engine import (
    compute_candidate_experience,
    detect_certifications,
    detect_education,
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

    # -------------------------------------------------------------
    # Preserved Stage 1 Tests
    # -------------------------------------------------------------

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

    # -------------------------------------------------------------
    # Stage 2 Reliability & Regression Tests
    # -------------------------------------------------------------

    def test_completely_irrelevant_resume_scores_zero_or_near_zero(self):
        """Verify completely irrelevant resume receives near-zero score, empty skills, and no false certs."""
        irrelevant_resume = (
            "Pierre Dubois | pierre@boulangerie.fr | Paris. "
            "Executive Pastry Chef specializing in artisan sourdough, viennoiserie, and French croissants. "
            "Managed kitchen staff of 5 bakers and oversaw daily deck oven temperature calibration, "
            "dough proofing schedules, and flour supplier negotiations across Paris bakeries."
        )
        res = evaluate_candidate_deterministically(self.sample_jd, irrelevant_resume)

        # Should match zero technical skills
        self.assertEqual(res["skills_matched"], [])
        self.assertEqual(res["certifications_detected"], [])
        # Match score must be near-zero (no artificial 35% or 50% floor)
        self.assertLessEqual(res["match_score"], 5)
        self.assertTrue(res["human_review_required"])
        self.assertIn("Low", res["verdict"])
        # Organization must not invent 'Tier-1 Enterprise'
        self.assertEqual(res["metadata"]["organization"], "Not Detected (Requires human verification)")

    def test_skills_mentioned_without_certifications_claimed(self):
        """Verify Python, AWS, Kubernetes, and Linux are recognized as skills, not false certifications."""
        cloud_jd = (
            "Cloud DevOps Platform Engineer. "
            "Requirements: 5+ years experience hands-on with Python, Linux, AWS, Kubernetes, and Docker containers."
        )
        skills_resume = (
            "Siddharth Rao | sid@cloudops.net | Bengaluru, Karnataka. "
            "Senior Infrastructure Developer with 5 years experience designing microservices. "
            "Hands-on expertise deploying Python backend services onto Kubernetes clusters on AWS EC2 Linux nodes. "
            "No formal vendor certifications held at this time."
        )
        res = evaluate_candidate_deterministically(cloud_jd, skills_resume)

        # Python and Kubernetes should be recognized as technical skills
        self.assertIn("python", res["skills_matched"])
        self.assertIn("kubernetes", res["skills_matched"])

        # But certifications_detected must remain empty because none were claimed
        self.assertEqual(res["certifications_detected"], [])

    def test_missing_or_unverified_education(self):
        """Verify missing education awards 0 education credit, avoiding artificial 80-point inflation."""
        backend_jd = "Senior Python Developer with PostgreSQL, Redis, FastAPI, and Docker."
        resume_with_edu = (
            "Ananya Sen | ananya@dev.io | Pune, Maharashtra. "
            "Python developer with 5 years experience in FastAPI, PostgreSQL, Redis, and Docker. "
            "Education: Bachelor of Technology (B.Tech) in Computer Science from Pune University."
        )
        resume_no_edu = (
            "Ananya Sen | ananya@dev.io | Pune, Maharashtra. "
            "Python developer with 5 years experience in FastAPI, PostgreSQL, Redis, and Docker. "
            "Extensive experience in distributed systems and performance optimization."
        )

        res_with = evaluate_candidate_deterministically(backend_jd, resume_with_edu)
        res_no = evaluate_candidate_deterministically(backend_jd, resume_no_edu)

        # The candidate with detected education should score higher than candidate without education
        self.assertGreater(res_with["match_score"], res_no["match_score"])

        # Test pure education weight: missing education must score 0
        edu_only = evaluate_candidate_deterministically(
            backend_jd, resume_no_edu, weights={"skills": 0.0, "exp": 0.0, "edu": 100.0, "extras": 0.0}
        )
        self.assertEqual(edu_only["match_score"], 0)

    def test_genuine_matching_technical_skills_with_evidence(self):
        """Verify genuine technical skills are matched and generic words are cleanly filtered out."""
        res = evaluate_candidate_deterministically(self.sample_jd, self.sample_resume)

        matched = res["skills_matched"]

        # Genuine technical skills must match
        for skill in ["cisco", "cucm", "expressway", "python", "sip"]:
            self.assertIn(skill, matched)

        # Generic non-technical words must NOT be treated as technical skills
        for generic in ["senior", "engineer", "systems", "years", "requirements", "handling"]:
            self.assertNotIn(generic, matched)

        # Supporting evidence must provide non-empty citations for top matched skills
        self.assertIn("cucm", res["supporting_evidence"])
        self.assertGreater(len(res["supporting_evidence"]["cucm"]), 0)

    def test_no_artificial_minimum_score_floors(self):
        """Verify scores do not receive artificial minimum baseline floors (e.g. 35, 45, or 65)."""
        senior_jd = (
            "Principal Distributed Systems Architect. "
            "Requirements: 15+ years experience leading enterprise Golang, Rust, Cassandra, and Kafka architectures."
        )
        junior_resume = (
            "Amit Kumar | amit@startup.in | Delhi. "
            "Junior programmer with 1 year experience writing basic scripts. No database or distributed experience."
        )
        res = evaluate_candidate_deterministically(senior_jd, junior_resume)

        # Score must be low and NOT clamped to 35
        self.assertLess(res["match_score"], 25)

        # Zero weights handled cleanly
        zero_res = evaluate_candidate_deterministically(
            senior_jd, junior_resume, weights={"skills": 0.0, "exp": 0.0, "edu": 0.0, "extras": 0.0}
        )
        self.assertEqual(zero_res["match_score"], 0)

    def test_supporting_evidence_corresponds_to_actual_resume_text(self):
        """Verify supporting evidence snippets are exact substrings of the actual resume text."""
        res = evaluate_candidate_deterministically(self.sample_jd, self.sample_resume)

        evidence_dict = res["supporting_evidence"]
        self.assertGreater(len(evidence_dict), 0)

        for skill, snippets in evidence_dict.items():
            self.assertIsInstance(snippets, list)
            for snippet in snippets:
                # Every snippet MUST be an exact substring of the candidate resume
                self.assertIn(
                    snippet,
                    self.sample_resume,
                    f"Evidence snippet for '{skill}' was not found in the original resume text: {snippet}"
                )


if __name__ == "__main__":
    unittest.main()
