# 💾 Backup, Retention & Disaster Recovery — FITMENT.AI

> **Audience**: Systems Administrators, DevOps Leads, and Database Operators.  
> **Last Reviewed**: 2026-10-19  

---

## 1. Storage Footprint Overview

All persistent state in FITMENT.AI resides under the `./data` directory:
- **`data/fitment.db`**: SQLite database containing all candidate profiles, screening scorecards, status history, and file catalogs.
- **`data/job_descriptions/`**: Stored job description documents (.docx, .pdf, .txt).
- **`data/resumes/`**: Stored candidate resumes (.docx, .pdf, .txt).
- **`data/logs/`**: Application diagnostic logs and runtime traces.

---

## 2. Backup Procedures

### 2.1 Online Hot Database Snapshot (PowerShell)
Because SQLite supports atomic read locks, hot backups can be taken while Streamlit is actively serving recruiters:

```powershell
# Create automated timestamped snapshot
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "data/fitment_backup_$timestamp.db"
Copy-Item data/fitment.db $backupFile
Write-Host "✅ Database snapshot saved to: $backupFile"
```

### 2.2 Complete Storage Archive (Database + Documents)
To take a full archival backup of all database tables and physical uploaded files:

```powershell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$archiveZip = "fitment_full_backup_$timestamp.zip"
Compress-Archive -Path "data/fitment.db", "data/job_descriptions", "data/resumes" -DestinationPath $archiveZip
Write-Host "✅ Full platform archive created: $archiveZip"
```

---

## 3. Disaster Recovery & Restoration

If the database becomes corrupted or a host failure occurs:

### Step 1: Terminate Active Streamlit Server
```powershell
Stop-Process -Name python -Force -ErrorAction SilentlyContinue
```

### Step 2: Restore Database Snapshot
```powershell
# Restore from preferred backup file
Copy-Item "data/fitment_backup_<timestamp>.db" data/fitment.db -Force
```

### Step 3: Verify Integrity & Start Server
```powershell
# Verify SQLite integrity
python -c "import sqlite3; conn = sqlite3.connect('data/fitment.db'); print(conn.execute('PRAGMA integrity_check;').fetchall())"

# Restart portal
streamlit run app.py
```

---

## 4. Storage Retention & Pruning Policy

To comply with data privacy regulations (e.g. GDPR, CCPA) or reclaim host disk space:

### Pruning Physical Resumes Older Than 180 Days
```powershell
$limit = (Get-Date).AddDays(-180)
Get-ChildItem -Path "data/resumes", "data/job_descriptions" -File | Where-Object { $_.LastWriteTime -lt $limit } | Remove-Item
Write-Host "✅ Purged physical files older than 180 days."
```
> [!NOTE]
> Pruning physical document files does **not** corrupt candidate profiles or fitment scorecards in `fitment.db`. The candidate records, scores, and status history remain fully accessible in the Candidate Tracker.
