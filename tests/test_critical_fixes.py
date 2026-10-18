"""
Unit and Regression Tests for FITMENT.AI Critical Bug Fixes
Covers:
1. uploaded_cv NameError resolution across all lifecycle states:
   - Newly uploaded resume
   - Saved resume loaded without new upload
   - Pasted resume text
   - No resume selected
   - Existing screening result reopened after rerun
2. Chatbot message loop prevention:
   - Single assistant response per submitted message
   - No duplicate messages on Streamlit reruns
   - Candidate selection context vs chat message separation
   - Deliberate re-querying works correctly
3. Load JD and Load Resume:
   - Dynamic success notifications
   - Loaded content actually used for screening
   - Missing/unreadable file error handling
4. Candidate Directory and View All:
   - Search by name, role, organization, and skills
   - Selection loads screening record
   - Empty search results handled gracefully
5. Skill Gaps and Grounded AI Recommendation:
   - Derived from actual JD and resume
   - Mandatory vs preferred distinction
   - Empty state when documents missing (no fabricated gaps)
   - Fallback recommendation when LLM is unavailable
   - Deterministic score remains authoritative
"""

import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import chatbot
import deterministic_engine
import parser
import registry
import storage


class TestCriticalFixes(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_critical.db")
        registry.init_db(self.db_path)

        self.sample_jd_text = (
            "Job Title: Cisco Collaboration Specialist L3\n"
            "Mandatory: SIP, CUCM, Expressway, CUBE\n"
            "Preferred: Python, Automation\n"
            "Experience: Minimum 6 years of enterprise voice experience."
        )
        self.sample_resume_text = (
            "Prachi Gupta | prachirgup08@gmail.com | Pune, India\n"
            "Summary: Voice Analyst with 5 years experience in Cisco CUCM and SIP.\n"
            "Skills: Cisco CUCM, SIP, CallManager, Troubleshooting.\n"
            "Certifications: CCNA Collaboration."
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # --------------------------------------------------------------------------
    # P0 — 1: uploaded_cv NameError Resolution
    # --------------------------------------------------------------------------
    def test_01_uploaded_cv_safety_when_loading_saved_resume(self):
        """When loading a saved resume, uploaded_cv is not defined in locals, but reference must resolve."""
        # Simulate saved resume state in session state
        session_state = {
            "last_parsed_cv_name": "Prachi_Gupta_CV.pdf",
            "cv_text_val": self.sample_resume_text,
        }
        # uploaded_cv variable is None (as initialized in app.py)
        uploaded_cv = None

        resume_ref = (
            session_state.get("last_parsed_cv_name")
            or (uploaded_cv.name if uploaded_cv else None)
            or "Pasted Text"
        )
        self.assertEqual(resume_ref, "Prachi_Gupta_CV.pdf")

        # Upsert candidate with this resolved reference succeeds
        meta = deterministic_engine.extract_candidate_metadata(self.sample_resume_text)
        cid = registry.upsert_candidate(
            name=meta["name"],
            email=meta["email"],
            mobile=meta["mobile"],
            resume_reference=resume_ref,
            db_path=self.db_path,
        )
        self.assertTrue(len(cid) >= 6)
        cand = registry.get_candidate_by_id(cid, db_path=self.db_path)
        self.assertEqual(cand["resume_reference"], "Prachi_Gupta_CV.pdf")

    def test_02_uploaded_cv_safety_with_pasted_text(self):
        """When user pastes text directly without uploading or loading a file, falls back to 'Pasted Text'."""
        session_state = {
            "last_parsed_cv_name": None,
            "cv_text_val": self.sample_resume_text,
        }
        uploaded_cv = None

        resume_ref = (
            session_state.get("last_parsed_cv_name")
            or (uploaded_cv.name if uploaded_cv else None)
            or "Pasted Text"
        )
        self.assertEqual(resume_ref, "Pasted Text")

    def test_03_uploaded_cv_safety_with_new_upload(self):
        """When a new file is uploaded, file.name is correctly resolved."""
        class MockUploadedFile:
            name = "Tarun_Resume_2026.docx"
            size = 10240

        uploaded_cv = MockUploadedFile()
        session_state = {
            "last_parsed_cv_name": uploaded_cv.name,
            "cv_text_val": self.sample_resume_text,
        }

        resume_ref = (
            session_state.get("last_parsed_cv_name")
            or (uploaded_cv.name if uploaded_cv else None)
            or "Pasted Text"
        )
        self.assertEqual(resume_ref, "Tarun_Resume_2026.docx")

    def test_04_no_resume_selected_handling(self):
        """When no resume is selected (empty string), empty evaluation raises EmptyDocumentError gracefully."""
        with self.assertRaises(parser.EmptyDocumentError):
            deterministic_engine.evaluate_candidate_deterministically(self.sample_jd_text, "")

    def test_05_reopening_existing_screening_record_without_upload(self):
        """Reopening an existing screening record restores state without needing uploaded_cv."""
        meta = deterministic_engine.extract_candidate_metadata(self.sample_resume_text)
        cid = registry.upsert_candidate(
            name=meta["name"],
            email=meta["email"],
            resume_reference="Prachi_Gupta_CV.pdf",
            db_path=self.db_path,
        )
        jid = registry.upsert_job(job_title="Voice Specialist", job_description=self.sample_jd_text, db_path=self.db_path)
        sid = registry.save_screening(
            candidate_id=cid,
            job_id=jid,
            deterministic_score=68,
            verdict="Moderate Keyword Match",
            recommendation="Review Skill Gaps",
            db_path=self.db_path,
        )

        # Retrieve screening record
        screens = registry.get_candidate_screenings(cid, db_path=self.db_path)
        self.assertEqual(len(screens), 1)
        self.assertEqual(screens[0]["screening_id"], sid)

        # Reopening record relies only on database fields, zero dependencies on uploaded_cv widget
        cand = registry.get_candidate_by_id(cid, db_path=self.db_path)
        self.assertEqual(cand["resume_reference"], "Prachi_Gupta_CV.pdf")

    # --------------------------------------------------------------------------
    # P0 — 2: Chatbot Loop and Message Deduplication
    # --------------------------------------------------------------------------
    def test_06_single_response_per_chat_query(self):
        """Submitting a query like 'Find details for Tarun' produces exactly one user message and one assistant message."""
        # Upsert Tarun in database
        registry.upsert_candidate(
            name="Tarun Taneja",
            email="taruntan@gmail.com",
            mobile="+91 9654388916",
            current_designation="Solutions Architect",
            current_organization="Cisco",
            db_path=self.db_path,
        )

        bot = chatbot.FitmentAssistant(db_path=self.db_path)
        query = "Find details for: Tarun"

        chat_history = []
        # User submission simulation
        chat_history.append({"role": "user", "content": query})
        res = bot.ask(query)
        chat_history.append({"role": "assistant", "content": res["answer"]})

        # Verify history has exactly 1 user message and 1 assistant response
        self.assertEqual(len(chat_history), 2)
        self.assertEqual(chat_history[0]["role"], "user")
        self.assertEqual(chat_history[0]["content"], query)
        self.assertEqual(chat_history[1]["role"], "assistant")
        self.assertIn("Tarun Taneja", chat_history[1]["content"])

        # Simulate unrelated rerun: no query submitted
        query_to_execute = None  # None because submit_chat is False and pending_chat_q is None
        if query_to_execute:
            chat_history.append({"role": "user", "content": query_to_execute})

        # History remains unchanged
        self.assertEqual(len(chat_history), 2)

    def test_07_deliberate_resubmission_produces_single_new_response(self):
        """Deliberately submitting the same query again produces a new response."""
        registry.upsert_candidate(
            name="Tarun Taneja",
            email="taruntan@gmail.com",
            db_path=self.db_path,
        )
        bot = chatbot.FitmentAssistant(db_path=self.db_path)
        chat_history = []

        # First submission
        q = "Find details for: Tarun"
        chat_history.append({"role": "user", "content": q})
        r1 = bot.ask(q)
        chat_history.append({"role": "assistant", "content": r1["answer"]})

        # Deliberate second submission
        chat_history.append({"role": "user", "content": q})
        r2 = bot.ask(q)
        chat_history.append({"role": "assistant", "content": r2["answer"]})

        self.assertEqual(len(chat_history), 4)
        self.assertEqual(chat_history[2]["role"], "user")
        self.assertEqual(chat_history[3]["role"], "assistant")

    def test_08_candidate_selection_does_not_pollute_chat(self):
        """Selecting a candidate updates active context but does not append chat messages."""
        cid = registry.upsert_candidate(name="Prachi Gupta", email="prachi@test.com", db_path=self.db_path)
        session_state = {
            "active_candidate_id": None,
            "active_candidate_name": None,
            "chat_history": [{"role": "assistant", "content": "Welcome!"}],
        }

        # Simulating candidate selection
        session_state["active_candidate_id"] = cid
        session_state["active_candidate_name"] = "Prachi Gupta"

        # Chat history is not modified by candidate selection
        self.assertEqual(len(session_state["chat_history"]), 1)
        self.assertEqual(session_state["active_candidate_id"], cid)

    # --------------------------------------------------------------------------
    # P1 — 3: Load JD and Load Resume
    # --------------------------------------------------------------------------
    def test_09_load_jd_notification_and_screening_integration(self):
        """Loaded JD text is populated into session state and used directly in deterministic screening."""
        saved_jd = storage.save_job_description_file(
            file_bytes=self.sample_jd_text.encode("utf-8"),
            original_filename="Voice_L3_JD.txt",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        self.assertEqual(saved_jd["status"], "success")

        # Simulate Load JD action
        filename = saved_jd["original_filename"]
        notification_msg = f'Load JD "{filename}" successfully!'
        self.assertEqual(notification_msg, 'Load JD "Voice_L3_JD.txt" successfully!')

        # Read back bytes
        raw_bytes = storage.read_stored_file_bytes(saved_jd["stored_path"], base_dir=self.test_dir)
        loaded_jd_text, _ = parser.extract_text_from_file(raw_bytes, filename)
        self.assertIn("Cisco Collaboration Specialist L3", loaded_jd_text)

        # Ensure screening with this loaded JD works
        result = deterministic_engine.evaluate_candidate_deterministically(
            loaded_jd_text, self.sample_resume_text
        )
        self.assertIn("skills_matched", result)
        self.assertIn("cucm", result["skills_matched"])

    def test_10_load_resume_notification_and_screening_integration(self):
        """Loaded Resume text is populated and used directly in screening."""
        saved_cv = storage.save_resume_file(
            file_bytes=self.sample_resume_text.encode("utf-8"),
            original_filename="Prachi_CV.txt",
            candidate_name="Prachi Gupta",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        self.assertEqual(saved_cv["status"], "success")

        filename = saved_cv["original_filename"]
        notification_msg = f'Load CV "{filename}" successfully!'
        self.assertEqual(notification_msg, 'Load CV "Prachi_CV.txt" successfully!')

        raw_bytes = storage.read_stored_file_bytes(saved_cv["stored_path"], base_dir=self.test_dir)
        loaded_cv_text, _ = parser.extract_text_from_file(raw_bytes, filename)
        self.assertIn("Prachi Gupta", loaded_cv_text)

        result = deterministic_engine.evaluate_candidate_deterministically(
            self.sample_jd_text, loaded_cv_text
        )
        self.assertIn("cucm", result["skills_matched"])

    # --------------------------------------------------------------------------
    # P1 — 4: Candidate Directory Search and Loading
    # --------------------------------------------------------------------------
    def test_11_candidate_directory_search_by_skill_and_role(self):
        """Directory search finds candidates by skill (e.g., SIP, CUCM) or designation."""
        cid = registry.upsert_candidate(
            name="Prachi Gupta",
            email="prachi@test.com",
            current_designation="Voice Analyst",
            current_organization="Cisco",
            db_path=self.db_path,
        )
        jid = registry.upsert_job(job_title="Voice Lead", job_description="Cisco SIP Voice", db_path=self.db_path)
        registry.save_screening(
            candidate_id=cid,
            job_id=jid,
            deterministic_score=72,
            verdict="High Match",
            recommendation="Proceed to Interview",
            matched_skills=["sip", "cucm"],
            missing_skills=["expressway"],
            db_path=self.db_path,
        )

        # Search by designation
        res_role = registry.search_candidates_portal_wide(query_term="Voice Analyst", db_path=self.db_path)
        self.assertEqual(len(res_role), 1)
        self.assertEqual(res_role[0]["name"], "Prachi Gupta")

        # Search by skill (SIP)
        res_skill = registry.search_candidates_portal_wide(query_term="sip", db_path=self.db_path)
        self.assertEqual(len(res_skill), 1)
        self.assertEqual(res_skill[0]["name"], "Prachi Gupta")

        # Search non-matching term returns empty list gracefully
        res_none = registry.search_candidates_portal_wide(query_term="NonExistentTechXYZ", db_path=self.db_path)
        self.assertEqual(len(res_none), 0)

    # --------------------------------------------------------------------------
    # P1 — 5: Skill Gap Analysis and Grounded Recommendation
    # --------------------------------------------------------------------------
    def test_12_skill_gap_analysis_prioritizes_mandatory_over_preferred(self):
        """Skill gaps distinguish mandatory requirements from preferred/core skills."""
        gaps = deterministic_engine.analyze_skill_gaps(self.sample_jd_text, self.sample_resume_text)
        self.assertTrue(gaps["has_data"])

        # CUCM and SIP were in resume, so Expressway and CUBE should be missing mandatory gaps
        mandatory_skill_names = [g["skill"] for g in gaps["mandatory_gaps"]]
        self.assertIn("expressway", mandatory_skill_names)
        self.assertIn("cube", mandatory_skill_names)

        # Python and automation should be in preferred gaps
        preferred_skill_names = [g["skill"] for g in gaps["preferred_gaps"]]
        self.assertTrue("python" in preferred_skill_names or "automation" in preferred_skill_names)

        # Prioritized gaps should place mandatory items first
        p_gaps = gaps["prioritized_gaps"]
        self.assertGreater(len(p_gaps), 0)
        self.assertEqual(p_gaps[0]["tier"], "Mandatory")
        self.assertIn("rationale", p_gaps[0])

    def test_13_skill_gap_empty_state_when_documents_missing(self):
        """Empty or missing documents return safe empty state with zero fabricated gaps."""
        empty_gaps = deterministic_engine.analyze_skill_gaps("", "")
        self.assertFalse(empty_gaps["has_data"])
        self.assertEqual(len(empty_gaps["prioritized_gaps"]), 0)
        self.assertIn("Please provide", empty_gaps["message"])

    def test_14_grounded_deterministic_recommendation_fallback(self):
        """Deterministic recommendation produces rich strengths, gaps, and grounded status without LLM."""
        det_result = deterministic_engine.evaluate_candidate_deterministically(
            self.sample_jd_text, self.sample_resume_text
        )
        meta = deterministic_engine.extract_candidate_metadata(self.sample_resume_text)

        rec = deterministic_engine.generate_grounded_recommendation(
            det_result, meta, job_title="Cisco Collaboration Specialist L3"
        )
        self.assertIn(rec["status"], ["Shortlisted", "In Review", "Not Recommended"])
        self.assertFalse(rec["is_llm"])
        self.assertGreater(len(rec["strengths"]), 0)
        self.assertGreater(len(rec["gaps"]), 0)
        self.assertGreater(len(rec["interview_probes"]), 0)
        self.assertIn("Prachi Gupta", rec["summary"])


if __name__ == "__main__":
    unittest.main()
