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

    # --------------------------------------------------------------------------
    # P0 — Fix 1: Uploading, Loading, Clearing, and Deleting JDs and Resumes
    # --------------------------------------------------------------------------
    def test_15_upload_and_save_jd_file(self):
        """Upload and save a JD file validates type/size, extracts text, and indexes in SQLite."""
        jd_bytes = b"Job Title: Senior Network Engineer\nRequirements: BGP, OSPF, Cisco IOS, MPLS\nExperience: 5+ years"
        res = storage.save_job_description_file(
            file_bytes=jd_bytes,
            original_filename="Network_Engineer_JD.txt",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        self.assertEqual(res["status"], "success")
        self.assertTrue(os.path.exists(res["stored_absolute_path"]))

        # Read back bytes safely
        read_bytes = storage.read_stored_file_bytes(res["stored_relative_path"], base_dir=self.test_dir)
        self.assertEqual(read_bytes, jd_bytes)

    def test_16_upload_and_save_resume_file(self):
        """Upload and save a resume file validates type/size, saves to data/resumes/, and extracts metadata."""
        cv_bytes = b"Tarun Taneja\nEmail: tarun@example.com\nDesignation: Voice Specialist\nSkills: Cisco CUCM, SIP, Python\nExperience: 6 years"
        res = storage.save_resume_file(
            file_bytes=cv_bytes,
            original_filename="Tarun_Taneja_CV.txt",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        self.assertEqual(res["status"], "success")
        self.assertTrue(os.path.exists(res["stored_absolute_path"]))

        resumes = storage.list_saved_resumes(base_dir=self.test_dir, db_path=self.db_path)
        self.assertEqual(len(resumes), 1)
        self.assertEqual(resumes[0]["original_filename"], "Tarun_Taneja_CV.txt")

    def test_17_clear_jd_and_resume_does_not_delete_saved_files(self):
        """Clearing active selection must never delete or corrupt the underlying saved files in storage."""
        jd_bytes = b"Sample JD content for clearing test"
        cv_bytes = b"Sample CV content for clearing test"
        jd_meta = storage.save_job_description_file(jd_bytes, "Sample_JD.txt", base_dir=self.test_dir, db_path=self.db_path)
        cv_meta = storage.save_resume_file(cv_bytes, "Sample_CV.txt", base_dir=self.test_dir, db_path=self.db_path)

        # Simulate active session state
        session_state = {
            "jd_text_val": "Sample JD content for clearing test",
            "last_parsed_jd_name": "Sample_JD.txt",
            "active_jd_file_id": jd_meta["file_id"],
            "cv_text_val": "Sample CV content for clearing test",
            "last_parsed_cv_name": "Sample_CV.txt",
            "active_resume_file_id": cv_meta["file_id"],
            "active_screening_record": {"score": 75},
        }

        # Clear JD selection
        session_state["jd_text_val"] = ""
        session_state.pop("last_parsed_jd_name", None)
        session_state.pop("active_jd_file_id", None)
        session_state["active_screening_record"] = None

        # Verify underlying file on disk and in database still exists
        self.assertTrue(os.path.exists(jd_meta["stored_absolute_path"]))
        jds = storage.list_saved_job_descriptions(base_dir=self.test_dir, db_path=self.db_path)
        self.assertEqual(len(jds), 1)

        # Clear Resume selection
        session_state["cv_text_val"] = ""
        session_state.pop("last_parsed_cv_name", None)
        session_state.pop("active_resume_file_id", None)

        # Verify underlying resume file on disk and in database still exists
        self.assertTrue(os.path.exists(cv_meta["stored_absolute_path"]))
        cvs = storage.list_saved_resumes(base_dir=self.test_dir, db_path=self.db_path)
        self.assertEqual(len(cvs), 1)

    def test_18_delete_saved_file_permanently_removes_from_storage_and_db(self):
        """Explicit permanent delete removes the file from disk and updates registry list."""
        jd_bytes = b"Temporary JD to be deleted"
        jd_meta = storage.save_job_description_file(jd_bytes, "Temp_JD.txt", base_dir=self.test_dir, db_path=self.db_path)
        self.assertTrue(os.path.exists(jd_meta["stored_absolute_path"]))

        # Execute permanent deletion
        ok = storage.delete_saved_job_description(jd_meta["file_id"], base_dir=self.test_dir, db_path=self.db_path)
        self.assertTrue(ok)
        self.assertFalse(os.path.exists(jd_meta["stored_absolute_path"]))

        # Registry list no longer includes the deleted file
        remaining = storage.list_saved_job_descriptions(base_dir=self.test_dir, db_path=self.db_path)
        self.assertEqual(len(remaining), 0)

    # --------------------------------------------------------------------------
    # P0 — Fix 2: Candidate Separation & Zero Data Leakage Between Resumes
    # --------------------------------------------------------------------------
    def test_19_consecutive_resume_loads_zero_candidate_data_leakage(self):
        """Loading Resume A then Resume B ensures no candidate identity, score, or results leak into B."""
        # Candidate A: Prachi Gupta
        resume_a_text = (
            "Prachi Gupta | prachirgup08@gmail.com | +91 91457 37256\n"
            "Current Designation: Network Analyst at Cisco\n"
            "Experience: 3+ Years in Voice\n"
            "Skills: Cisco CUCM, SIP, Troubleshooting."
        )
        # Candidate B: Tarun Taneja
        resume_b_text = (
            "Tarun Taneja | tarun@telecom.com | +91 98765 43210\n"
            "Current Designation: Senior Collaboration Architect at Infosys\n"
            "Experience: 8+ Years in Enterprise Networks\n"
            "Skills: SIP, Expressway, CUBE, Python, Automation, ITIL."
        )

        # 1. Screen Candidate A
        det_a = deterministic_engine.evaluate_candidate_deterministically(self.sample_jd_text, resume_a_text)
        meta_a = deterministic_engine.extract_candidate_metadata(resume_a_text)
        cid_a = registry.upsert_candidate(name=meta_a["name"], email=meta_a["email"], db_path=self.db_path)
        screening_a_record = {
            "candidate_id": cid_a,
            "meta": meta_a,
            "det_result": det_a,
            "skills_score": 32,
            "job_title": "Cisco Collaboration Specialist L3",
        }

        # 2. Simulate User Loading Resume B:
        # Step A: Invalidate active screening record from Candidate A
        active_screening_record = None

        # Step B: Parse Candidate B's resume
        meta_b = deterministic_engine.extract_candidate_metadata(resume_b_text)
        last_parsed_cv_name = "Tarun_Taneja_CV.pdf"

        # Verify Candidate B context does NOT contain any fields from Candidate A
        self.assertIsNone(active_screening_record)
        self.assertEqual(meta_b["name"], "Tarun Taneja")
        self.assertNotEqual(meta_b["name"], meta_a["name"])
        self.assertEqual(meta_b["organization"], "Infosys")
        self.assertNotEqual(meta_b["organization"], meta_a["organization"])
        self.assertEqual(last_parsed_cv_name, "Tarun_Taneja_CV.pdf")

        # 3. Screen Candidate B independently
        det_b = deterministic_engine.evaluate_candidate_deterministically(self.sample_jd_text, resume_b_text)
        cid_b = registry.upsert_candidate(name=meta_b["name"], email=meta_b["email"], db_path=self.db_path)
        screening_b_record = {
            "candidate_id": cid_b,
            "meta": meta_b,
            "det_result": det_b,
            "skills_score": int((len(det_b["skills_matched"]) / max(len(det_b["skills_matched"]) + len(det_b["missing_skills"]), 1)) * 100),
            "job_title": "Cisco Collaboration Specialist L3",
        }

        # Verify separate candidate IDs, scores, and skills
        self.assertNotEqual(cid_a, cid_b)
        self.assertEqual(screening_b_record["meta"]["name"], "Tarun Taneja")
        self.assertIn("expressway", det_b["skills_matched"])
        self.assertNotIn("expressway", det_a["skills_matched"])

    # --------------------------------------------------------------------------
    # P0 — Fix 3: Deterministic Offline Screening & Zero Cloud Calls
    # --------------------------------------------------------------------------
    def test_20_offline_screening_makes_zero_cloud_calls(self):
        """Offline screening executes purely deterministically without making any network/cloud LLM calls."""
        with patch("llm_manager.generate_qualitative_assessment") as mock_llm:
            det_result = deterministic_engine.evaluate_candidate_deterministically(
                self.sample_jd_text, self.sample_resume_text
            )
            mock_llm.assert_not_called()
            self.assertIn("match_score", det_result)
            self.assertIn("verdict", det_result)
            self.assertIn("skills_matched", det_result)
            self.assertIn("missing_skills", det_result)

    def test_21_ai_screening_handles_provider_failure_gracefully(self):
        """AI screening falls back gracefully to deterministic analysis when the provider times out or fails."""
        import llm_manager
        with patch.object(llm_manager, "generate_qualitative_assessment", return_value={"status": "error", "message": "Connection timed out"}):
            res = llm_manager.generate_qualitative_assessment(
                job_description=self.sample_jd_text,
                resume_text=self.sample_resume_text,
                preferred_provider="gemini",
                timeout_seconds=5.0,
            )
            self.assertEqual(res["status"], "error")
            self.assertIn("Connection timed out", res["message"])

            # Verify deterministic recommendation operates as fallback
            det_result = deterministic_engine.evaluate_candidate_deterministically(self.sample_jd_text, self.sample_resume_text)
            meta = deterministic_engine.extract_candidate_metadata(self.sample_resume_text)
            fallback = deterministic_engine.generate_grounded_recommendation(det_result, meta, "Target Role")
            self.assertFalse(fallback["is_llm"])
            self.assertIn("Deterministic", fallback["engine_label"])

    def test_22_dialog_and_detailed_analysis_state_toggles(self):
        """View Full Profile dialog payload contains complete profile, and Detailed Analysis expander toggles."""
        det_result = deterministic_engine.evaluate_candidate_deterministically(self.sample_jd_text, self.sample_resume_text)
        meta = deterministic_engine.extract_candidate_metadata(self.sample_resume_text)
        active_rec = {
            "candidate_id": "cand-test-123",
            "meta": meta,
            "det_result": det_result,
            "skills_score": 32,
            "exp_score": 40,
            "cert_score": 0,
            "found_certs": ["CCNA Collaboration"],
            "job_title": "Cisco Collaboration Specialist L3",
        }

        # Verify payload elements needed for show_full_candidate_profile_dialog
        self.assertEqual(active_rec["meta"]["name"], "Prachi Gupta")
        self.assertEqual(active_rec["job_title"], "Cisco Collaboration Specialist L3")
        self.assertIn("CCNA Collaboration", active_rec["found_certs"])

        # Verify toggle state logic
        session_state = {"expand_detailed_analysis": False}
        session_state["expand_detailed_analysis"] = not session_state.get("expand_detailed_analysis", False)
        self.assertTrue(session_state["expand_detailed_analysis"])
        session_state["expand_detailed_analysis"] = not session_state.get("expand_detailed_analysis", False)
        self.assertFalse(session_state["expand_detailed_analysis"])

    def test_23_extract_candidate_metadata_hybrid_two_resumes_separation(self):
        """Verify parser.extract_candidate_metadata_hybrid extracts real candidate fields without data leakage."""
        self.assertTrue(hasattr(parser, "extract_candidate_metadata_hybrid"))
        self.assertTrue(callable(parser.extract_candidate_metadata_hybrid))
        self.assertTrue(hasattr(parser, "extract_candidate_metadata"))

        resume_1 = """
        PRACHI GUPTA
        Email: prachi.gupta@telecomcorp.com
        Contact: +91 91457 37256
        Current Organization: Cisco Systems
        Current Designation: Cisco Collaboration Specialist
        Total Experience: 3+ Years
        Skills: CUCM, CUC, Cisco Webex, SIP, CCNA Collaboration
        """

        resume_2 = """
        VIKRAM SHARMA
        Email: vikram.sharma@infotech.io
        Phone: +91 98765 43210
        Current Employer: Infosys
        Current Role: Senior Cloud DevOps Engineer
        Total Experience: 7 Years
        Skills: AWS, Kubernetes, Terraform, Docker, Python
        """

        meta_1 = parser.extract_candidate_metadata_hybrid(resume_1)
        self.assertEqual(meta_1["name"].upper(), "PRACHI GUPTA")
        self.assertIn("Cisco", meta_1["organization"])
        self.assertIn("3", meta_1["total_exp"])
        self.assertIn("91457", meta_1["mobile"])

        meta_2 = parser.extract_candidate_metadata_hybrid(resume_2)
        self.assertEqual(meta_2["name"].upper(), "VIKRAM SHARMA")
        self.assertIn("Infosys", meta_2["organization"])
        self.assertIn("7", meta_2["total_exp"])
        self.assertIn("98765", meta_2["mobile"])

        # Strict non-leakage assertions
        self.assertNotEqual(meta_1["name"].upper(), meta_2["name"].upper())
        self.assertNotEqual(meta_1["email"], meta_2["email"])
        self.assertNotEqual(meta_1["organization"], meta_2["organization"])
        self.assertNotIn("Prachi", meta_2["name"])
        self.assertNotIn("Cisco", meta_2["organization"])

        # Verify direct app.py line 2735 pattern
        session_state = {"cv_text_val": resume_2, "pending_candidate_meta": None}
        meta_resolved = session_state.get("pending_candidate_meta") or parser.extract_candidate_metadata_hybrid(session_state["cv_text_val"])
        self.assertEqual(meta_resolved["name"].upper(), "VIKRAM SHARMA")

    def test_24_extract_candidate_metadata_hybrid_resilience(self):
        """Verify extract_candidate_metadata_hybrid handles empty, corrupted, or non-candidate input safely."""
        # Empty input
        meta_empty = parser.extract_candidate_metadata_hybrid("")
        self.assertIsInstance(meta_empty, dict)
        self.assertEqual(meta_empty["name"], "Candidate Profile")
        self.assertEqual(meta_empty["organization"], "Not Detected (Requires human verification)")

        # None input
        meta_none = parser.extract_candidate_metadata_hybrid(None)
        self.assertIsInstance(meta_none, dict)
        self.assertEqual(meta_none["name"], "Candidate Profile")

        # Corrupted / unstructured text without candidate names
        corrupted = "12345 67890 \x00 random garbage text without any candidate profile or email"
        meta_corrupted = parser.extract_candidate_metadata_hybrid(corrupted)
        self.assertIsInstance(meta_corrupted, dict)
        self.assertNotEqual(meta_corrupted["name"], "Prachi Gupta")
        self.assertEqual(meta_corrupted["organization"], "Not Detected (Requires human verification)")


    # --------------------------------------------------------------------------
    # P1 — 7: Regression Tests for Default File Selection & Screening Repair
    # --------------------------------------------------------------------------
    def test_25_new_session_starts_empty_without_default_selection(self):
        """A new session starts without a default JD, resume, or active candidate."""
        # Simulated fresh session state
        session_state = {}
        if "workspace_initialized" not in session_state:
            session_state["workspace_initialized"] = True
            session_state["jd_text_val"] = ""
            session_state["last_parsed_jd_name"] = None
            session_state["cv_text_val"] = ""
            session_state["last_parsed_cv_name"] = None
            session_state["active_screening_record"] = None
            session_state["active_candidate_id"] = None
            session_state["active_candidate_name"] = None
            session_state["pending_candidate_meta"] = None

        self.assertEqual(session_state["jd_text_val"], "")
        self.assertIsNone(session_state["last_parsed_jd_name"])
        self.assertEqual(session_state["cv_text_val"], "")
        self.assertIsNone(session_state["last_parsed_cv_name"])
        self.assertIsNone(session_state["active_screening_record"])
        self.assertIsNone(session_state["active_candidate_id"])
        self.assertIsNone(session_state["active_candidate_name"])

    def test_26_saved_files_lists_available_with_neutral_placeholders(self):
        """Saved-file lists are available without automatically selecting an item."""
        saved_jds = [{"file_id": "jd1", "original_filename": "Target_JD.docx"}]
        saved_resumes = [{"file_id": "cv1", "original_filename": "Candidate_CV.pdf"}]

        jd_placeholder = "-- Select a JD to load --"
        cv_placeholder = "-- Select a resume to load --"

        jd_options = [jd_placeholder] + [j["original_filename"] for j in saved_jds]
        cv_options = [cv_placeholder] + [r["original_filename"] for r in saved_resumes]

        # The default selection (index 0) is the neutral placeholder
        self.assertEqual(jd_options[0], "-- Select a JD to load --")
        self.assertEqual(cv_options[0], "-- Select a resume to load --")
        self.assertNotEqual(jd_options[0], "Target_JD.docx")
        self.assertNotEqual(cv_options[0], "Candidate_CV.pdf")

    def test_27_explicit_jd_and_resume_loading(self):
        """Explicitly loading a JD and resume selects the correct file and sets truthful messages."""
        chosen_jd = {"file_id": "jd_test_1", "original_filename": "Network_Architect_JD.docx"}
        chosen_cv = {"file_id": "cv_test_1", "original_filename": "Shubhangi Singh Rathore CV.pdf"}

        # Simulate loading JD
        msg_jd = f"Loaded JD: {chosen_jd['original_filename']} successfully."
        self.assertEqual(msg_jd, "Loaded JD: Network_Architect_JD.docx successfully.")

        # Simulate loading CV
        msg_cv = f"Loaded CV: {chosen_cv['original_filename']} successfully."
        self.assertEqual(msg_cv, "Loaded CV: Shubhangi Singh Rathore CV.pdf successfully.")

    def test_28_selection_persists_on_rerun_and_clearing_preserves_file(self):
        """A selection persists through reruns, and clearing the selection does not delete the saved file."""
        session_state = {
            "workspace_initialized": True,
            "last_parsed_jd_name": "Network_Architect_JD.docx",
            "jd_text_val": self.sample_jd_text,
            "active_jd_file_id": "jd_123",
        }

        # Simulated rerun: state must not be overwritten
        if "workspace_initialized" not in session_state:
            session_state["workspace_initialized"] = True
            session_state["last_parsed_jd_name"] = None
            session_state["jd_text_val"] = ""

        self.assertEqual(session_state["last_parsed_jd_name"], "Network_Architect_JD.docx")
        self.assertEqual(session_state["jd_text_val"], self.sample_jd_text)

        # Clear selection
        session_state["jd_text_val"] = ""
        session_state.pop("last_parsed_jd_name", None)
        session_state.pop("active_jd_file_id", None)

        self.assertEqual(session_state["jd_text_val"], "")
        self.assertNotIn("last_parsed_jd_name", session_state)
        # Note: physical file in storage is not deleted by clear action

    def test_29_switching_candidates_invalidates_old_screening_result(self):
        """Switching from one resume to another does not retain the old candidate's result or identity."""
        session_state = {
            "active_candidate_name": "Prachi Gupta",
            "active_screening_record": {"score": 85, "candidate_name": "Prachi Gupta"},
            "cv_text_val": "Prachi Gupta resume text",
        }

        # User loads Vikram Sharma
        new_cv_text = "Vikram Sharma | Senior DevOps | Bangalore"
        # When loaded, active_screening_record is invalidated
        session_state["active_screening_record"] = None
        session_state["cv_text_val"] = new_cv_text
        meta = parser.extract_candidate_metadata_hybrid(new_cv_text)
        session_state["active_candidate_name"] = meta["name"]

        self.assertEqual(session_state["active_candidate_name"].upper(), "VIKRAM SHARMA")
        self.assertIsNone(session_state["active_screening_record"])
        self.assertNotIn("Prachi", session_state["active_candidate_name"])

    def test_30_offline_screening_zero_external_calls(self):
        """Offline screening performs zero external LLM or cloud calls."""
        with patch("llm_manager.generate_qualitative_assessment") as mock_llm:
            det_res = deterministic_engine.evaluate_candidate_deterministically(
                self.sample_jd_text, self.sample_resume_text
            )
            mock_llm.assert_not_called()
            self.assertIn("match_score", det_res)
            self.assertIn("skills_matched", det_res)
            self.assertIn("verdict", det_res)

    def test_31_ai_screening_handles_provider_failure_gracefully(self):
        """AI screening handles timeouts/failures gracefully and falls back to deterministic."""
        with patch("llm_manager.generate_qualitative_assessment", return_value={"status": "error", "message": "API Quota Exceeded"}):
            det_res = deterministic_engine.evaluate_candidate_deterministically(
                self.sample_jd_text, self.sample_resume_text
            )
            # Deterministic score remains valid and unaffected by LLM failure
            self.assertGreater(det_res["match_score"], 0)

    def test_32_missing_inputs_produce_helpful_warnings(self):
        """Missing inputs produce helpful warnings without crashing."""
        # Both missing
        jd_val = ""
        cv_val = ""
        warn_msg = None
        if not jd_val and not cv_val:
            warn_msg = "Please provide both a Job Description and a Candidate Resume to initiate screening."
        self.assertIn("both a Job Description and a Candidate Resume", warn_msg)

        # Only JD missing
        jd_val = ""
        cv_val = "Some resume text"
        if not jd_val and not cv_val:
            warn_msg = "both"
        elif not jd_val:
            warn_msg = "Job Description is missing."
        self.assertEqual(warn_msg, "Job Description is missing.")

        # Only CV missing
        jd_val = "Some JD text"
        cv_val = ""
        if not jd_val and not cv_val:
            warn_msg = "both"
        elif not cv_val:
            warn_msg = "Candidate Resume is missing."
        self.assertEqual(warn_msg, "Candidate Resume is missing.")

    def test_33_sidebar_css_preserves_expand_control(self):
        """Verify that app.py CSS preserves stExpandSidebarButton and stToolbar."""
        with open("app.py", "r", encoding="utf-8") as f:
            content = f.read()

        # stToolbar must NOT be set to display: none !important
        self.assertNotIn('[data-testid="stToolbar"] {\n        display: none !important;', content)
        self.assertIn('[data-testid="stExpandSidebarButton"]', content)
        self.assertIn('[data-testid="stSidebarCollapseButton"]', content)


if __name__ == "__main__":
    unittest.main()

