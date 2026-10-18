"""
Regression Test Suite for JD and Resume Upload, Persistence, and Reuse
Validates the unified metadata contract, legacy compatibility, error handling,
restart persistence, and screening integration.
"""

import os
import shutil
import tempfile
import unittest

import deterministic_engine
import parser
import registry
import storage


class TestUploadPersistenceRegression(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_fitment.db")
        registry.init_db(self.db_path)

        self.sample_jd_bytes = b"Job Title: Voice Engineer L3\nRequirements: Cisco CallManager, SIP, CUBE, 5+ years experience."
        self.sample_resume_bytes = b"Candidate Name: Tarun Taneja\nEmail: tarun@test.com\nSkills: Cisco CallManager, SIP, CUBE\nExperience: 6 years at Cisco."

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # 1. JD upload and persistence
    def test_01_jd_upload_and_persistence(self):
        res = storage.save_job_description_file(
            file_bytes=self.sample_jd_bytes,
            original_filename="Network_JD.docx",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        self.assertEqual(res["status"], "success")
        self.assertIn("stored_path", res)
        self.assertIn("stored_relative_path", res)
        self.assertEqual(res["stored_path"], res["stored_relative_path"])
        self.assertEqual(res["file_role"], "jd")
        self.assertTrue(os.path.exists(res["stored_absolute_path"]))
        self.assertEqual(os.path.getsize(res["stored_absolute_path"]), len(self.sample_jd_bytes))

    # 2. Resume upload and persistence
    def test_02_resume_upload_and_persistence(self):
        res = storage.save_resume_file(
            file_bytes=self.sample_resume_bytes,
            original_filename="Tarun_Agentic_AI_1.0.docx",
            candidate_name="Tarun Taneja",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        self.assertEqual(res["status"], "success")
        self.assertIn("stored_path", res)
        self.assertEqual(res["stored_path"], res["stored_relative_path"])
        self.assertEqual(res["file_role"], "resume")
        # Ensure original .docx extension is preserved despite candidate name stem
        self.assertTrue(res["stored_path"].endswith(".docx"))
        self.assertTrue(os.path.exists(res["stored_absolute_path"]))

    # 3. Saved JD selection and reuse
    def test_03_saved_jd_selection_and_reuse(self):
        save_res = storage.save_job_description_file(
            file_bytes=self.sample_jd_bytes,
            original_filename="Voice_L3_JD.docx",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        saved_list = storage.list_saved_job_descriptions(base_dir=self.test_dir, db_path=self.db_path)
        self.assertGreaterEqual(len(saved_list), 1)
        chosen = next(j for j in saved_list if j["file_id"] == save_res["file_id"])

        # Caller accessing stored_path must succeed without KeyError
        stored_p = chosen["stored_path"]
        self.assertIsNotNone(stored_p)
        content_bytes = storage.read_stored_file_bytes(chosen, base_dir=self.test_dir)
        self.assertEqual(content_bytes, self.sample_jd_bytes)

    # 4. Saved resume selection and reuse
    def test_04_saved_resume_selection_and_reuse(self):
        save_res = storage.save_resume_file(
            file_bytes=self.sample_resume_bytes,
            original_filename="Engineer_CV.docx",
            candidate_name="Alice Smith",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        saved_list = storage.list_saved_resumes(base_dir=self.test_dir, db_path=self.db_path)
        self.assertGreaterEqual(len(saved_list), 1)
        chosen = next(r for r in saved_list if r["file_id"] == save_res["file_id"])

        stored_p = chosen["stored_path"]
        self.assertIsNotNone(stored_p)
        content_bytes = storage.read_stored_file_bytes(chosen, base_dir=self.test_dir)
        self.assertEqual(content_bytes, self.sample_resume_bytes)

    # 5. Metadata returned matches caller's expected schema
    def test_05_metadata_schema_contract(self):
        jd_meta = storage.save_job_description_file(
            file_bytes=self.sample_jd_bytes,
            original_filename="Senior_Dev.docx",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        expected_keys = {
            "file_id", "original_filename", "file_role", "stored_path",
            "stored_relative_path", "stored_absolute_path", "file_size",
            "sha256", "uploaded_at", "reused", "status", "message"
        }
        for k in expected_keys:
            self.assertIn(k, jd_meta, f"Missing key '{k}' in JD metadata")

        cv_meta = storage.save_resume_file(
            file_bytes=self.sample_resume_bytes,
            original_filename="Senior_Dev_CV.docx",
            candidate_name="Dev Candidate",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        for k in expected_keys:
            self.assertIn(k, cv_meta, f"Missing key '{k}' in Resume metadata")

    # 6. Legacy metadata without stored_path handled seamlessly
    def test_06_legacy_metadata_without_stored_path(self):
        legacy_dict = {
            "stored_relative_path": "data/job_descriptions/Legacy_JD.docx",
            "original_filename": "Legacy_JD.docx",
            "file_role": "job_description"
        }
        # resolve_stored_path must resolve dict even if stored_path key is absent
        resolved = storage.resolve_stored_path(legacy_dict, base_dir=self.test_dir)
        self.assertIn("Legacy_JD.docx", resolved)

    # 7. Missing saved file raises FileNotFoundError
    def test_07_missing_saved_file_raises_not_found(self):
        missing_dict = {
            "stored_path": "data/job_descriptions/non_existent_file.docx",
            "original_filename": "non_existent_file.docx"
        }
        with self.assertRaises(FileNotFoundError):
            storage.read_stored_file_bytes(missing_dict, base_dir=self.test_dir)

    # 8. Corrupted or unsupported document rejected during validation
    def test_08_unsupported_document_rejected(self):
        bad_meta = storage.save_job_description_file(
            file_bytes=b"malicious executable binary",
            original_filename="payload.exe",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        self.assertEqual(bad_meta["status"], "error")
        self.assertIn("Unsupported file extension", bad_meta["message"])

    # 9. Duplicate filenames do not overwrite existing files
    def test_09_duplicate_filenames_no_overwrite(self):
        res1 = storage.save_job_description_file(
            file_bytes=b"Version 1 content",
            original_filename="JD_Standard.docx",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        res2 = storage.save_job_description_file(
            file_bytes=b"Version 2 different content",
            original_filename="JD_Standard.docx",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        self.assertNotEqual(res1["file_id"], res2["file_id"])
        self.assertNotEqual(res1["stored_path"], res2["stored_path"])
        # Both files must exist independently on disk
        self.assertTrue(os.path.exists(res1["stored_absolute_path"]))
        self.assertTrue(os.path.exists(res2["stored_absolute_path"]))

    # 10. Restart persistence: DB and disk remain valid across sessions
    def test_10_restart_persistence(self):
        save_res = storage.save_job_description_file(
            file_bytes=self.sample_jd_bytes,
            original_filename="Persistent_JD.docx",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        # Simulate new session by re-initializing DB connection
        registry.init_db(self.db_path)
        loaded_list = storage.list_saved_job_descriptions(base_dir=self.test_dir, db_path=self.db_path)
        found = next((j for j in loaded_list if j["file_id"] == save_res["file_id"]), None)
        self.assertIsNotNone(found)
        self.assertEqual(found["stored_path"], save_res["stored_path"])

    # 11. Existing candidate records remain intact after file saves
    def test_11_candidate_records_remain_intact(self):
        cid = registry.upsert_candidate(
            name="Existing Candidate",
            email="existing@corp.com",
            mobile="+1-555-0199",
            initial_status="Under Review",
            db_path=self.db_path,
        )
        # Save a file
        storage.save_resume_file(
            file_bytes=self.sample_resume_bytes,
            original_filename="Existing_CV.docx",
            candidate_id=cid,
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        # Verify candidate record is unchanged
        cand = registry.get_candidate_by_id(cid, db_path=self.db_path)
        self.assertIsNotNone(cand)
        self.assertEqual(cand["name"], "Existing Candidate")
        self.assertEqual(cand["current_status"], "Under Review")

    # 12. Screening uses selected JD and resume
    def test_12_screening_uses_selected_files(self):
        cid = registry.upsert_candidate(name="Screening Candidate", email="screen@test.com", db_path=self.db_path)
        jid = registry.upsert_job(job_title="Lead Voice Architect", job_description="Cisco SIP Voice", db_path=self.db_path)

        jd_meta = storage.save_job_description_file(
            file_bytes=self.sample_jd_bytes,
            original_filename="Job_Req.docx",
            job_id=jid,
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        cv_meta = storage.save_resume_file(
            file_bytes=self.sample_resume_bytes,
            original_filename="Cand_Resume.docx",
            candidate_id=cid,
            base_dir=self.test_dir,
            db_path=self.db_path,
        )

        sc_id = registry.save_screening(
            candidate_id=cid,
            job_id=jid,
            deterministic_score=85,
            verdict="High Fit",
            recommendation="Advance to technical round",
            db_path=self.db_path,
        )
        registry.associate_screening_files(
            screening_id=sc_id,
            jd_file_id=jd_meta["file_id"],
            resume_file_id=cv_meta["file_id"],
            db_path=self.db_path,
        )

        sc_files = registry.get_screening_files(sc_id, db_path=self.db_path)
        norm_files = registry.normalize_screening_files(sc_files)
        self.assertEqual(len(norm_files), 2)
        roles = {f["file_role"] for f in norm_files}
        self.assertIn("JD", roles)
        self.assertIn("Resume", roles)

    # 13. Failed persistence does not produce false success
    def test_13_failed_persistence_does_not_produce_success(self):
        huge_bytes = b"0" * (16 * 1024 * 1024)  # 16MB exceeds 15MB limit
        res = storage.save_job_description_file(
            file_bytes=huge_bytes,
            original_filename="Oversized.pdf",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        self.assertEqual(res["status"], "error")
        self.assertNotIn("✅", res.get("message", ""))
        self.assertIn("exceeds maximum allowed limit", res["message"])

    # 14. find_candidate_by_name exact and partial match
    def test_14_find_candidate_by_name(self):
        cid = registry.upsert_candidate(name="Priya Sharma", email="priya@test.com", db_path=self.db_path)
        found_exact = registry.find_candidate_by_name("Priya Sharma", db_path=self.db_path)
        self.assertIsNotNone(found_exact)
        self.assertEqual(found_exact["candidate_id"], cid)

        found_partial = registry.find_candidate_by_name("Priya", db_path=self.db_path)
        self.assertIsNotNone(found_partial)
        self.assertEqual(found_partial["candidate_id"], cid)

        self.assertIsNone(registry.find_candidate_by_name("Unknown Person", db_path=self.db_path))
        self.assertIsNone(registry.find_candidate_by_name("", db_path=self.db_path))
        self.assertIsNone(registry.find_candidate_by_name(None, db_path=self.db_path))


if __name__ == "__main__":
    unittest.main()
