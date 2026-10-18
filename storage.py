"""
Recruitment Intelligence Platform — Persistent File Storage Engine
Handles atomic, durable, collision-safe file persistence for uploaded Job Descriptions and CVs/Resumes.
Ensures path-traversal safety, SHA-256 deduplication, file-size enforcement, and SQLite indexing.
"""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import registry

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB limit


def get_base_data_dir(custom_dir: Optional[str] = None) -> str:
    """Resolve configured or default project data directory safely."""
    if custom_dir:
        return os.path.abspath(custom_dir)
    env_dir = os.getenv("FITMENT_DATA_DIR")
    if env_dir:
        return os.path.abspath(env_dir)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))


def get_storage_dirs(base_dir: Optional[str] = None) -> Tuple[str, str, str, str]:
    """
    Ensures and returns (base_dir, jd_dir, resumes_dir, logs_dir).
    Creates directories automatically if they do not exist.
    """
    base = get_base_data_dir(base_dir)
    jd_dir = os.path.join(base, "job_descriptions")
    resumes_dir = os.path.join(base, "resumes")
    logs_dir = os.path.join(base, "logs")

    os.makedirs(base, exist_ok=True)
    os.makedirs(jd_dir, exist_ok=True)
    os.makedirs(resumes_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)

    return base, jd_dir, resumes_dir, logs_dir


def compute_sha256(data: bytes) -> str:
    """Calculate SHA-256 checksum of file bytes."""
    return hashlib.sha256(data).hexdigest()


def sanitize_filename(filename: str) -> Tuple[str, str]:
    """
    Sanitize uploaded filename to prevent directory traversal and filesystem attacks.
    Returns (clean_stem, clean_extension).
    """
    # Extract basename only to strip any path components
    base_name = os.path.basename(filename)
    stem, ext = os.path.splitext(base_name)
    ext = ext.lower().strip()

    # Replace spaces and non-alphanumeric chars with underscores
    clean_stem = re.sub(r"[^\w\-.]", "_", stem)
    clean_stem = re.sub(r"_+", "_", clean_stem).strip("._")
    if not clean_stem:
        clean_stem = "file"

    return clean_stem[:60], ext


def validate_file_upload(filename: str, file_bytes: bytes) -> Tuple[bool, str]:
    """
    Validates file extension, length, and size.
    Returns (is_valid: bool, error_message: str).
    """
    if not filename or not filename.strip():
        return False, "Filename cannot be empty."

    _, ext = sanitize_filename(filename)
    if ext not in ALLOWED_EXTENSIONS:
        allowed_str = ", ".join(sorted(list(ALLOWED_EXTENSIONS)))
        return False, f"Unsupported file extension '{ext}'. Allowed formats: {allowed_str}"

    if not file_bytes or len(file_bytes) == 0:
        return False, "Uploaded file is empty (0 bytes)."

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        mb_size = round(len(file_bytes) / (1024 * 1024), 2)
        max_mb = round(MAX_FILE_SIZE_BYTES / (1024 * 1024), 0)
        return False, f"File size ({mb_size} MB) exceeds maximum allowed limit of {max_mb} MB."

    return True, ""


