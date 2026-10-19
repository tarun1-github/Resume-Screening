# 📚 FITMENT.AI Technical Knowledge Base & Documentation Vault

Welcome to the comprehensive engineering knowledge base for the **FITMENT.AI Recruitment Intelligence Platform**.

This documentation suite serves as the authoritative, long-term technical reference for software engineers, solution architects, AI practitioners, systems operators, and talent acquisition leaders.

---

## 🗺️ Master Documentation Directory

### 1. High-Level & Architecture Overview (Root Docs)
- [**Root README**](file:///e:/Projects/resume-screening-agent/README.md) — Quickstart, system summary, core features, and setup.
- [**ARCHITECTURE.md**](file:///e:/Projects/resume-screening-agent/ARCHITECTURE.md) — Executive solution architecture and high-level interaction models.
- [**APPLICATION_ARCHITECTURE.md**](file:///e:/Projects/resume-screening-agent/APPLICATION_ARCHITECTURE.md) — Deep-dive into application tiers, components, and data contracts.
- [**AI_ARCHITECTURE.md**](file:///e:/Projects/resume-screening-agent/AI_ARCHITECTURE.md) — Deterministic vs. GenAI vs. Agentic AI classification and multi-provider gateway.
- [**DATA_ARCHITECTURE.md**](file:///e:/Projects/resume-screening-agent/DATA_ARCHITECTURE.md) — Relational schema, SQLite ER model, durable file storage, and IST timezone architecture.
- [**SECURITY.md**](file:///e:/Projects/resume-screening-agent/SECURITY.md) — Secrets management, PII protections, and security threat models.
- [**CONTRIBUTING.md**](file:///e:/Projects/resume-screening-agent/CONTRIBUTING.md) — Contribution standards, coding conventions, and pre-commit checklists.
- [**CHANGELOG.md**](file:///e:/Projects/resume-screening-agent/CHANGELOG.md) — Release notes and version history.

---

### 2. Architecture Knowledge Deep-Dive (`docs/architecture/`)
- [**System Context**](file:///e:/Projects/resume-screening-agent/docs/architecture/system-context.md) — Stakeholders, system boundaries, and external touchpoints.
- [**Application Components**](file:///e:/Projects/resume-screening-agent/docs/architecture/application-components.md) — Responsibilities, interfaces, and dependencies of all Python modules.
- [**Data Flow**](file:///e:/Projects/resume-screening-agent/docs/architecture/data-flow.md) — Step-by-step data transformation pipelines from ingestion to persistence.
- [**Sequence Diagrams**](file:///e:/Projects/resume-screening-agent/docs/architecture/sequence-diagrams.md) — 10 end-to-end Mermaid sequence diagrams for all core user workflows.
- [**State Management**](file:///e:/Projects/resume-screening-agent/docs/architecture/state-management.md) — Streamlit session state lifecycle, pending navigation, and widget safety.
- [**Error Handling & Fault Tolerance**](file:///e:/Projects/resume-screening-agent/docs/architecture/error-handling.md) — Resilience patterns, timeout budgets, and graceful fallbacks.
- [**Deployment Architecture**](file:///e:/Projects/resume-screening-agent/docs/architecture/deployment-architecture.md) — Local development, host/port network configuration, and server daemon processes.
- [**Architecture Decision Records (ADR)**](file:///e:/Projects/resume-screening-agent/docs/architecture/architecture-decisions.md) — 8 key architectural decisions, rationale, alternatives, and tradeoffs.

---

### 3. AI Ecosystem & Evaluation (`docs/ai/`)
- [**AI Ecosystem**](file:///e:/Projects/resume-screening-agent/docs/ai/ai-ecosystem.md) — Comprehensive view of AI capabilities across deterministic, generative, and conversational layers.
- [**Deterministic vs. Generative AI**](file:///e:/Projects/resume-screening-agent/docs/ai/deterministic-vs-genai.md) — Separation of zero-hallucination math from qualitative narrative synthesis.
- [**Chatbot Modes (A vs. B)**](file:///e:/Projects/resume-screening-agent/docs/ai/chatbot-modes.md) — Database-grounded candidate intelligence (Mode A) vs. general technical assistant (Mode B).
- [**Grounding and Retrieval**](file:///e:/Projects/resume-screening-agent/docs/ai/grounding-and-retrieval.md) — Exact SQL retrieval mechanics vs. vector RAG comparison.
- [**Provider Integration**](file:///e:/Projects/resume-screening-agent/docs/ai/provider-integration.md) — Configuration, health validation, and multi-provider failover (Gemini, OpenRouter, NVIDIA, Groq).
- [**Agentic AI Assessment**](file:///e:/Projects/resume-screening-agent/docs/ai/agentic-ai-assessment.md) — Implemented agentic behaviors vs. future autonomous roadmap.
- [**AI Evaluation & Guardrails**](file:///e:/Projects/resume-screening-agent/docs/ai/ai-evaluation.md) — Hallucination risks, prompt injection defenses, secret leakage barriers, and audit results.

---

### 4. Data Architecture & Security (`docs/data-and-security/`)
- [**Database Schema Reference**](file:///e:/Projects/resume-screening-agent/docs/data-and-security/database-schema.md) — Full specification of all 7 SQLite tables, columns, indexes, and foreign keys.
- [**Entity Relationships**](file:///e:/Projects/resume-screening-agent/docs/data-and-security/entity-relationships.md) — Visual ER diagrams, cardinalities, and many-to-many junction table design.
- [**Data Lifecycle**](file:///e:/Projects/resume-screening-agent/docs/data-and-security/data-lifecycle.md) — Creation, modification, persistence, retention, and deletion flows.
- [**Privacy & Threat Model**](file:///e:/Projects/resume-screening-agent/docs/data-and-security/privacy-and-threat-model.md) — STRIDE threat analysis, PII mitigation, and path traversal protection.
- [**Secrets & Configuration**](file:///e:/Projects/resume-screening-agent/docs/data-and-security/secrets-and-configuration.md) — Environment variables, session state memory governance, and zero-leakage guarantees.

---

### 5. Learning & Knowledge Transfer (`docs/learning/`)
- [**Knowledge Map**](file:///e:/Projects/resume-screening-agent/docs/learning/KNOWLEDGE_MAP.md) — Guided learning curricula for Beginners, Developers, and Solution Architects.
- [**Mental Models**](file:///e:/Projects/resume-screening-agent/docs/learning/MENTAL_MODELS.md) — 7 progressively deeper mental models (from 30-second summary to deep security architecture).
- [**End-to-End Walkthrough**](file:///e:/Projects/resume-screening-agent/docs/learning/END_TO_END_WALKTHROUGH.md) — Step-by-step trace of a complete recruitment screening and decision cycle.
- [**Codebase Tour**](file:///e:/Projects/resume-screening-agent/docs/learning/CODEBASE_TOUR.md) — Architectural file tree, execution pathways, and code navigation guide.
- [**Glossary**](file:///e:/Projects/resume-screening-agent/docs/learning/GLOSSARY.md) — Authoritative dictionary of recruitment and AI engineering terms.
- [**Architecture Q&A**](file:///e:/Projects/resume-screening-agent/docs/learning/ARCHITECTURE_QA.md) — Technical review questions, interview prompts, and model answers.
- [**Hands-On Exercises**](file:///e:/Projects/resume-screening-agent/docs/learning/EXERCISES.md) — Practical code exercises, diagnostic scenarios, and extension challenges.

---

### 6. Operations & Runbooks (`docs/operations/`)
- [**Setup & Installation**](file:///e:/Projects/resume-screening-agent/docs/operations/setup-and-installation.md) — Clean environment installation, dependencies, and verification.
- [**Configuration Reference**](file:///e:/Projects/resume-screening-agent/docs/operations/configuration-reference.md) — Complete inventory of environment variables and UI settings.
- [**Testing Guide**](file:///e:/Projects/resume-screening-agent/docs/operations/testing-guide.md) — Running unit test suites, writing regressions, and coverage reports.
- [**Troubleshooting & Runbook**](file:///e:/Projects/resume-screening-agent/docs/operations/troubleshooting.md) — Diagnostic guides for common errors, widget states, and provider timeouts.
- [**Backup & Recovery**](file:///e:/Projects/resume-screening-agent/docs/operations/backup-and-recovery.md) — Hot database snapshotting, file restore, and disaster recovery procedures.
- [**Release & GitHub Workflow**](file:///e:/Projects/resume-screening-agent/docs/operations/release-and-github-workflow.md) — Branch governance, pre-commit checklists, and sanitized release protocol.
