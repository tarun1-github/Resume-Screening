"""
Dedicated unit tests for registry.get_dashboard_analytics_summary()
Validates empty database behavior, populated database metric calculations,
aliasing compatibility for app.py UI consumers, null handling, and module reload resilience.
"""

import os
import unittest
import tempfile
import importlib
from datetime import datetime, timezone

import registry


class TestDashboardAnalyticsSummary(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_analytics.db")
        registry.init_db(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_module_has_attribute_and_export(self):
        """Verify get_dashboard_analytics_summary is properly bound and exported in registry."""
        self.assertTrue(hasattr(registry, "get_dashboard_analytics_summary"))
        self.assertTrue(callable(registry.get_dashboard_analytics_summary))
        self.assertIn("get_dashboard_analytics_summary", registry.__all__)

        # Verify module reloads cleanly without dropping the attribute
        reloaded = importlib.reload(registry)
        self.assertTrue(hasattr(reloaded, "get_dashboard_analytics_summary"))

    def test_empty_database_returns_safe_zero_metrics(self):
        """Empty database must return zero counts and an empty recent_candidates list without raising exceptions."""
        summary = registry.get_dashboard_analytics_summary(db_path=self.db_path)

        self.assertIsInstance(summary, dict)
        self.assertEqual(summary["total_candidates"], 0)
        self.assertEqual(summary["total_screened"], 0)
        self.assertEqual(summary["shortlisted_count"], 0)
        self.assertEqual(summary["in_review_count"], 0)
        self.assertEqual(summary["interviews_scheduled_count"], 0)
        self.assertEqual(summary["joined_count"], 0)
        self.assertEqual(summary["recent_candidates"], [])

    def test_populated_database_calculates_exact_metrics(self):
        """Populated SQLite records must yield exact aggregate counts and correctly formatted recent candidate records."""
        # 1. Insert jobs
        job_1 = registry.upsert_job(
            job_title="Senior Python Architect",
            job_description="Architecting microservices and AI pipelines with Python.",
            required_skills=["Python", "FastAPI", "Docker", "PostgreSQL"],
            db_path=self.db_path,
        )
        job_2 = registry.upsert_job(
            job_title="Cisco Collaboration Engineer",
            job_description="Deploying Cisco CUCM, CUBE, and Webex Calling.",
            required_skills=["CUCM", "CUBE", "SIP", "Webex"],
            db_path=self.db_path,
        )

        # 2. Insert candidates with diverse statuses
        candidates_data = [
            ("Alice Smith", "Shortlisted", "Senior Software Engineer"),
            ("Bob Jones", "Shortlisted", "Backend Lead"),
            ("Carol White", "Recruiter Review", "Data Engineer"),
            ("David Brown", "Interview Scheduled", "Voice Specialist"),
            ("Eve Davis", "Interview Completed", "Telecom Architect"),
            ("Frank Miller", "Joined", "Principal Architect"),
            ("Grace Hopper", "Screened", "Systems Engineer"),
            ("Heidi Green", "Rejected", "Junior Developer"),
        ]

        candidate_ids = []
        for idx, (name, status, desig) in enumerate(candidates_data):
            cid = registry.upsert_candidate(
                name=name,
                mobile=f"+1-555-01{idx:02d}",
                email=f"{name.lower().replace(' ', '.')}@example.com",
                location="Dallas, TX",
                current_designation=desig,
                current_organization="Tech Corp",
                total_experience="8 years",
                db_path=self.db_path,
            )
            registry.update_candidate_status(cid, status, notes=f"Setting to {status}", db_path=self.db_path)
            candidate_ids.append(cid)

        # 3. Insert screenings for a subset of candidates
        # Screen Alice for Job 1
        registry.save_screening(
            candidate_id=candidate_ids[0],
            job_id=job_1,
            deterministic_score=92,
            skills_score=95,
            exp_score=90,
            cert_score=85,
            matched_skills=["Python", "FastAPI"],
            missing_skills=["Docker"],
            verdict="High Fit",
            recommendation="Strong recommendation for interview",
            evidence={"details": "Matches senior backend expectations"},
            db_path=self.db_path,
        )

        # Screen David for Job 2
        registry.save_screening(
            candidate_id=candidate_ids[3],
            job_id=job_2,
            deterministic_score=84,
            skills_score=85,
            exp_score=80,
            cert_score=90,
            matched_skills=["CUCM", "SIP"],
            missing_skills=["CUBE"],
            verdict="Good Fit",
            recommendation="Advance to technical screen",
            evidence={"details": "Voice collaboration specialist"},
            db_path=self.db_path,
        )

        # Screen Frank for Job 1
        registry.save_screening(
            candidate_id=candidate_ids[5],
            job_id=job_1,
            deterministic_score=96,
            skills_score=98,
            exp_score=95,
            cert_score=90,
            matched_skills=["Python", "FastAPI", "Docker", "PostgreSQL"],
            missing_skills=[],
            verdict="High Fit",
            recommendation="Immediate offer recommendation",
            evidence={"details": "Perfect match"},
            db_path=self.db_path,
        )

        # 4. Fetch dashboard analytics summary
        summary = registry.get_dashboard_analytics_summary(db_path=self.db_path)

        # Check total candidates
        self.assertEqual(summary["total_candidates"], 8)

        # Check total screenings
        self.assertEqual(summary["total_screened"], 3)

        # Check status aggregations:
        # Shortlisted = 2 (Alice, Bob)
        self.assertEqual(summary["shortlisted_count"], 2)
        # Recruiter Review = 1 (Carol)
        self.assertEqual(summary["in_review_count"], 1)
        # Interviews Scheduled / Completed = 2 (David, Eve)
        self.assertEqual(summary["interviews_scheduled_count"], 2)
        # Selected / Offer Released / Joined = 1 (Frank)
        self.assertEqual(summary["joined_count"], 1)

        # Check recent_candidates
        recent = summary["recent_candidates"]
        self.assertIsInstance(recent, list)
        self.assertEqual(len(recent), 5)  # Capped at 5

        # Check candidate structure and alias keys consumed by app.py
        for rc in recent:
            self.assertIn("candidate_id", rc)
            self.assertIn("name", rc)
            self.assertIn("current_status", rc)
            self.assertIn("updated_at", rc)
            self.assertIn("last_activity_time", rc)
            self.assertIn("latest_score", rc)
            self.assertIn("deterministic_score", rc)
            self.assertIn("target_role", rc)
            self.assertIn("job_title", rc)
            self.assertIn("current_designation", rc)

            # Check aliasing consistency
            self.assertEqual(rc["latest_score"], rc["deterministic_score"])
            self.assertEqual(rc["last_activity_time"], rc["updated_at"])
            self.assertTrue(len(rc["target_role"]) > 0)

        # Screened candidate Frank should have score 96
        frank_rc = next((r for r in recent if r["name"] == "Frank Miller"), None)
        if frank_rc:
            self.assertEqual(frank_rc["latest_score"], 96)
            self.assertEqual(frank_rc["target_role"], "Senior Python Architect")
            self.assertEqual(frank_rc["verdict"], "High Fit")

    def test_null_and_missing_screenings_handled_gracefully(self):
        """Candidates with no screenings should have latest_score=None and role falling back to designation gracefully."""
        registry.upsert_candidate(
            name="Unscreened Candidate",
            current_designation="Staff Site Reliability Engineer",
            db_path=self.db_path,
        )

        summary = registry.get_dashboard_analytics_summary(db_path=self.db_path)
        self.assertEqual(summary["total_candidates"], 1)
        self.assertEqual(summary["total_screened"], 0)

        recent = summary["recent_candidates"]
        self.assertEqual(len(recent), 1)
        cand = recent[0]
        self.assertEqual(cand["name"], "Unscreened Candidate")
        self.assertIsNone(cand["latest_score"])
        self.assertIsNone(cand["verdict"])
        self.assertEqual(cand["target_role"], "Staff Site Reliability Engineer")


if __name__ == "__main__":
    unittest.main()