def resolve_stored_path(path_or_dict: Union[str, Dict[str, Any]], base_dir: Optional[str] = None) -> str:
    """
    Safely resolves a stored relative path or file dictionary against base data directory,
    enforcing that the resolved path cannot escape base_dir (path traversal prevention).
    Supports legacy absolute paths if within allowed project boundaries.
    """
    if isinstance(path_or_dict, dict):
        raw_path = (
            path_or_dict.get("stored_path")
            or path_or_dict.get("stored_relative_path")
            or path_or_dict.get("stored_absolute_path")
            or ""
        )
    else:
        raw_path = str(path_or_dict or "")

    clean_p = raw_path.strip().replace("\\", "/")
    if not clean_p:
        raise ValueError("Cannot resolve empty file path")

    base = os.path.abspath(get_base_data_dir(base_dir))

    # Reject obvious traversal sequences
    parts = [part for part in clean_p.split("/") if part]
    if ".." in parts:
        raise PermissionError(f"Security Alert: Path traversal attempt detected for '{raw_path}'")

    # If already an absolute path
    if os.path.isabs(clean_p) or (len(clean_p) > 2 and clean_p[1] == ":"):
        target_path = os.path.abspath(clean_p)
        try:
            common = os.path.commonpath([base, target_path])
            if common == base:
                return target_path
        except ValueError:
            pass
        # Check if within project root
        project_root = os.path.abspath(os.path.dirname(base))
        try:
            common_proj = os.path.commonpath([project_root, target_path])
            if common_proj == project_root:
                return target_path
        except ValueError:
            pass
        raise PermissionError(f"Security Alert: Absolute path outside allowed directory: '{raw_path}'")

    # Strip leading 'data/' if relative
    if clean_p.startswith("data/"):
        clean_p = clean_p[5:]

    target_path = os.path.abspath(os.path.join(base, clean_p))
    try:
        common = os.path.commonpath([base, target_path])
        if common != base:
            raise PermissionError(f"Security Alert: Path traversal attempt detected for '{raw_path}'")
    except ValueError:
        raise PermissionError(f"Security Alert: Path traversal attempt detected for '{raw_path}'")

    return target_path


def read_stored_file_bytes(file_ref: Union[str, Dict[str, Any]], base_dir: Optional[str] = None) -> bytes:
    """Reads bytes of a stored file or dictionary record with path-traversal safety check."""
    if isinstance(file_ref, dict):
        relative_path = (
            file_ref.get("stored_path")
            or file_ref.get("stored_relative_path")
            or file_ref.get("stored_absolute_path")
        )
        if not relative_path:
            raise KeyError("File record dictionary missing 'stored_path' or 'stored_relative_path'")
    else:
        relative_path = file_ref

    full_path = resolve_stored_path(relative_path, base_dir)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"Stored file does not exist at '{relative_path}'")
    with open(full_path, "rb") as f:
        return f.read()


def save_job_description_file(
    file_bytes: bytes,
    original_filename: str,
    job_id: Optional[str] = None,
    base_dir: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Atomically saves an uploaded Job Description in data/job_descriptions/.
    Handles deduplication, validates size, and records metadata in database.
    Returns unified file metadata contract.
    """
    is_valid, err_msg = validate_file_upload(original_filename, file_bytes)
    if not is_valid:
        return {"status": "error", "message": err_msg}

    base, jd_dir, _, _ = get_storage_dirs(base_dir)
    checksum = compute_sha256(file_bytes)
    clean_stem, ext = sanitize_filename(original_filename)

    # Check for identical existing file in database
    with registry.get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM stored_files WHERE file_type = 'job_description' AND sha256_hash = ?",
            (checksum,),
        )
        existing_row = cursor.fetchone()
        if existing_row:
            existing = dict(existing_row)
            rel_path = existing.get("stored_relative_path") or existing.get("stored_path")
            abs_path = resolve_stored_path(rel_path, base)
            if os.path.exists(abs_path) and os.path.getsize(abs_path) == len(file_bytes):
                return {
                    "status": "success",
                    "file_id": existing["file_id"],
                    "original_filename": original_filename,
                    "file_role": "jd",
                    "file_type": "job_description",
                    "stored_path": rel_path,
                    "stored_relative_path": rel_path,
                    "stored_absolute_path": abs_path,
                    "file_size": len(file_bytes),
                    "sha256": checksum,
                    "sha256_hash": checksum,
                    "uploaded_at": existing.get("upload_timestamp", datetime.now().isoformat()),
                    "upload_timestamp": existing.get("upload_timestamp", datetime.now().isoformat()),
                    "reused": True,
                    "message": f"✅ JD — {original_filename} verified and reused from data/job_descriptions/",
                }

    # Generate collision-safe filename
    file_uuid = uuid.uuid4().hex[:8]
    stored_name = f"JD_{clean_stem}_{file_uuid}{ext}"
    target_abs_path = os.path.join(jd_dir, stored_name)
    rel_stored_path = f"data/job_descriptions/{stored_name}"

    # Atomic write using NamedTemporaryFile
    try:
        temp_fd, temp_path = tempfile.mkstemp(dir=jd_dir, prefix="temp_jd_")
        with os.fdopen(temp_fd, "wb") as f:
            f.write(file_bytes)
            f.flush()
            os.fsync(f.fileno())

        # Atomic replace
        os.replace(temp_path, target_abs_path)

        # Verification
        if not os.path.exists(target_abs_path) or os.path.getsize(target_abs_path) != len(file_bytes):
            raise IOError("Written file size does not match uploaded bytes.")
    except Exception as exc:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        return {"status": "error", "message": f"Filesystem write failed for '{original_filename}': {str(exc)}"}

    # Record in database
    file_id = f"file-jd-{file_uuid}"
    now_iso = datetime.now().isoformat()
    with registry.get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO stored_files (
                file_id, file_type, original_filename, stored_relative_path,
                file_size, sha256_hash, upload_timestamp, job_id
            ) VALUES (?, 'job_description', ?, ?, ?, ?, ?, ?)
            """,
            (file_id, original_filename, rel_stored_path, len(file_bytes), checksum, now_iso, job_id),
        )
        # Update stored_path column if table supports it
        try:
            cursor.execute("UPDATE stored_files SET stored_path = ? WHERE file_id = ?", (rel_stored_path, file_id))
        except Exception:
            pass
        conn.commit()

    return {
        "status": "success",
        "file_id": file_id,
        "original_filename": original_filename,
        "file_role": "jd",
        "file_type": "job_description",
        "stored_path": rel_stored_path,
        "stored_relative_path": rel_stored_path,
        "stored_absolute_path": target_abs_path,
        "file_size": len(file_bytes),
        "sha256": checksum,
        "sha256_hash": checksum,
        "uploaded_at": now_iso,
        "upload_timestamp": now_iso,
        "reused": False,
        "message": f"✅ JD — {original_filename} saved successfully in data/job_descriptions/",
    }


