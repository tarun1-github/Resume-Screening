# 🧪 Practical Engineering Exercises & Labs — FITMENT.AI

> **Audience**: Trainee Developers, Systems Engineers, and Architecture Evaluators.  
> **Last Reviewed**: 2026-10-19  

These hands-on exercises are designed to build practical mastery of the FITMENT.AI architecture. Each lab includes a clear objective, step-by-step instructions, and verification checks.

---

## Lab 1: Adding a New Skill Category to the Deterministic Engine

### Objective
Extend [`deterministic_engine.py`](file:///e:/Projects/resume-screening-agent/deterministic_engine.py) to recognize modern Cloud Native and Observability competencies, and verify via automated unit tests.

### Steps
1. Open [`deterministic_engine.py`](file:///e:/Projects/resume-screening-agent/deterministic_engine.py).
2. Locate the skill token dictionary definition. Add new competencies:
   - `OpenTelemetry`, `Prometheus`, `Grafana`, `ArgoCD`, `Helm`.
3. Open [`tests/test_deterministic_engine.py`](file:///e:/Projects/resume-screening-agent/tests/test_deterministic_engine.py).
4. Create a new test case `test_cloud_native_skill_matching()`:
   ```python
   def test_cloud_native_skill_matching(self):
       jd = "Looking for a DevOps Lead with Prometheus, Grafana, and ArgoCD experience."
       cv = "Senior SRE with extensive background in Prometheus monitoring and ArgoCD GitOps pipelines."
       result = evaluate_candidate_deterministically(jd, cv)
       self.assertIn("Prometheus", result["skills_matched"])
       self.assertIn("ArgoCD", result["skills_matched"])
       self.assertIn("Grafana", result["missing_skills"])
   ```
5. Run the test:
   ```powershell
   python -m unittest tests/test_deterministic_engine.py
   ```

---

## Lab 2: Simulating a Cloud LLM Provider Outage

### Objective
Verify that FITMENT.AI degrades gracefully to offline screening without throwing exceptions when the cloud AI provider times out.

### Steps
1. In your local `.env`, change `GEMINI_API_KEY` to an invalid string:
   ```ini
   GEMINI_API_KEY=invalid_dummy_token_12345
   ```
2. Launch the Streamlit application:
   ```powershell
   streamlit run app.py
   ```
3. Open the sidebar Settings and observe the health validation probe.
   - *Expected Result*: Renders `⚡ InstantFit Offline Screening Active`.
4. Upload a JD and resume and click `"🚀 Run InstantFit AI Screening"`.
   - *Expected Result*: The scorecard renders cleanly with mathematical scores (e.g. 85/100), verified evidence pills, and targeted interview probes. No Python traceback occurs.

---

## Lab 3: Safe Database Schema Extension

### Objective
Add a new column `linkedin_url` to the `candidates` table in [`registry.py`](file:///e:/Projects/resume-screening-agent/registry.py) using an idempotent migration that preserves existing candidate records in `data/fitment.db`.

### Steps
1. Open [`registry.py`](file:///e:/Projects/resume-screening-agent/registry.py).
2. In `init_db()`, add the column to the `CREATE TABLE IF NOT EXISTS candidates` statement:
   ```sql
   linkedin_url TEXT DEFAULT '',
   ```
3. In the schema migration section of `init_db()`, add an idempotent check:
   ```python
   cursor.execute("PRAGMA table_info(candidates);")
   cand_cols = {r["name"] for r in cursor.fetchall()}
   if "linkedin_url" not in cand_cols:
       cursor.execute("ALTER TABLE candidates ADD COLUMN linkedin_url TEXT DEFAULT '';")
   ```
4. Run `init_db()` and verify via SQLite CLI:
   ```powershell
   python -c "import registry; registry.init_db()"
   ```
5. Confirm that existing candidate records are untouched and all 155 unit tests pass:
   ```powershell
   python -m unittest discover tests
   ```

---

## Lab 4: Testing Path Traversal Defenses

### Objective
Verify that [`storage.py`](file:///e:/Projects/resume-screening-agent/storage.py) rejects any target path that attempts to escape the configured `data/` directory.

### Steps
1. Create a quick test script in `scratch/test_traversal.py`:
   ```python
   import storage
   try:
       storage.resolve_stored_path("../../Windows/System32/calc.exe", base_dir="./data")
       print("FAIL: Security breach permitted traversal!")
   except PermissionError as e:
       print("PASS: Traversal blocked successfully:", e)
   ```
2. Run the script:
   ```powershell
   python scratch/test_traversal.py
   ```
3. Confirm that `PermissionError` is raised with an explicit security alert.
