"""
Automated Unit & Integration Tests for Persistent File Storage (Section 12-J)
Proves all 12 storage requirements:
1. An uploaded JD is saved in data/job_descriptions/.
2. An uploaded resume is saved in data/resumes/.
3. Original bytes and file extension are preserved.
4. Duplicate filenames do not overwrite earlier files (collision-safe).
5. Identical-content uploads handled according to deduplication policy.
6. Stored paths remain valid after restart.
7. Screening records reference correct source files.
8. A JD can be reused for multiple candidates.
9. Failed file writes do not produce false success messages.
10. Invalid extensions and oversized files are rejected.
11. Path traversal attempts cannot escape the configured data directory.
12. Existing candidate records and screening history remain intact.
"""

import os
import unittest
import tempfile
import shutil
from unittest.mock import patch

import registry
import storage


class TestPersistentFileStorage(unittest.TestCase):

    def setUp(self):
        # Create an isolated temporary test directory
        self.test_dir = tempfile.mkdtemp(prefix="fitment_test_storage_")
        self.db_path = os.path.join(self.test_dir, "fitment_test.db")
        registry.init_db(self.db_path)

        self.sample_jd_bytes = b"Cisco Network Voice L3 / Voice T2 Engineer\nMandatory: SIP, CUCM, Expressway."
        self.sample_cv_bytes = b"SHUBHANGI SINGH RATHORE\nNetwork Analyst\nExperience: 5+ years with Cisco VoIP."

    def tearDown(self):
        if os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir, ignore_errors=True)
            except Exception:
                pass

    # 1. An uploaded JD is saved in data/job_descriptions/
    def test_01_jd_saved_in_job_descriptions_dir(self):
        res = storage.save_job_description_file(
            file_bytes=self.sample_jd_bytes,
            original_filename="JD_Cisco_Voice.docx",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        self.assertEqual(res["status"], "success")
        self.assertIn("data/job_descriptions/", res["stored_relative_path"])
        self.assertTrue(os.path.exists(res["stored_absolute_path"]))

    # 2. An uploaded resume is saved in data/resumes/
    def test_02_resume_saved_in_resumes_dir(self):
        res = storage.save_resume_file(
            file_bytes=self.sample_cv_bytes,
            original_filename="Shubhangi_CV.pdf",
            candidate_name="Shubhangi Singh",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        self.assertEqual(res["status"], "success")
        self.assertIn("data/resumes/", res["stored_relative_path"])
        self.assertTrue(os.path.exists(res["stored_absolute_path"]))

    # 3. Original bytes and file extension are preserved
    def test_03_original_bytes_and_extension_preserved(self):
        res = storage.save_job_description_file(
            file_bytes=self.sample_jd_bytes,
            original_filename="Senior_Voice_JD.docx",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        self.assertTrue(res["stored_absolute_path"].endswith(".docx"))
        with open(res["stored_absolute_path"], "rb") as f:
            saved_bytes = f.read()
        self.assertEqual(saved_bytes, self.sample_jd_bytes)

    # 4. Duplicate filenames do not overwrite earlier files
    def test_04_duplicate_filenames_do_not_overwrite(self):
        res1 = storage.save_resume_file(
            file_bytes=b"Content Version 1",
            original_filename="Resume.pdf",
            candidate_name="Candidate A",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        res2 = storage.save_resume_file(
            file_bytes=b"Content Version 2 (different content)",
            original_filename="Resume.pdf",
            candidate_name="Candidate B",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        self.assertNotEqual(res1["stored_absolute_path"], res2["stored_absolute_path"])
        self.assertTrue(os.path.exists(res1["stored_absolute_path"]))
        self.assertTrue(os.path.exists(res2["stored_absolute_path"]))
        with open(res1["stored_absolute_path"], "rb") as f:
            self.assertEqual(f.read(), b"Content Version 1")
        with open(res2["stored_absolute_path"], "rb") as f:
            self.assertEqual(f.read(), b"Content Version 2 (different content)")

    # 5. Identical-content uploads handled according to deduplication policy
    def test_05_identical_content_handled_with_deduplication(self):
        res1 = storage.save_job_description_file(
            file_bytes=self.sample_jd_bytes,
            original_filename="JD_Copy1.docx",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        self.assertFalse(res1.get("reused", False))

        res2 = storage.save_job_description_file(
            file_bytes=self.sample_jd_bytes,
            original_filename="JD_Copy2.docx",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        self.assertTrue(res2.get("reused", False))
        self.assertEqual(res1["sha256"], res2["sha256"])
        self.assertEqual(res1["stored_relative_path"], res2["stored_relative_path"])

    # 6. Stored paths remain valid after restart (path resolution)
    def test_06_stored_paths_remain_valid_after_restart(self):
        res = storage.save_job_description_file(
            file_bytes=self.sample_jd_bytes,
            original_filename="Network_JD.txt",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        rel_path = res["stored_relative_path"]

        # Resolve path as if in a new process/session
        resolved = storage.resolve_stored_path(rel_path, base_dir=self.test_dir)
        self.assertTrue(os.path.exists(resolved))
        read_bytes = storage.read_stored_file_bytes(rel_path, base_dir=self.test_dir)
        self.assertEqual(read_bytes, self.sample_jd_bytes)

    # 7. Screening records reference the correct source files
    def test_07_screening_records_reference_correct_source_files(self):
        cid = registry.upsert_candidate(name="Tarun Taneja", email="tarun@test.com", db_path=self.db_path)
        jid = registry.upsert_job(job_title="Voice L3", job_description="Voice Support", db_path=self.db_path)

        jd_res = storage.save_job_description_file(
            file_bytes=self.sample_jd_bytes,
            original_filename="Voice_L3_JD.docx",
            job_id=jid,
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        cv_res = storage.save_resume_file(
            file_bytes=self.sample_cv_bytes,
            original_filename="Tarun_CV.docx",
            candidate_id=cid,
            base_dir=self.test_dir,
            db_path=self.db_path,
        )

        sid = registry.save_screening(
            candidate_id=cid,
            job_id=jid,
            deterministic_score=85,
            verdict="Strong Match",
            recommendation="Proceed to Interview",
            db_path=self.db_path,
        )

        registry.associate_screening_files(
            screening_id=sid,
            jd_file_id=jd_res["file_id"],
            resume_file_id=cv_res["file_id"],
            candidate_id=cid,
            job_id=jid,
            db_path=self.db_path,
        )

        files = registry.get_screening_files(sid, db_path=self.db_path)
        self.assertIsNotNone(files["jd_file"])
        self.assertIsNotNone(files["resume_file"])
        self.assertEqual(files["jd_file"]["original_filename"], "Voice_L3_JD.docx")
        self.assertEqual(files["resume_file"]["original_filename"], "Tarun_CV.docx")

    # 8. A JD can be reused for multiple candidates
    def test_08_jd_reusable_for_multiple_candidates(self):
        jid = registry.upsert_job(job_title="Voice L3", job_description="Voice Support", db_path=self.db_path)
        jd_res = storage.save_job_description_file(
            file_bytes=self.sample_jd_bytes,
            original_filename="Shared_JD.docx",
            job_id=jid,
            base_dir=self.test_dir,
            db_path=self.db_path,
        )

        cid1 = registry.upsert_candidate(name="Candidate 1", email="c1@test.com", db_path=self.db_path)
        cid2 = registry.upsert_candidate(name="Candidate 2", email="c2@test.com", db_path=self.db_path)

        sid1 = registry.save_screening(candidate_id=cid1, job_id=jid, deterministic_score=70, verdict="Pass", recommendation="OK", db_path=self.db_path)
        sid2 = registry.save_screening(candidate_id=cid2, job_id=jid, deterministic_score=80, verdict="Pass", recommendation="OK", db_path=self.db_path)

        registry.associate_screening_files(screening_id=sid1, jd_file_id=jd_res["file_id"], candidate_id=cid1, job_id=jid, db_path=self.db_path)
        registry.associate_screening_files(screening_id=sid2, jd_file_id=jd_res["file_id"], candidate_id=cid2, job_id=jid, db_path=self.db_path)

        # Both screenings reference the same JD
        f1 = registry.get_screening_files(sid1, db_path=self.db_path)
        f2 = registry.get_screening_files(sid2, db_path=self.db_path)
        self.assertEqual(f1["jd_file"]["stored_relative_path"], f2["jd_file"]["stored_relative_path"])

    # 9. Failed file writes do not produce false success messages
    def test_09_failed_file_writes_do_not_produce_false_success(self):
        with patch("os.replace", side_effect=IOError("Simulated disk full or permission denied")):
            res = storage.save_job_description_file(
                file_bytes=self.sample_jd_bytes,
                original_filename="Fail_JD.docx",
                base_dir=self.test_dir,
                db_path=self.db_path,
            )
            self.assertEqual(res["status"], "error")
            self.assertIn("Filesystem write failed", res["message"])

    # 10. Invalid extensions and oversized files are rejected
    def test_10_invalid_extensions_and_oversized_files_rejected(self):
        # Invalid extension (.exe)
        res_ext = storage.save_resume_file(
            file_bytes=b"binary executable",
            original_filename="Malicious.exe",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        self.assertEqual(res_ext["status"], "error")
        self.assertIn("Unsupported file extension", res_ext["message"])

        # Oversized file (> 15 MB)
        oversized_bytes = b"0" * (16 * 1024 * 1024)
        res_size = storage.save_job_description_file(
            file_bytes=oversized_bytes,
            original_filename="Giant_JD.pdf",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        self.assertEqual(res_size["status"], "error")
        self.assertIn("exceeds maximum allowed limit", res_size["message"])

    # 11. Path traversal attempts cannot escape the configured data directory
    def test_11_path_traversal_attempts_cannot_escape_data_dir(self):
        # Filename with path traversal attempts
        res = storage.save_resume_file(
            file_bytes=self.sample_cv_bytes,
            original_filename="../../../Windows/System32/evil.pdf",
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        self.assertEqual(res["status"], "success")
        # Ensure stored file is strictly inside data/resumes/
        self.assertTrue(res["stored_absolute_path"].startswith(self.test_dir))
        self.assertNotIn("..", res["stored_relative_path"])

        # Attempt resolving malicious relative path
        with self.assertRaises(PermissionError):
            storage.resolve_stored_path("../../secret.txt", base_dir=self.test_dir)

    # 12. Existing candidate records and screening history remain intact
    def test_12_existing_candidate_records_and_history_intact(self):
        cid = registry.upsert_candidate(name="Preserved Candidate", email="preserve@test.com", db_path=self.db_path)
        jid = registry.upsert_job(job_title="Preserved Role", job_description="Desc", db_path=self.db_path)
        sid = registry.save_screening(candidate_id=cid, job_id=jid, deterministic_score=92, verdict="Selected", recommendation="Hire", db_path=self.db_path)

        # Execute multiple storage operations
        storage.save_job_description_file(self.sample_jd_bytes, "JD_1.docx", base_dir=self.test_dir, db_path=self.db_path)
        storage.save_resume_file(self.sample_cv_bytes, "CV_1.pdf", base_dir=self.test_dir, db_path=self.db_path)

        # Verify candidate and screening remain unaltered
        cand = registry.get_candidate_by_id(cid, db_path=self.db_path)
        self.assertIsNotNone(cand)
        self.assertEqual(cand["name"], "Preserved Candidate")

        screenings = registry.get_candidate_screenings(cid, db_path=self.db_path)
        self.assertEqual(len(screenings), 1)
        self.assertEqual(screenings[0]["deterministic_score"], 92)


if __name__ == "__main__":
    unittest.main()