def save_resume_file(
    file_bytes: bytes,
    original_filename: str,
    candidate_name: str = "",
    candidate_id: Optional[str] = None,
    base_dir: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Atomically saves an uploaded CV/Resume in data/resumes/.
    Handles deduplication, validates size, preserves original file extension,
    and records metadata in database with unified metadata contract.
    """
    is_valid, err_msg = validate_file_upload(original_filename, file_bytes)
    if not is_valid:
        return {"status": "error", "message": err_msg}

    base, _, resumes_dir, _ = get_storage_dirs(base_dir)
    checksum = compute_sha256(file_bytes)

    # Always preserve the original file extension from original_filename
    _, ext = sanitize_filename(original_filename)
    if candidate_name and candidate_name.strip():
        clean_cand_stem, _ = sanitize_filename(candidate_name)
        stem_to_use = clean_cand_stem
    else:
        stem_to_use, _ = sanitize_filename(original_filename)

    # Check for identical existing file in database
    with registry.get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM stored_files WHERE file_type = 'resume' AND sha256_hash = ?",
            (checksum,),
        )
        existing_row = cursor.fetchone()
        if existing_row:
            existing = dict(existing_row)
            rel_path = existing.get("stored_relative_path") or existing.get("stored_path")
            abs_path = resolve_stored_path(rel_path, base)
            if os.path.exists(abs_path) and os.path.getsize(abs_path) == len(file_bytes):
                # Update candidate association if candidate_id provided
                if candidate_id:
                    cursor.execute(
                        "UPDATE stored_files SET candidate_id = ? WHERE file_id = ?",
                        (candidate_id, existing["file_id"]),
                    )
                    conn.commit()
                return {
                    "status": "success",
                    "file_id": existing["file_id"],
                    "original_filename": original_filename,
                    "file_role": "resume",
                    "file_type": "resume",
                    "stored_path": rel_path,
                    "stored_relative_path": rel_path,
                    "stored_absolute_path": abs_path,
                    "file_size": len(file_bytes),
                    "sha256": checksum,
                    "sha256_hash": checksum,
                    "uploaded_at": existing.get("upload_timestamp", datetime.now().isoformat()),
                    "upload_timestamp": existing.get("upload_timestamp", datetime.now().isoformat()),
                    "candidate_id": candidate_id or existing.get("candidate_id"),
                    "reused": True,
                    "message": f"✅ Resume — {original_filename} verified and reused from data/resumes/",
                }

    # Generate collision-safe filename preserving extension
    file_uuid = uuid.uuid4().hex[:8]
    stored_name = f"{stem_to_use}_{file_uuid}{ext}"
    target_abs_path = os.path.join(resumes_dir, stored_name)
    rel_stored_path = f"data/resumes/{stored_name}"

    # Atomic write
    try:
        temp_fd, temp_path = tempfile.mkstemp(dir=resumes_dir, prefix="temp_cv_")
        with os.fdopen(temp_fd, "wb") as f:
            f.write(file_bytes)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_path, target_abs_path)

        if not os.path.exists(target_abs_path) or os.path.getsize(target_abs_path) != len(file_bytes):
            raise IOError("Written resume file size does not match uploaded bytes.")
    except Exception as exc:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        return {"status": "error", "message": f"Filesystem write failed for '{original_filename}': {str(exc)}"}

    # Record in database
    file_id = f"file-cv-{file_uuid}"
    now_iso = datetime.now().isoformat()
    with registry.get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO stored_files (
                file_id, file_type, original_filename, stored_relative_path,
                file_size, sha256_hash, upload_timestamp, candidate_id
            ) VALUES (?, 'resume', ?, ?, ?, ?, ?, ?)
            """,
            (file_id, original_filename, rel_stored_path, len(file_bytes), checksum, now_iso, candidate_id),
        )
        try:
            cursor.execute("UPDATE stored_files SET stored_path = ? WHERE file_id = ?", (rel_stored_path, file_id))
        except Exception:
            pass
        conn.commit()

    return {
        "status": "success",
        "file_id": file_id,
        "original_filename": original_filename,
        "file_role": "resume",
        "file_type": "resume",
        "stored_path": rel_stored_path,
        "stored_relative_path": rel_stored_path,
        "stored_absolute_path": target_abs_path,
        "file_size": len(file_bytes),
        "sha256": checksum,
        "sha256_hash": checksum,
        "uploaded_at": now_iso,
        "upload_timestamp": now_iso,
        "candidate_id": candidate_id,
        "reused": False,
        "message": f"✅ Resume — {original_filename} saved successfully in data/resumes/",
    }


