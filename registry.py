"""
FITMENT.AI - Candidate Fitment Registry
Persistent SQLite-backed storage for candidates, jobs, screenings, status tracking, and follow-ups.
Thread-safe, parameterized queries with zero arbitrary SQL execution.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple, Generator

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "fitment.db")

CANDIDATE_STATUSES = [
    "New",
    "Screened",
    "Shortlisted",
    "Recruiter Review",
    "Interview Scheduled",
    "Interview Completed",
    "On Hold",
    "Rejected",
    "Selected",
    "Offer Released",
    "Joined",
]


def _get_db_path(db_path: Optional[str] = None) -> str:
    if db_path:
        return db_path
    env_url = os.getenv("DATABASE_URL", "")
    if env_url.startswith("sqlite:///"):
        raw_path = env_url.replace("sqlite:///", "")
        if not os.path.isabs(raw_path):
            raw_path = os.path.join(os.path.dirname(__file__), raw_path)
        return raw_path
    return DEFAULT_DB_PATH


@contextmanager
def get_connection(db_path: Optional[str] = None) -> Generator[sqlite3.Connection, None, None]:
    """
    Thread-safe SQLite connection context manager.
    Automatically commits transactions and guarantees connection closure on exit.
    """
    path = _get_db_path(db_path)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize database tables, constraints, and indices."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. Candidates table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS candidates (
                candidate_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                mobile TEXT DEFAULT 'Not available in CV',
                email TEXT DEFAULT 'Not Specified',
                location TEXT DEFAULT 'Not Specified',
                current_organization TEXT DEFAULT 'Not Detected',
                current_designation TEXT DEFAULT 'Not Detected',
                previous_organizations TEXT DEFAULT '[]',
                education TEXT DEFAULT 'Not Specified',
                certifications TEXT DEFAULT '[]',
                total_experience TEXT DEFAULT 'Not Detected',
                relevant_experience TEXT DEFAULT 'Not Detected',
                resume_reference TEXT DEFAULT '',
                current_status TEXT DEFAULT 'Screened',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )

        # 2. Jobs table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                job_title TEXT NOT NULL,
                job_description TEXT NOT NULL,
                required_skills TEXT DEFAULT '[]',
                preferred_skills TEXT DEFAULT '[]',
                min_experience REAL DEFAULT 0,
                created_at TEXT NOT NULL
            );
            """
        )

        # 3. Screenings table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS screenings (
                screening_id TEXT PRIMARY KEY,
                candidate_id TEXT NOT NULL,
                job_id TEXT NOT NULL,
                screening_timestamp TEXT NOT NULL,
                deterministic_score INTEGER NOT NULL,
                skills_score INTEGER DEFAULT 0,
                exp_score INTEGER DEFAULT 0,
                cert_score INTEGER DEFAULT 0,
                matched_skills TEXT DEFAULT '[]',
                missing_skills TEXT DEFAULT '[]',
                verdict TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                evidence TEXT DEFAULT '{}',
                interview_questions TEXT DEFAULT '[]',
                llm_analysis TEXT DEFAULT '',
                llm_provider TEXT DEFAULT 'Offline / Deterministic',
                llm_model TEXT DEFAULT 'None',
                engine_version TEXT DEFAULT '2.0.0',
                FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE CASCADE,
                FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
            );
            """
        )

        # 4. Candidate status history
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS candidate_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id TEXT NOT NULL,
                screening_id TEXT,
                previous_status TEXT,
                new_status TEXT NOT NULL,
                changed_at TEXT NOT NULL,
                notes TEXT DEFAULT '',
                changed_by TEXT DEFAULT 'Recruiter',
                FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE CASCADE
            );
            """
        )

        # 5. Follow-ups
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS follow_ups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id TEXT NOT NULL,
                screening_id TEXT,
                follow_up_date TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE CASCADE
            );
            """
        )

        # 6. Persistent Stored Files Registry
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS stored_files (
                file_id TEXT PRIMARY KEY,
                file_type TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                stored_relative_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                sha256_hash TEXT NOT NULL,
                upload_timestamp TEXT NOT NULL,
                candidate_id TEXT,
                job_id TEXT,
                screening_id TEXT,
                FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id) ON DELETE SET NULL,
                FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE SET NULL
            );
            """
        )

        # 7. Screening Source Files Junction Table (supports multi-candidate JD reuse)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS screening_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                screening_id TEXT NOT NULL,
                file_id TEXT NOT NULL,
                file_role TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (screening_id) REFERENCES screenings(screening_id) ON DELETE CASCADE,
                FOREIGN KEY (file_id) REFERENCES stored_files(file_id) ON DELETE CASCADE
            );
            """
        )

        # Indices for rapid querying
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_name ON candidates(name);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_mobile ON candidates(mobile);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(current_status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_org ON candidates(current_organization);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_desig ON candidates(current_designation);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(job_title);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_screenings_candidate ON screenings(candidate_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_screenings_job ON screenings(job_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_screenings_score ON screenings(deterministic_score);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_screenings_timestamp ON screenings(screening_timestamp);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_follow_ups_date ON follow_ups(follow_up_date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stored_files_hash ON stored_files(sha256_hash);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stored_files_type ON stored_files(file_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stored_files_cand ON stored_files(candidate_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_screening_files_sid ON screening_files(screening_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_screening_files_fid ON screening_files(file_id);")


        conn.commit()



def normalize_phone(phone: str) -> str:
    """Strip all non-digits from phone number for duplicate checking."""
    if not phone or "not available" in phone.lower():
        return ""
    digits = re.sub(r"\D", "", phone)
    if len(digits) >= 10:
        return digits[-10:]
    return digits


def normalize_email(email: str) -> str:
    """Normalize email for deduplication."""
    if not email or "not specified" in email.lower() or "confidential" in email.lower():
        return ""
    return email.strip().lower()


def find_existing_candidate(
    email: str = "",
    mobile: str = "",
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Duplicate detection using normalized email or phone.
    Does NOT merge solely by candidate name to protect candidate identity integrity.
    """
    clean_e = normalize_email(email)
    clean_p = normalize_phone(mobile)

    if not clean_e and not clean_p:
        return None

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        if clean_e:
            cursor.execute("SELECT * FROM candidates WHERE LOWER(email) = ?", (clean_e,))
            row = cursor.fetchone()
            if row:
                return dict(row)

        if clean_p:
            cursor.execute("SELECT * FROM candidates")
            for row in cursor.fetchall():
                cand_phone_norm = normalize_phone(row["mobile"])
                if cand_phone_norm and cand_phone_norm == clean_p:
                    return dict(row)

    return None


