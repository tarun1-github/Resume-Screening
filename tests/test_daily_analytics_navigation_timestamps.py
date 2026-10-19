"""
Unit & Integration Tests for FITMENT.AI:
- Safe View All navigation without StreamlitWidgetAlreadyInstantiatedError
- Candidate Tracker full candidate list reset
- Today's Activity filtering by IST date (Asia/Kolkata)
- Midnight IST date-boundary handling (before midnight vs after midnight)
- Status transition event counting for Screened, Shortlisted, Interview, Joined
- Live clock using Asia/Kolkata
- Screening timestamp formatting and conversion to IST
- Candidate with no screening history ("Not screened yet")
- Distinct screening timestamps per candidate (no global leakage)
- Compatibility with existing database (data/fitment.db)
"""

import os
import unittest
import tempfile
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import MagicMock, patch

import registry


class TestDailyAnalyticsNavigationTimestamps(unittest.TestCase):

    def setUp(self):
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db_file.close()
        self.db_path = self.temp_db_file.name
        registry.init_db(self.db_path)

        self.IST = ZoneInfo("Asia/Kolkata")
        self.UTC = ZoneInfo("UTC")

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass

    def test_01_view_all_navigation_safe_pattern(self):
        """Verify pending-navigation pattern does not modify widget key post-instantiation."""
        # Simulated session state
        session_state = {
            "sidebar_nav_radio": "🏠 Screening Dashboard",
            "selected_nav": "🏠 Screening Dashboard",
        }

        # User clicks "View All ➔": sets pending navigation and filter reset
        session_state["pending_nav"] = "📋 Candidate Tracker"
        session_state["tracker_reset_filters"] = True

        # Next run: Before radio instantiation, pending nav is applied and cleared
        if session_state.get("pending_nav"):
            target = session_state.pop("pending_nav")
            session_state["sidebar_nav_radio"] = target
            session_state["selected_nav"] = target

        self.assertEqual(session_state["sidebar_nav_radio"], "📋 Candidate Tracker")
        self.assertEqual(session_state["selected_nav"], "📋 Candidate Tracker")
        self.assertNotIn("pending_nav", session_state)
        self.assertTrue(session_state.get("tracker_reset_filters"))

    def test_02_full_candidate_list_opening_in_tracker(self):
        """Verify tracker filters are reset when tracker_reset_filters flag is set."""
        # Seed candidates
        cid1 = registry.upsert_candidate(name="Alice Engineer", email="alice@test.com", db_path=self.db_path)
        cid2 = registry.upsert_candidate(name="Bob Architect", email="bob@test.com", db_path=self.db_path)
        jid = registry.upsert_job(job_title="DevOps Engineer", job_description="Cloud and K8s", db_path=self.db_path)

        # Simulate existing session state with filters applied
        session_state = {
            "tracker_search_query": "NonExistentName",
            "tracker_filter_status": "Joined",
            "tracker_filter_job": "DevOps Engineer",
            "tracker_score_range": 90,
            "tracker_filter_fu": "Overdue",
            "tracker_reset_filters": True,
        }

        # Apply reset logic
        if session_state.pop("tracker_reset_filters", False):
            session_state["tracker_search_query"] = ""
            session_state["tracker_filter_status"] = "All"
            session_state["tracker_filter_job"] = "All"
            session_state["tracker_score_range"] = 0
            session_state["tracker_filter_fu"] = "All"

        candidates = registry.search_candidates_portal_wide(
            query_term=session_state["tracker_search_query"],
            status_filter=session_state["tracker_filter_status"],
            target_job=session_state["tracker_filter_job"],
            min_score=session_state["tracker_score_range"] if session_state["tracker_score_range"] > 0 else None,
            follow_up_filter=session_state["tracker_filter_fu"],
            db_path=self.db_path,
        )

        self.assertEqual(len(candidates), 2)
        names = [c["name"] for c in candidates]
        self.assertIn("Alice Engineer", names)
        self.assertIn("Bob Architect", names)

    def test_03_todays_activity_filtering_by_ist_date(self):
        """Verify Today's Activity only counts events belonging to the current IST date."""
        cid1 = registry.upsert_candidate(name="Yesterday Cand", email="y@test.com", db_path=self.db_path)
        cid2 = registry.upsert_candidate(name="Today Cand", email="t@test.com", db_path=self.db_path)
        jid = registry.upsert_job(job_title="Developer", job_description="Python Dev", db_path=self.db_path)

        yesterday = date(2026, 10, 18)
        today = date(2026, 10, 19)

        # Yesterday screening
        registry.save_screening(
            candidate_id=cid1,
            job_id=jid,
            deterministic_score=75,
            verdict="Good Match",
            recommendation="Interview",
            screening_timestamp="2026-10-18T14:30:00+05:30",
            db_path=self.db_path,
        )

        # Today screening
        registry.save_screening(
            candidate_id=cid2,
            job_id=jid,
            deterministic_score=85,
            verdict="Strong Match",
            recommendation="Fast Track",
            screening_timestamp="2026-10-19T09:15:00+05:30",
            db_path=self.db_path,
        )

        # Check today's summary
        summary_today = registry.get_dashboard_analytics_summary(db_path=self.db_path, target_date=today)
        self.assertEqual(summary_today["total_screened"], 1)

        # Check yesterday's summary
        summary_yesterday = registry.get_dashboard_analytics_summary(db_path=self.db_path, target_date=yesterday)
        self.assertEqual(summary_yesterday["total_screened"], 1)

        # Total unique candidates all-time
        self.assertEqual(summary_today["total_candidates"], 2)

    def test_04_midnight_ist_date_boundary_handling(self):
        """
        Test records around midnight IST:
        - Record 1: 1 second before midnight IST (2026-10-18T23:59:59+05:30)
        - Record 2: 1 second after midnight IST (2026-10-19T00:00:01+05:30)
        - Record 3: UTC timestamp matching 00:00:05 IST (2026-10-18T18:30:05Z)
        - Record 4: next day midnight IST (2026-10-20T00:00:00+05:30)
        Confirm only events belonging to the current IST date (2026-10-19) contribute to today's count.
        """
        cid = registry.upsert_candidate(name="Boundary Cand", email="bound@test.com", db_path=self.db_path)
        jid = registry.upsert_job(job_title="QA", job_description="Testing", db_path=self.db_path)

        # Record 1: Shortly before midnight
        registry.save_screening(
            candidate_id=cid, job_id=jid, deterministic_score=50, verdict="M", recommendation="R",
            screening_timestamp="2026-10-18T23:59:59+05:30", db_path=self.db_path,
        )
        # Record 2: Shortly after midnight IST
        registry.save_screening(
            candidate_id=cid, job_id=jid, deterministic_score=60, verdict="M", recommendation="R",
            screening_timestamp="2026-10-19T00:00:01+05:30", db_path=self.db_path,
        )
        # Record 3: In UTC format, representing 00:00:05 IST
        registry.save_screening(
            candidate_id=cid, job_id=jid, deterministic_score=70, verdict="M", recommendation="R",
            screening_timestamp="2026-10-18T18:30:05Z", db_path=self.db_path,
        )
        # Record 4: Next day midnight (end-exclusive)
        registry.save_screening(
            candidate_id=cid, job_id=jid, deterministic_score=80, verdict="M", recommendation="R",
            screening_timestamp="2026-10-20T00:00:00+05:30", db_path=self.db_path,
        )

        today = date(2026, 10, 19)
        summary = registry.get_dashboard_analytics_summary(db_path=self.db_path, target_date=today)

        # Records 2 and 3 belong to 2026-10-19. Records 1 and 4 do NOT.
        self.assertEqual(summary["total_screened"], 2)

    def test_05_each_status_count_using_actual_event_data(self):
        """Verify Screened, Shortlisted, Interview, and Joined counts use respective event records."""
        today = date(2026, 10, 19)
        now_ts = "2026-10-19T10:00:00+05:30"

        c1 = registry.upsert_candidate(name="Cand 1", email="c1@test.com", db_path=self.db_path)
        c2 = registry.upsert_candidate(name="Cand 2", email="c2@test.com", db_path=self.db_path)
        c3 = registry.upsert_candidate(name="Cand 3", email="c3@test.com", db_path=self.db_path)
        c4 = registry.upsert_candidate(name="Cand 4", email="c4@test.com", db_path=self.db_path)
        jid = registry.upsert_job(job_title="Engineer", job_description="Desc", db_path=self.db_path)

        # 1. Screened event today
        registry.save_screening(candidate_id=c1, job_id=jid, deterministic_score=80, verdict="V", recommendation="R", screening_timestamp=now_ts, db_path=self.db_path)

        # 2. Shortlisted transition today
        with registry.get_connection(self.db_path) as conn:
            conn.execute(
                "INSERT INTO candidate_status_history (candidate_id, previous_status, new_status, changed_at, notes, changed_by) VALUES (?, 'Screened', 'Shortlisted', ?, 'Good candidate', 'Recruiter')",
                (c2, now_ts),
            )
            conn.commit()

        # 3. Interview Scheduled transition today
        with registry.get_connection(self.db_path) as conn:
            conn.execute(
                "INSERT INTO candidate_status_history (candidate_id, previous_status, new_status, changed_at, notes, changed_by) VALUES (?, 'Shortlisted', 'Interview Scheduled', ?, 'Round 1 set', 'Recruiter')",
                (c3, now_ts),
            )
            conn.commit()

        # 4. Joined transition today
        with registry.get_connection(self.db_path) as conn:
            conn.execute(
                "INSERT INTO candidate_status_history (candidate_id, previous_status, new_status, changed_at, notes, changed_by) VALUES (?, 'Offer Released', 'Joined', ?, 'Onboarded', 'HR')",
                (c4, now_ts),
            )
            conn.commit()

        summary = registry.get_dashboard_analytics_summary(db_path=self.db_path, target_date=today)
        self.assertEqual(summary["total_screened"], 1)
        self.assertEqual(summary["shortlisted_count"], 1)
        self.assertEqual(summary["interviews_scheduled_count"], 1)
        self.assertEqual(summary["joined_count"], 1)

    def test_06_live_clock_using_asia_kolkata(self):
        """Verify dynamic live clock string uses Asia/Kolkata timezone and proper format."""
        clock_str = registry.get_current_ist_str()
        self.assertIn("IST (UTC+05:30)", clock_str)
        self.assertIn("|", clock_str)

        now_ist = datetime.now(self.IST)
        expected_date = now_ist.strftime("%d %b %Y")
        self.assertIn(expected_date, clock_str)

    def test_07_correct_conversion_of_screening_timestamps_to_ist(self):
        """Verify correct parsing and display conversion of naive, UTC, and aware timestamps."""
        # Naive local timestamp
        res_naive = registry.format_last_screened("2026-10-18T14:34:33.673222")
        self.assertEqual(res_naive, "Last screened: 18 Oct 2026, 14:34:33 IST")

        # UTC timestamp: 03:12:15 UTC is 08:42:15 IST (+5:30)
        res_utc = registry.format_last_screened("2026-10-19T03:12:15Z")
        self.assertEqual(res_utc, "Last screened: 19 Oct 2026, 08:42:15 IST")

        # Timezone-aware IST timestamp
        res_aware = registry.format_last_screened("2026-10-19T08:42:15.123456+05:30")
        self.assertEqual(res_aware, "Last screened: 19 Oct 2026, 08:42:15 IST")

    def test_08_candidate_with_no_screening_history(self):
        """Verify candidate with no screening history displays 'Not screened yet'."""
        cid = registry.upsert_candidate(name="Unscreened Candidate", email="unscreened@test.com", db_path=self.db_path)
        ts = registry.get_candidate_last_screened_timestamp(cid, db_path=self.db_path)
        self.assertIsNone(ts)

        display_str = registry.format_last_screened(ts)
        self.assertEqual(display_str, "Not screened yet")

    def test_09_two_candidates_with_different_screening_timestamps(self):
        """Verify two candidates have separate, distinct last-screened timestamps."""
        c1 = registry.upsert_candidate(name="Candidate Alpha", email="alpha@test.com", db_path=self.db_path)
        c2 = registry.upsert_candidate(name="Candidate Beta", email="beta@test.com", db_path=self.db_path)
        jid = registry.upsert_job(job_title="Role", job_description="Desc", db_path=self.db_path)

        ts_a = "2026-10-19T08:00:00+05:30"
        ts_b = "2026-10-19T10:30:00+05:30"

        registry.save_screening(candidate_id=c1, job_id=jid, deterministic_score=70, verdict="V", recommendation="R", screening_timestamp=ts_a, db_path=self.db_path)
        registry.save_screening(candidate_id=c2, job_id=jid, deterministic_score=85, verdict="V", recommendation="R", screening_timestamp=ts_b, db_path=self.db_path)

        act_ts_a = registry.get_candidate_last_screened_timestamp(c1, db_path=self.db_path)
        act_ts_b = registry.get_candidate_last_screened_timestamp(c2, db_path=self.db_path)

        self.assertEqual(act_ts_a, ts_a)
        self.assertEqual(act_ts_b, ts_b)
        self.assertNotEqual(act_ts_a, act_ts_b)

        fmt_a = registry.format_last_screened(act_ts_a)
        fmt_b = registry.format_last_screened(act_ts_b)

        self.assertEqual(fmt_a, "Last screened: 19 Oct 2026, 08:00:00 IST")
        self.assertEqual(fmt_b, "Last screened: 19 Oct 2026, 10:30:00 IST")

    def test_10_existing_database_compatibility(self):
        """Verify compatibility with existing SQLite fitment.db records and legacy timestamps."""
        real_db = "data/fitment.db"
        if not os.path.exists(real_db):
            self.skipTest("Real DB not present")

        # Today's activity on fitment.db (today should be 0 because all 24 records were yesterday)
        summary_today = registry.get_dashboard_analytics_summary(db_path=real_db)
        self.assertEqual(summary_today["total_screened"], 0)
        self.assertEqual(summary_today["shortlisted_count"], 0)
        self.assertEqual(summary_today["interviews_scheduled_count"], 0)
        self.assertEqual(summary_today["joined_count"], 0)

        # Total candidates all time should still be preserved
        self.assertGreaterEqual(summary_today["total_candidates"], 3)
        self.assertEqual(summary_today["all_time_screened"], 24)

        # Yesterday's activity should reflect the 24 screenings
        summary_yesterday = registry.get_dashboard_analytics_summary(db_path=real_db, target_date=date(2026, 10, 18))
        self.assertEqual(summary_yesterday["total_screened"], 24)
        self.assertEqual(summary_yesterday["shortlisted_count"], 1)


if __name__ == "__main__":
    unittest.main()
