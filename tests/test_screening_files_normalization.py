"""
Regression tests for screening files normalization (Phase 1).
Covers:
1. A list of file-record dictionaries.
2. A list of stored filename strings.
3. An empty list.
4. A missing optional filename or role.
5. A malformed record (non-dict, non-string, None).
6. File metadata loaded from an existing SQLite screening record.
"""

import os
import unittest
import tempfile
import shutil

import registry
import storage


class TestScreeningFilesNormalization(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="fitment_test_norm_")
        self.db_path = os.path.join(self.test_dir, "test_norm.db")
        registry.init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir, ignore_errors=True)
            except Exception:
                pass

    # 1. A list of file-record dictionaries
    def test_list_of_file_record_dictionaries(self):
        records = [
            {"original_filename": "Voice_JD.docx", "file_role": "job_description", "stored_relative_path": "data/job_descriptions/Voice_JD.docx"},
            {"original_filename": "Candidate_CV.pdf", "file_role": "resume", "stored_relative_path": "data/resumes/Candidate_CV.pdf"},
        ]
        norm = registry.normalize_screening_files(records)
        self.assertEqual(len(norm), 2)
        self.assertEqual(norm[0]["original_filename"], "Voice_JD.docx")
        self.assertEqual(norm[0]["file_role"], "JD")
        self.assertEqual(norm[1]["original_filename"], "Candidate_CV.pdf")
        self.assertEqual(norm[1]["file_role"], "Resume")

    # 2. A list of stored filename strings
    def test_list_of_stored_filename_strings(self):
        records = [
            "data/job_descriptions/Network_Engineer_JD_abc123.docx",
            "data/resumes/Shubhangi_CV_xyz789.pdf",
        ]
        norm = registry.normalize_screening_files(records)
        self.assertEqual(len(norm), 2)
        self.assertEqual(norm[0]["original_filename"], "Network_Engineer_JD_abc123.docx")
        self.assertEqual(norm[0]["file_role"], "JD")
        self.assertEqual(norm[1]["original_filename"], "Shubhangi_CV_xyz789.pdf")
        self.assertEqual(norm[1]["file_role"], "Resume")

    # 3. An empty list and None
    def test_empty_list_and_none(self):
        self.assertEqual(registry.normalize_screening_files([]), [])
        self.assertEqual(registry.normalize_screening_files(None), [])
        self.assertEqual(registry.normalize_screening_files({}), [])

    # 4. A missing optional filename or role
    def test_missing_optional_filename_or_role(self):
        records = [
            {"stored_relative_path": "data/resumes/Fallback_Resume.pdf"}, # missing original_filename and file_role
            {"original_filename": "Special_Note.txt"}, # missing file_role and path
            {}, # completely empty dictionary
        ]
        norm = registry.normalize_screening_files(records)
        self.assertEqual(len(norm), 3)
        self.assertEqual(norm[0]["original_filename"], "Fallback_Resume.pdf")
        self.assertEqual(norm[0]["file_role"], "Resume")
        self.assertEqual(norm[1]["original_filename"], "Special_Note.txt")
        self.assertEqual(norm[1]["file_role"], "Document")
        self.assertEqual(norm[2]["original_filename"], "Unknown Document")
        self.assertEqual(norm[2]["file_role"], "Document")

    # 5. A malformed record (non-dict, non-string, integers, etc.)
    def test_malformed_records(self):
        records = [
            {"original_filename": "Valid_JD.docx", "file_role": "jd"},
            12345, # integer
            None, # None in list
            ["nested_list"], # nested list
            {"original_filename": "Valid_Resume.pdf", "file_role": "resume"},
        ]
        norm = registry.normalize_screening_files(records)
        self.assertEqual(len(norm), 2)
        self.assertEqual(norm[0]["original_filename"], "Valid_JD.docx")
        self.assertEqual(norm[0]["file_role"], "JD")
        self.assertEqual(norm[1]["original_filename"], "Valid_Resume.pdf")
        self.assertEqual(norm[1]["file_role"], "Resume")

    # 6. File metadata loaded from an existing SQLite screening record
    def test_metadata_loaded_from_sqlite_screening_record(self):
        cid = registry.upsert_candidate(name="Prachi Gupta", email="prachi@test.com", db_path=self.db_path)
        jid = registry.upsert_job(job_title="Voice L3 Lead", job_description="Cisco Voice", db_path=self.db_path)

        jd_meta = storage.save_job_description_file(
            file_bytes=b"Job description test bytes",
            original_filename="Cisco_Voice_JD.docx",
            job_id=jid,
            base_dir=self.test_dir,
            db_path=self.db_path,
        )
        cv_meta = storage.save_resume_file(
            file_bytes=b"Candidate CV test bytes",
            original_filename="Prachi_CV.pdf",
            candidate_id=cid,
            base_dir=self.test_dir,
            db_path=self.db_path,
        )

        sid = registry.save_screening(
            candidate_id=cid,
            job_id=jid,
            deterministic_score=92,
            verdict="Direct Fit",
            recommendation="Advance to Final",
            db_path=self.db_path,
        )

        registry.associate_screening_files(
            screening_id=sid,
            jd_file_id=jd_meta["file_id"],
            resume_file_id=cv_meta["file_id"],
            candidate_id=cid,
            job_id=jid,
            db_path=self.db_path,
        )

        raw_files = registry.get_screening_files(sid, db_path=self.db_path)
        # raw_files is a dict with 'jd_file', 'resume_file', 'files'
        norm = registry.normalize_screening_files(raw_files)
        self.assertEqual(len(norm), 2)
        self.assertTrue(any(f["original_filename"] == "Cisco_Voice_JD.docx" and f["file_role"] == "JD" for f in norm))
        self.assertTrue(any(f["original_filename"] == "Prachi_CV.pdf" and f["file_role"] == "Resume" for f in norm))


if __name__ == "__main__":
    unittest.main()