def upsert_candidate(
    name: str,
    email: str = "Not Specified",
    mobile: str = "Not available in CV",
    location: str = "Not Specified",
    current_organization: str = "Not Detected",
    current_designation: str = "Not Detected",
    previous_organizations: Optional[List[str]] = None,
    education: str = "Not Specified",
    certifications: Optional[List[str]] = None,
    total_experience: str = "Not Detected",
    relevant_experience: str = "Not Detected",
    resume_reference: str = "",
    initial_status: str = "Screened",
    candidate_id: Optional[str] = None,
    db_path: Optional[str] = None,
) -> str:
    """
    Insert or update candidate record.
    Returns candidate_id.
    """
    now_iso = datetime.now().isoformat()
    cid = candidate_id or str(uuid.uuid4())[:8]

    # Check duplicate if ID not provided
    if not candidate_id:
        existing = find_existing_candidate(email=email, mobile=mobile, db_path=db_path)
        if existing:
            cid = existing["candidate_id"]

    prev_orgs_json = json.dumps(previous_organizations or [])
    certs_json = json.dumps(certifications or [])

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT candidate_id FROM candidates WHERE candidate_id = ?", (cid,))
        exists = cursor.fetchone()

        if exists:
            cursor.execute(
                """
                UPDATE candidates
                SET name = ?, mobile = ?, email = ?, location = ?,
                    current_organization = ?, current_designation = ?,
                    previous_organizations = ?, education = ?, certifications = ?,
                    total_experience = ?, relevant_experience = ?, resume_reference = ?,
                    updated_at = ?
                WHERE candidate_id = ?
                """,
                (
                    name,
                    mobile or "Not available in CV",
                    email or "Not Specified",
                    location or "Not Specified",
                    current_organization or "Not Detected",
                    current_designation or "Not Detected",
                    prev_orgs_json,
                    education or "Not Specified",
                    certs_json,
                    total_experience or "Not Detected",
                    relevant_experience or "Not Detected",
                    resume_reference,
                    now_iso,
                    cid,
                ),
            )
        else:
            cursor.execute(
                """
                INSERT INTO candidates (
                    candidate_id, name, mobile, email, location,
                    current_organization, current_designation, previous_organizations,
                    education, certifications, total_experience, relevant_experience,
                    resume_reference, current_status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cid,
                    name,
                    mobile or "Not available in CV",
                    email or "Not Specified",
                    location or "Not Specified",
                    current_organization or "Not Detected",
                    current_designation or "Not Detected",
                    prev_orgs_json,
                    education or "Not Specified",
                    certs_json,
                    total_experience or "Not Detected",
                    relevant_experience or "Not Detected",
                    resume_reference,
                    initial_status,
                    now_iso,
                    now_iso,
                ),
            )
            # Record initial status in history
            cursor.execute(
                """
                INSERT INTO candidate_status_history (
                    candidate_id, previous_status, new_status, changed_at, notes, changed_by
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (cid, "None", initial_status, now_iso, "Candidate initially screened and registered", "System"),
            )

        conn.commit()

    return cid


def upsert_job(
    job_title: str,
    job_description: str,
    required_skills: Optional[List[str]] = None,
    preferred_skills: Optional[List[str]] = None,
    min_experience: float = 0.0,
    job_id: Optional[str] = None,
    db_path: Optional[str] = None,
) -> str:
    """Save or update target job record."""
    now_iso = datetime.now().isoformat()
    jid = job_id or f"job-{uuid.uuid4().hex[:6]}"
    req_json = json.dumps(required_skills or [])
    pref_json = json.dumps(preferred_skills or [])

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT job_id FROM jobs WHERE job_id = ?", (jid,))
        exists = cursor.fetchone()

        if exists:
            cursor.execute(
                """
                UPDATE jobs
                SET job_title = ?, job_description = ?, required_skills = ?,
                    preferred_skills = ?, min_experience = ?
                WHERE job_id = ?
                """,
                (job_title, job_description, req_json, pref_json, min_experience, jid),
            )
        else:
            cursor.execute(
                """
                INSERT INTO jobs (
                    job_id, job_title, job_description, required_skills, preferred_skills, min_experience, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (jid, job_title, job_description, req_json, pref_json, min_experience, now_iso),
            )
        conn.commit()

    return jid


def save_screening(
    candidate_id: str,
    job_id: str,
    deterministic_score: int,
    verdict: str,
    recommendation: str,
    skills_score: int = 0,
    exp_score: int = 0,
    cert_score: int = 0,
    matched_skills: Optional[List[str]] = None,
    missing_skills: Optional[List[str]] = None,
    evidence: Optional[Dict[str, Any]] = None,
    interview_questions: Optional[List[str]] = None,
    llm_analysis: str = "",
    llm_provider: str = "Offline / Deterministic",
    llm_model: str = "None",
    screening_id: Optional[str] = None,
    db_path: Optional[str] = None,
) -> str:
    """
    Save an authoritative screening record. Does NOT overwrite past screenings for the same candidate.
    """
    sid = screening_id or f"scr-{uuid.uuid4().hex[:8]}"
    now_iso = datetime.now().isoformat()

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO screenings (
                screening_id, candidate_id, job_id, screening_timestamp,
                deterministic_score, skills_score, exp_score, cert_score,
                matched_skills, missing_skills, verdict, recommendation,
                evidence, interview_questions, llm_analysis, llm_provider,
                llm_model, engine_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sid,
                candidate_id,
                job_id,
                now_iso,
                deterministic_score,
                skills_score,
                exp_score,
                cert_score,
                json.dumps(matched_skills or []),
                json.dumps(missing_skills or []),
                verdict,
                recommendation,
                json.dumps(evidence or {}),
                json.dumps(interview_questions or []),
                llm_analysis,
                llm_provider,
                llm_model,
                "2.0.0",
            ),
        )
        conn.commit()

    return sid


def associate_screening_files(
    screening_id: str,
    jd_file_id: Optional[str] = None,
    resume_file_id: Optional[str] = None,
    candidate_id: Optional[str] = None,
    job_id: Optional[str] = None,
    db_path: Optional[str] = None,
) -> None:
    """Associates stored files with their resulting screening record (many-to-many capable)."""
    now_iso = datetime.now().isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        if jd_file_id:
            cursor.execute(
                """
                INSERT INTO screening_files (screening_id, file_id, file_role, created_at)
                VALUES (?, ?, 'job_description', ?)
                """,
                (screening_id, jd_file_id, now_iso),
            )
            cursor.execute(
                "UPDATE stored_files SET screening_id = ?, job_id = COALESCE(?, job_id) WHERE file_id = ?",
                (screening_id, job_id, jd_file_id),
            )
        if resume_file_id:
            cursor.execute(
                """
                INSERT INTO screening_files (screening_id, file_id, file_role, created_at)
                VALUES (?, ?, 'resume', ?)
                """,
                (screening_id, resume_file_id, now_iso),
            )
            cursor.execute(
                "UPDATE stored_files SET screening_id = ?, candidate_id = COALESCE(?, candidate_id) WHERE file_id = ?",
                (screening_id, candidate_id, resume_file_id),
            )
        conn.commit()


def get_screening_files(screening_id: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    """Retrieves source JD and Resume file records associated with a screening."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT sf.*, scf.file_role
            FROM screening_files scf
            JOIN stored_files sf ON scf.file_id = sf.file_id
            WHERE scf.screening_id = ?
            ORDER BY scf.id ASC
            """,
            (screening_id,),
        )
        rows = [dict(r) for r in cursor.fetchall()]

    # Fallback to direct screening_id on stored_files if no junction rows
    if not rows:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT *, file_type AS file_role FROM stored_files WHERE screening_id = ?", (screening_id,))
            rows = [dict(r) for r in cursor.fetchall()]

    jd_file = next((r for r in rows if r.get("file_role") == "job_description" or r.get("file_type") == "job_description"), None)
    resume_file = next((r for r in rows if r.get("file_role") == "resume" or r.get("file_type") == "resume"), None)
    all_files = [f for f in (jd_file, resume_file) if f is not None]
    return {
        "jd_file": jd_file,
        "resume_file": resume_file,
        "files": all_files,
    }


def normalize_screening_files(files_data: Any) -> List[Dict[str, str]]:
    """
    Normalizes screening files data into a uniform list of file records.
    Each record contains:
      - 'original_filename': str
      - 'file_role': str ('JD', 'Resume', 'Document', or custom role)
      - 'stored_relative_path': str
      - 'file_id': str

    Safely handles:
      - Dictionary with 'jd_file', 'resume_file', or 'files'
      - List of file record dictionaries
      - List of stored filename strings or paths
      - Empty lists or None
      - Missing optional keys ('original_filename', 'file_role')
      - Malformed records with sanitized diagnostic logging
    """
    if not files_data:
        return []

    raw_items: List[Any] = []
    if isinstance(files_data, dict):
        if "files" in files_data and isinstance(files_data["files"], list):
            raw_items = files_data["files"]
        else:
            for k in ("jd_file", "resume_file"):
                val = files_data.get(k)
                if val:
                    raw_items.append(val)
            if not raw_items:
                for k, val in files_data.items():
                    if val and isinstance(val, (dict, str)):
                        raw_items.append(val)
    elif isinstance(files_data, list):
        raw_items = files_data
    elif isinstance(files_data, str):
        raw_items = [files_data]
    else:
        logger.warning("Sanitized: Invalid files_data type passed to normalize_screening_files: %s", type(files_data).__name__)
        return []

    normalized: List[Dict[str, str]] = []
    for item in raw_items:
        if isinstance(item, dict):
            raw_name = (
                item.get("original_filename")
                or item.get("filename")
                or (os.path.basename(item["stored_relative_path"]) if item.get("stored_relative_path") else "")
                or "Unknown Document"
            )
            raw_role = item.get("file_role") or item.get("file_type")
            if not raw_role:
                check_str = (item.get("stored_relative_path") or raw_name).lower()
                if "jd" in check_str or "job" in check_str:
                    role_label = "JD"
                elif "resume" in check_str or "cv" in check_str:
                    role_label = "Resume"
                else:
                    role_label = "Document"
            else:
                role_str = str(raw_role).strip()
                role_lower = role_str.lower()
                if "jd" in role_lower or "job" in role_lower:
                    role_label = "JD"
                elif "resume" in role_lower or "cv" in role_lower:
                    role_label = "Resume"
                else:
                    role_label = role_str.capitalize() if role_str else "Document"

            normalized.append({
                "original_filename": str(raw_name),
                "file_role": role_label,
                "stored_relative_path": str(item.get("stored_relative_path") or ""),
                "file_id": str(item.get("file_id") or ""),
            })
        elif isinstance(item, str):
            clean_str = item.strip()
            if not clean_str:
                continue
            name = os.path.basename(clean_str)
            lower = name.lower()
            if "jd" in lower or "job" in lower:
                role_label = "JD"
            elif "resume" in lower or "cv" in lower:
                role_label = "Resume"
            else:
                role_label = "Document"

            normalized.append({
                "original_filename": name,
                "file_role": role_label,
                "stored_relative_path": clean_str,
                "file_id": "",
            })
        else:
            logger.warning("Sanitized: Skipped malformed screening file record item of type: %s", type(item).__name__)
            continue

    return normalized




def update_candidate_status(
    candidate_id: str,
    new_status: str,
    notes: str = "",
    changed_by: str = "Recruiter",
    screening_id: Optional[str] = None,
    db_path: Optional[str] = None,
) -> bool:
    """Updates candidate status with validation and writes an immutable audit record."""
    if new_status not in CANDIDATE_STATUSES:
        return False

    now_iso = datetime.now().isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT current_status FROM candidates WHERE candidate_id = ?", (candidate_id,))
        row = cursor.fetchone()
        if not row:
            return False

        prev_status = row["current_status"]
        cursor.execute(
            "UPDATE candidates SET current_status = ?, updated_at = ? WHERE candidate_id = ?",
            (new_status, now_iso, candidate_id),
        )
        cursor.execute(
            """
            INSERT INTO candidate_status_history (
                candidate_id, screening_id, previous_status, new_status, changed_at, notes, changed_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (candidate_id, screening_id, prev_status, new_status, now_iso, notes, changed_by),
        )
        conn.commit()
    return True


def get_candidate_by_id(candidate_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve candidate profile by ID."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM candidates WHERE candidate_id = ?", (candidate_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_distinct_target_jobs(db_path: Optional[str] = None) -> List[str]:
    """Retrieve distinct target job titles saved in database."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT job_title FROM jobs WHERE job_title IS NOT NULL AND TRIM(job_title) != '' ORDER BY job_title ASC")
        return [r["job_title"] for r in cursor.fetchall()]


def add_follow_up(
    candidate_id: str,
    follow_up_date: str,
    notes: str = "",
    screening_id: Optional[str] = None,
    db_path: Optional[str] = None,
) -> int:
    """Persists candidate follow-up date."""
    now_iso = datetime.now().isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO follow_ups (
                candidate_id, screening_id, follow_up_date, status, notes, created_at
            ) VALUES (?, ?, ?, 'pending', ?, ?)
            """,
            (candidate_id, screening_id, follow_up_date, notes, now_iso),
        )
        conn.commit()
        return cursor.lastrowid


def search_candidates_portal_wide(
    query_term: str = "",
    status_filter: Optional[str] = None,
    target_job: Optional[str] = None,
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    screening_date_start: Optional[str] = None,
    screening_date_end: Optional[str] = None,
    follow_up_filter: Optional[str] = None,
    follow_up_date: Optional[str] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Search candidate records across the complete registry.
    Supports searches by full name, partial name, email, mobile, candidate ID,
    screening reference, current organization, current designation, target job,
    and recruitment status using normalized search terms and parameterized SQL.
    """
    init_db(db_path)
    today_str = date.today().isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        sql = """
            SELECT
                c.*,
                s.screening_id,
                s.deterministic_score,
                s.verdict,
                s.recommendation,
                s.screening_timestamp,
                s.llm_provider,
                s.llm_model,
                j.job_title,
                f.follow_up_date,
                f.notes AS follow_up_notes
            FROM candidates c
            LEFT JOIN (
                SELECT s1.*
                FROM screenings s1
                INNER JOIN (
                    SELECT candidate_id, MAX(screening_timestamp) AS max_ts
                    FROM screenings
                    GROUP BY candidate_id
                ) s2 ON s1.candidate_id = s2.candidate_id AND s1.screening_timestamp = s2.max_ts
            ) s ON c.candidate_id = s.candidate_id
            LEFT JOIN jobs j ON s.job_id = j.job_id
            LEFT JOIN (
                SELECT candidate_id, MIN(follow_up_date) AS follow_up_date, notes
                FROM follow_ups
                WHERE status = 'pending'
                GROUP BY candidate_id
            ) f ON c.candidate_id = f.candidate_id
            WHERE 1=1
        """
        params: List[Any] = []

        if query_term:
            term = query_term.strip()
            term_like = f"%{term.lower()}%"
            clean_digits = re.sub(r"\D", "", term)
            phone_clause = ""
            if len(clean_digits) >= 4:
                phone_clause = " OR c.mobile LIKE ?"

            sql += f"""
                AND (
                    LOWER(c.name) LIKE ?
                    OR LOWER(c.email) LIKE ?
                    OR LOWER(c.mobile) LIKE ?
                    OR LOWER(c.candidate_id) LIKE ?
                    OR LOWER(c.resume_reference) LIKE ?
                    OR LOWER(c.current_organization) LIKE ?
                    OR LOWER(c.current_designation) LIKE ?
                    OR LOWER(COALESCE(j.job_title, '')) LIKE ?
                    OR LOWER(c.current_status) LIKE ?
                    OR LOWER(COALESCE(s.screening_id, '')) LIKE ?
                    {phone_clause}
                )
            """
            params.extend([
                term_like, term_like, term_like, term_like, term_like,
                term_like, term_like, term_like, term_like, term_like,
            ])
            if phone_clause:
                params.append(f"%{clean_digits}%")

        if status_filter and status_filter != "All":
            sql += " AND c.current_status = ?"
            params.append(status_filter)

        if min_score is not None:
            sql += " AND s.deterministic_score >= ?"
            params.append(min_score)

        if max_score is not None:
            sql += " AND s.deterministic_score <= ?"
            params.append(max_score)

        if target_job and target_job != "All":
            sql += " AND j.job_title = ?"
            params.append(target_job)

        if screening_date_start:
            sql += " AND s.screening_timestamp >= ?"
            params.append(screening_date_start)

        if screening_date_end:
            sql += " AND s.screening_timestamp <= ?"
            params.append(screening_date_end)

        if follow_up_date:
            sql += " AND f.follow_up_date = ?"
            params.append(follow_up_date)
        elif follow_up_filter and follow_up_filter != "All":
            if follow_up_filter == "Overdue":
                sql += " AND f.follow_up_date IS NOT NULL AND f.follow_up_date < ?"
                params.append(today_str)
            elif follow_up_filter == "Due Today":
                sql += " AND f.follow_up_date = ?"
                params.append(today_str)
            elif follow_up_filter == "Upcoming":
                sql += " AND f.follow_up_date > ?"
                params.append(today_str)
            elif follow_up_filter == "Has Follow-up":
                sql += " AND f.follow_up_date IS NOT NULL"
            elif follow_up_filter == "No Follow-up":
                sql += " AND f.follow_up_date IS NULL"

        sql += " ORDER BY c.updated_at DESC"
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]


def get_all_candidates_with_latest_screening(
    search_query: str = "",
    status_filter: Optional[str] = None,
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    target_job: Optional[str] = None,
    follow_up_filter: Optional[str] = None,
    db_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Retrieve all candidates joined with their latest screening profile and follow-ups."""
    return search_candidates_portal_wide(
        query_term=search_query,
        status_filter=status_filter,
        target_job=target_job,
        min_score=min_score,
        max_score=max_score,
        follow_up_filter=follow_up_filter,
        db_path=db_path,
    )


def get_candidates_screened_for_role(job_title: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve all candidates who have been screened for a specific target job."""
    init_db(db_path)
    term = f"%{job_title.strip().lower()}%"
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.*, s.screening_id, s.deterministic_score, s.verdict, s.recommendation,
                   s.screening_timestamp, j.job_title
            FROM screenings s
            JOIN candidates c ON s.candidate_id = c.candidate_id
            JOIN jobs j ON s.job_id = j.job_id
            WHERE LOWER(j.job_title) LIKE ?
            ORDER BY s.screening_timestamp DESC
            """,
            (term,),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_candidate_screening_for_role(
    candidate_id: str,
    job_title: str,
    db_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Retrieve the screening record for a candidate for a specific job title."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT s.*, j.job_title, j.job_description
            FROM screenings s
            JOIN jobs j ON s.job_id = j.job_id
            WHERE s.candidate_id = ? AND LOWER(j.job_title) LIKE ?
            ORDER BY s.screening_timestamp DESC
            LIMIT 1
            """,
            (candidate_id, f"%{job_title.strip().lower()}%"),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_candidate_by_name_or_query(name_or_query: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Resolves candidate records matching a name, ID, or query token.
    Prioritizes:
    1. Exact candidate_id
    2. Exact screening_id
    3. Exact email
    4. Exact mobile digits
    5. Exact full name match
    6. Token / partial name match
    """
    clean_q = name_or_query.strip()
    if not clean_q:
        return []
    clean_lower = clean_q.lower()

    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. Exact candidate_id
        cursor.execute("SELECT * FROM candidates WHERE candidate_id = ?", (clean_q,))
        row = cursor.fetchone()
        if row:
            return [dict(row)]

        # 2. Exact screening_id
        cursor.execute(
            """
            SELECT c.* FROM candidates c
            JOIN screenings s ON c.candidate_id = s.candidate_id
            WHERE s.screening_id = ?
            LIMIT 1
            """,
            (clean_q,),
        )
        row = cursor.fetchone()
        if row:
            return [dict(row)]

        # 3. Exact email
        cursor.execute("SELECT * FROM candidates WHERE LOWER(email) = ?", (clean_lower,))
        rows = cursor.fetchall()
        if rows:
            return [dict(r) for r in rows]

        # 4. Mobile number match
        digits = re.sub(r"\D", "", clean_q)
        if len(digits) >= 10:
            cursor.execute("SELECT * FROM candidates WHERE mobile LIKE ?", (f"%{digits[-10:]}%",))
            rows = cursor.fetchall()
            if rows:
                return [dict(r) for r in rows]

        # 5. Exact full name match
        cursor.execute("SELECT * FROM candidates WHERE LOWER(name) = ?", (clean_lower,))
        rows = cursor.fetchall()
        if rows:
            return [dict(r) for r in rows]

        # 6. Name starts with or contains
        cursor.execute("SELECT * FROM candidates WHERE LOWER(name) LIKE ?", (f"%{clean_lower}%",))
        rows = cursor.fetchall()
        if rows:
            return [dict(r) for r in rows]

        # 7. Word boundary token match (min 3 chars)
        cursor.execute("SELECT * FROM candidates")
        all_cands = [dict(r) for r in cursor.fetchall()]
        matched = []
        for cand in all_cands:
            c_name = cand["name"].lower()
            for part in c_name.split():
                if len(part) >= 3 and (part == clean_lower or clean_lower == part or re.search(rf"\b{re.escape(clean_lower)}\b", c_name)):
                    if cand not in matched:
                        matched.append(cand)
                    break
        return matched


def get_candidate_screenings(candidate_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get complete chronological screening history for a candidate."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT s.*, j.job_title, j.job_description
            FROM screenings s
            LEFT JOIN jobs j ON s.job_id = j.job_id
            WHERE s.candidate_id = ?
            ORDER BY s.screening_timestamp DESC
            """,
            (candidate_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_candidate_status_history(candidate_id: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get status change history timeline."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM candidate_status_history
            WHERE candidate_id = ?
            ORDER BY changed_at DESC
            """,
            (candidate_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_follow_ups_overview(db_path: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """
    Categorizes follow-ups into overdue, due_today, and upcoming.
    """
    today_str = date.today().isoformat()
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT f.*, c.name AS candidate_name, c.current_status, c.current_designation, c.mobile
            FROM follow_ups f
            JOIN candidates c ON f.candidate_id = c.candidate_id
            WHERE f.status = 'pending'
            ORDER BY f.follow_up_date ASC
            """
        )
        rows = [dict(r) for r in cursor.fetchall()]

    overdue = [r for r in rows if r["follow_up_date"] < today_str]
    due_today = [r for r in rows if r["follow_up_date"] == today_str]
    upcoming = [r for r in rows if r["follow_up_date"] > today_str]

    return {
        "overdue": overdue,
        "due_today": due_today,
        "upcoming": upcoming,
    }


def export_candidates_csv(db_path: Optional[str] = None) -> str:
    """Exports candidates and latest screening results to CSV string."""
    records = get_all_candidates_with_latest_screening(db_path=db_path)
    output = io.StringIO()
    writer = csv.writer(output)

    headers = [
        "Candidate ID", "Name", "Mobile", "Email", "Current Designation",
        "Current Organization", "Location", "Total Experience", "Target Job",
        "Deterministic Score", "Verdict", "Current Status", "Last Screened"
    ]
    writer.writerow(headers)

    for r in records:
        writer.writerow([
            r.get("candidate_id", ""),
            r.get("name", ""),
            r.get("mobile", "Not available in CV"),
            r.get("email", ""),
            r.get("current_designation", ""),
            r.get("current_organization", ""),
            r.get("location", ""),
            r.get("total_experience", ""),
            r.get("job_title", "Unassigned"),
            r.get("deterministic_score", "N/A"),
            r.get("verdict", ""),
            r.get("current_status", ""),
            r.get("screening_timestamp", r.get("created_at", "")),
        ])
    return output.getvalue()
