# 🔗 Entity Relationships & Junction Model — FITMENT.AI

> **Audience**: Database Designers, Systems Integrators, and Backend Engineers.  
> **Last Reviewed**: 2026-10-19  
> **Primary Source Code**: [`registry.py`](file:///e:/Projects/resume-screening-agent/registry.py), [`storage.py`](file:///e:/Projects/resume-screening-agent/storage.py).

---

## 1. Relational Entity Overview

FITMENT.AI models the talent acquisition pipeline using a relational entity model. It balances strict normalization with high-speed read performance for candidate dashboards and conversational retrieval.

```mermaid
erDiagram
    CANDIDATES ||--o{ SCREENINGS : "1 to N (Historical Screenings)"
    CANDIDATES ||--o{ CANDIDATE_STATUS_HISTORY : "1 to N (Audit Trail)"
    CANDIDATES ||--o{ FOLLOW_UPS : "1 to N (Task Reminders)"
    CANDIDATES ||--o{ STORED_FILES : "1 to N (Associated Resumes)"
    JOBS ||--o{ SCREENINGS : "1 to N (Role Evaluations)"
    JOBS ||--o{ STORED_FILES : "1 to N (Associated JDs)"
    SCREENINGS ||--|{ SCREENING_FILES : "1 to N (Junction Records)"
    STORED_FILES ||--o{ SCREENING_FILES : "1 to N (File References)"
```

---

## 2. Cardinality Analysis

| Relationship | Cardinality | Business Meaning | Constraint Rule |
| :--- | :--- | :--- | :--- |
| **`candidates` $\rightarrow$ `screenings`** | $1 : N$ | A single candidate can be screened multiple times across different dates or against different job descriptions. | `ON DELETE CASCADE`: Deleting a candidate removes their evaluation history. |
| **`jobs` $\rightarrow$ `screenings`** | $1 : N$ | A single job requisition can evaluate dozens or hundreds of candidate applicants. | `ON DELETE CASCADE`: Deleting a job removes associated screening runs. |
| **`candidates` $\rightarrow$ `candidate_status_history`** | $1 : N$ | Every pipeline stage transition generates an immutable chronological audit row. | `ON DELETE CASCADE`. |
| **`candidates` $\rightarrow$ `follow_ups`** | $1 : N$ | A candidate can have multiple scheduled follow-up tasks and deadlines over their recruitment lifecycle. | `ON DELETE CASCADE`. |
| **`screenings` $\leftrightarrow$ `stored_files`** | $M : N$ | Screenings connect to stored files via the `screening_files` junction table. | Enforces referential integrity while permitting file reuse. |

---

## 3. The Many-to-Many Screening Files Junction Model

### The Problem in Traditional Recruitment Systems
In naive designs, a screening table contains two string columns: `jd_path` and `resume_path`. This causes major limitations:
1. **Redundant Storage**: If 50 candidates apply for the same "Senior Voice Engineer" role, the JD file is saved 50 times, consuming disk space.
2. **Broken File Tracing**: If a JD is modified or updated, historical screenings lose track of the exact original document version evaluated.
3. **Collision Vulnerability**: Resumes with identical filenames (e.g. `Resume.pdf`) overwrite each other.

### The FITMENT.AI Solution
FITMENT.AI separates **Physical File Storage** from **Screening Events** using the `screening_files` junction table:

```mermaid
flowchart LR
    subgraph Files ["stored_files Table (Deduplicated via SHA-256)"]
        JD1["File ID: jd-001<br/>(Voice_L3_Requisition.docx)"]
        CV1["File ID: cv-101<br/>(Tarun_CV.pdf)"]
        CV2["File ID: cv-102<br/>(Prachi_CV.pdf)"]
    end

    subgraph Junction ["screening_files Junction Table"]
        J1["Junction 1: (Screening A, jd-001, 'jd')"]
        J2["Junction 2: (Screening A, cv-101, 'resume')"]
        J3["Junction 3: (Screening B, jd-001, 'jd')"]
        J4["Junction 4: (Screening B, cv-102, 'resume')"]
    end

    subgraph Screenings ["screenings Table"]
        SA["Screening A<br/>Tarun vs Voice L3 (Score: 85)"]
        SB["Screening B<br/>Prachi vs Voice L3 (Score: 92)"]
    end

    JD1 --> J1
    CV1 --> J2
    JD1 --> J3
    CV2 --> J4

    J1 --> SA
    J2 --> SA
    J3 --> SB
    J4 --> SB
```

### Key Architectural Benefits
- **Zero Storage Bloat**: `Voice_L3_Requisition.docx` is stored once on disk. Both Screening A and Screening B link to the identical `file_id`.
- **Bidirectional Traceability**:
  - From a candidate screening, you can immediately retrieve the exact source JD and resume bytes (`registry.get_screening_files(screening_id)`).
  - From a stored JD file, you can immediately list every candidate ever evaluated against that exact document version.
- **Resilient File Deletion**: If a single screening is deleted, the master JD file remains safely available for other candidates.