def list_saved_job_descriptions(base_dir: Optional[str] = None, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all persisted Job Description files available for reuse with normalized contract."""
    registry.init_db(db_path)
    base, _, _, _ = get_storage_dirs(base_dir)
    with registry.get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM stored_files
            WHERE file_type = 'job_description'
            ORDER BY upload_timestamp DESC
            """
        )
        rows = [dict(r) for r in cursor.fetchall()]

    # Verify each file exists on disk and normalize contract
    valid = []
    for r in rows:
        try:
            stored_p = r.get("stored_relative_path") or r.get("stored_path")
            full_p = resolve_stored_path(stored_p, base)
            if os.path.exists(full_p):
                r["stored_path"] = stored_p
                r["stored_relative_path"] = stored_p
                r["stored_absolute_path"] = full_p
                r["file_role"] = "jd"
                r["sha256"] = r.get("sha256_hash")
                r["uploaded_at"] = r.get("upload_timestamp")
                valid.append(r)
        except Exception:
            continue
    return valid


def list_saved_resumes(base_dir: Optional[str] = None, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all persisted Resume/CV files available for reuse with normalized contract."""
    registry.init_db(db_path)
    base, _, _, _ = get_storage_dirs(base_dir)
    with registry.get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT sf.*, c.name AS candidate_name
            FROM stored_files sf
            LEFT JOIN candidates c ON sf.candidate_id = c.candidate_id
            WHERE sf.file_type = 'resume'
            ORDER BY sf.upload_timestamp DESC
            """
        )
        rows = [dict(r) for r in cursor.fetchall()]

    valid = []
    for r in rows:
        try:
            stored_p = r.get("stored_relative_path") or r.get("stored_path")
            full_p = resolve_stored_path(stored_p, base)
            if os.path.exists(full_p):
                r["stored_path"] = stored_p
                r["stored_relative_path"] = stored_p
                r["stored_absolute_path"] = full_p
                r["file_role"] = "resume"
                r["sha256"] = r.get("sha256_hash")
                r["uploaded_at"] = r.get("upload_timestamp")
                valid.append(r)
        except Exception:
            continue
    return valid
