"""
FITMENT.AI - Fitment Assistant Chatbot Engine
Portal-Wide Recruitment Intelligence Assistant.
Database-grounded conversational assistant querying all candidates and screening records in SQLite.
Supports candidate resolution, multi-screening history, status management, follow-ups,
and resilient offline/LLM qualitative insights.
"""

from __future__ import annotations

import json
import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import registry
import llm_manager

NOT_FOUND_MESSAGE = (
    "I couldn't find a matching candidate in the screened candidate records. "
    "Please check the name or screen the candidate first."
)

STOP_WORDS_FOR_NAMES = {
    "the", "for", "and", "about", "with", "from", "role", "voice", "cisco",
    "engineer", "network", "screening", "screened", "status", "score", "scores",
    "mobile", "phone", "number", "email", "job", "jobs", "candidate", "candidates",
    "recruitment", "interview", "questions", "interviews", "follow", "followup",
    "follow-up", "today", "tomorrow", "yesterday", "overdue", "rejected", "shortlisted",
    "review", "hold", "please", "check", "what", "which", "where", "when", "show",
    "find", "give", "tell", "current", "latest", "previous", "history", "all",
    "experience", "total", "relevant", "skills", "skill", "missing", "matched",
    "fitment", "dossier", "profile", "details", "contact", "organization", "company",
    "designation", "analyst", "consultant", "architect", "lead", "senior", "junior",
    "who", "why", "how", "can", "you", "does", "work", "scored", "scores",
    "flow", "call", "calls", "sip", "mgcp", "cucm", "voip", "routing", "trunk",
    "gateway", "setup", "telephony", "protocol", "packet", "script", "python",
    "powershell", "decorator", "decorators", "rag", "agent", "agents", "code",
    "email", "plan", "summary", "concept", "troubleshoot", "troubleshooting",
    "explain", "draft", "write", "compare", "between", "difference",
}


def extract_explicit_candidate_search_terms(query: str) -> List[str]:
    """
    Extracts potential candidate names or identifiers explicitly present in the query.
    Detects possessive forms, prepositional phrases, and ID patterns.
    """
    terms: List[str] = []

    # 1. Candidate ID / Screening ID pattern (e.g. 'candidate cid-123', 'id: scr-abc')
    id_patterns = [
        r"\b(?:candidate\s+id|candidate|id|ref|reference|screening\s+id|screening)\s*[:#]?\s*([a-zA-Z0-9_\-]+)\b",
    ]
    for pat in id_patterns:
        m = re.search(pat, query, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            if val.lower() not in STOP_WORDS_FOR_NAMES and len(val) >= 3:
                terms.append(val)

    # 2. Possessive name (e.g. "Tarun's", "Prachi’s", "Shubhangi's", "Alex's")
    possessive = re.findall(r"\b([A-Za-z]{3,})(?:'s|’s)\b", query)
    for name in possessive:
        if name.lower() not in STOP_WORDS_FOR_NAMES:
            terms.append(name)

    # 3. Prepositional phrases (e.g. "of Tarun", "for Shubhangi", "about Prachi", "of Alex")
    prep_patterns = [
        r"\b(?:of|for|about|named|regarding)\s+([A-Za-z]{3,}(?:\s+[A-Za-z]{3,})?)\b",
        r"\b(?:check|inspect|verify|view)\s+([A-Za-z]{3,}(?:\s+[A-Za-z]{3,})?)\b",
        r"\b(?:call|contact)\s+(?:candidate\s+)?([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})?)\b",
    ]
    for pat in prep_patterns:
        for match in re.findall(pat, query, re.IGNORECASE):
            parts = match.strip().split()
            valid_parts = [p for p in parts if p.lower() not in STOP_WORDS_FOR_NAMES]
            if valid_parts:
                terms.append(" ".join(valid_parts))

    # 4. Action phrases (e.g. "Change Tarun's status", "Mark Shubhangi as Shortlisted")
    action_patterns = [
        r"\b(?:change|update|mark|set|move|transition)\s+([A-Za-z]{3,}(?:\s+[A-Za-z]{3,})?)\b",
    ]
    for pat in action_patterns:
        for match in re.findall(pat, query, re.IGNORECASE):
            parts = match.strip().split()
            valid_parts = [p for p in parts if p.lower() not in STOP_WORDS_FOR_NAMES]
            if valid_parts:
                terms.append(" ".join(valid_parts))

    # Remove duplicates preserving order
    seen = set()
    cleaned_terms = []
    for t in terms:
        t_clean = t.strip()
        if t_clean and t_clean.lower() not in seen and t_clean.lower() not in STOP_WORDS_FOR_NAMES:
            seen.add(t_clean.lower())
            cleaned_terms.append(t_clean)
    return cleaned_terms


def find_matching_candidates_in_db(query: str, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Matches candidate records in the SQLite database against the text query.
    Checks full name, partial name, and individual non-stop name tokens with word boundaries.
    """
    q_lower = query.lower()
    with registry.get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM candidates")
        all_cands = [dict(r) for r in cursor.fetchall()]

    if not all_cands:
        return []

    # 1. Exact full name match
    full_matches = [c for c in all_cands if c["name"].lower() in q_lower]
    if full_matches:
        return full_matches

    # 2. Token match: check if any distinctive word in candidate name (>= 3 chars) is in query
    token_matches = []
    for cand in all_cands:
        parts = cand["name"].split()
        for p in parts:
            p_clean = p.strip().lower()
            if len(p_clean) >= 3 and p_clean not in STOP_WORDS_FOR_NAMES:
                if re.search(rf"\b{re.escape(p_clean)}\b", q_lower):
                    if cand not in token_matches:
                        token_matches.append(cand)
                    break
    return token_matches


def resolve_candidate_for_query(
    user_query: str,
    selected_candidate_id: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[str], List[Dict[str, Any]]]:
    """
    Strict context-aware candidate resolution adhering to Context Precedence:
    1. Explicit candidate name in latest message.
    2. Explicit candidate ID or screening reference.
    3. Selected candidate in current conversation ONLY when latest question clearly refers to it (pronoun / implicit context).
    4. Ambiguity / not-found handling. Never silently substitutes another candidate.

    Returns: (resolved_candidate, error_message, disambiguation_candidates)
    """
    q_lower = user_query.lower()

    # Step 1: Check if an explicit candidate name or token was extracted
    explicit_terms = extract_explicit_candidate_search_terms(user_query)

    # Step 2: Check matching candidates in DB
    db_matches = find_matching_candidates_in_db(user_query, db_path)

    # CASE A: Candidate explicitly matched in DB
    if db_matches:
        if len(db_matches) == 1:
            return db_matches[0], None, []
        else:
            return None, None, db_matches

    # CASE B: Candidate name was explicitly mentioned in the query (via syntax/patterns),
    # but 0 matching candidates were found in the database!
    if explicit_terms:
        for term in explicit_terms:
            search_res = registry.get_candidate_by_name_or_query(term, db_path)
            if len(search_res) == 1:
                return search_res[0], None, []
            elif len(search_res) > 1:
                return None, None, search_res

        # An explicit candidate name was mentioned, but not found in the DB!
        # Do NOT fall back to selected_candidate_id!
        return None, NOT_FOUND_MESSAGE, []

    # CASE C: No explicit candidate was named in the query.
    # Check for pronoun or contextual reference to the selected candidate.
    context_cues = ["he", "she", "her", "his", "him", "they", "them", "the candidate", "this candidate", "selected candidate", "current candidate", "this profile"]
    has_context_cue = any(re.search(rf"\b{re.escape(cue)}\b", q_lower) for cue in context_cues)

    # General technical terms that indicate Mode B unless a candidate is explicitly referenced
    general_tech_terms = [
        "explain", "how to", "what is", "difference between", "help write",
        "script", "decorators", "rag", "ai agents", "sip", "cucm", "mgcp",
        "powershell", "python", "email", "interview plan", "architecture",
        "summarize", "guide", "tutorial"
    ]
    is_general_inquiry = any(re.search(rf"\b{re.escape(term)}\b", q_lower) for term in general_tech_terms)

    cand_attribute_cues = ["score", "fitment", "mobile", "phone", "contact", "email", "status", "gaps", "skills", "experience", "designation", "resume", "cv", "profile", "interview questions", "probes"]
    has_attribute_cue = any(re.search(rf"\b{re.escape(cue)}\b", q_lower) for cue in cand_attribute_cues)

    if selected_candidate_id and (has_context_cue or (has_attribute_cue and not is_general_inquiry)):
        cand = registry.get_candidate_by_id(selected_candidate_id, db_path)
        if cand:
            return cand, None, []

    # If only 1 candidate exists in the entire database and user asked a single-candidate question
    with registry.get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM candidates")
        all_cands = [dict(r) for r in cursor.fetchall()]

    if len(all_cands) == 1 and (has_context_cue or (has_attribute_cue and not is_general_inquiry)):
        return all_cands[0], None, []

    return None, None, []


def resolve_status_from_text(text: str) -> Optional[str]:
    """Resolves natural language status mention to canonical CANDIDATE_STATUSES string."""
    t_lower = text.lower()
    for stat in registry.CANDIDATE_STATUSES:
        if stat.lower() in t_lower:
            return stat

    synonym_map = [
        ("awaiting recruiter review", "Recruiter Review"),
        ("awaiting review", "Recruiter Review"),
        ("under review", "Recruiter Review"),
        ("recruiter review", "Recruiter Review"),
        ("scheduled for interviews", "Interview Scheduled"),
        ("scheduled for interview", "Interview Scheduled"),
        ("interview scheduled", "Interview Scheduled"),
        ("interviews scheduled", "Interview Scheduled"),
        ("interview completed", "Interview Completed"),
        ("completed interview", "Interview Completed"),
        ("interview done", "Interview Completed"),
        ("shortlisted", "Shortlisted"),
        ("shortlist", "Shortlisted"),
        ("on hold", "On Hold"),
        ("put on hold", "On Hold"),
        ("offer released", "Offer Released"),
        ("released offer", "Offer Released"),
        ("selected", "Selected"),
        ("joined", "Joined"),
        ("rejected", "Rejected"),
        ("screened", "Screened"),
        ("new", "New"),
    ]
    for pattern, canonical in synonym_map:
        if pattern in t_lower:
            return canonical
    return None


def format_candidate_profile(cand: Dict[str, Any], latest_screening: Optional[Dict[str, Any]] = None) -> str:
    """Standardized Candidate Profile output adhering strictly to Section 8."""
    name = cand.get("name", "Unknown")
    desig = cand.get("current_designation") or "Not Detected"
    org = cand.get("current_organization") or "Not Detected"
    mobile = cand.get("mobile") or "Not available in CV"
    email = cand.get("email") or "Not Specified"
    total_exp = cand.get("total_experience") or "Not Detected"

    if latest_screening:
        score_val = f"{latest_screening.get('deterministic_score', 'N/A')}/100 ({latest_screening.get('job_title', 'Target Role')})"
    else:
        score_val = "Not yet screened"

    status = cand.get("current_status", "Screened")
    last_screened = (
        latest_screening.get("screening_timestamp")
        if latest_screening
        else (cand.get("updated_at") or cand.get("created_at") or "N/A")
    )

    return (
        f"**🎯 Candidate Profile — {name}**\n\n"
        f"- Current designation: {desig}\n"
        f"- Current organization: {org}\n"
        f"- Mobile number: {mobile}\n"
        f"- Email: {email}\n"
        f"- Total experience: {total_exp}\n"
        f"- Latest screening score: {score_val}\n"
        f"- Recruitment status: {status}\n"
        f"- Last screened: {last_screened}"
    )


class FitmentAssistant:
    """
    Authoritative, portal-wide database-grounded recruitment intelligence assistant.
    Queries all candidate records, screenings, and follow-ups in the FITMENT.AI registry.
    Supports general-purpose AI copilot queries (Mode B) routed to configured LLMs.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        preferred_provider: Optional[str] = None,
        preferred_model: Optional[str] = None,
    ):
        self.db_path = db_path
        self.preferred_provider = preferred_provider
        self.preferred_model = preferred_model
        registry.init_db(self.db_path)

    def get_registered_candidate_names(self) -> List[str]:
        with registry.get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM candidates ORDER BY updated_at DESC")
            return [r["name"] for r in cursor.fetchall()]

    def ask(
        self,
        user_query: str,
        selected_candidate_id: Optional[str] = None,
        preferred_provider: Optional[str] = None,
        preferred_model: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Parses intent, resolves candidate across complete registry, and returns structured responses.
        Mode A: Grounded recruitment intelligence (candidates, scores, follow-ups, comparisons).
        Mode B: General-purpose AI copilot (technical concepts, code, interview plans, email drafting).
        """
        q = user_query.strip()
        q_lower = q.lower()
        active_p = preferred_provider or self.preferred_provider
        active_m = preferred_model or self.preferred_model

        # 0. SECURITY & SECRETS PROTECTION
        secrets_pattern = r"\b(?:api[_\s-]?keys?|secrets?|environment\s+variables?|env\s+vars?|database_url|passwords?)\b"
        if re.search(r"\b(?:show|reveal|display|print|expose|leak|dump|view|give|tell)\b", q_lower) and re.search(secrets_pattern, q_lower):
            return {
                "answer": (
                    "🔒 **Security Protection Notice:** System environment variables, API credentials, and internal secret tokens "
                    "are strictly protected and cannot be displayed or exposed under any circumstances."
                ),
                "needs_disambiguation": False,
            }

        # ----------------------------------------------------------------------
        # 1. CANDIDATE STATUS UPDATE / TRANSITION INTENT
        # e.g., "Change Tarun's status to Shortlisted"
        # ----------------------------------------------------------------------
        action_verbs = ["change", "update", "mark", "set", "move", "transition", "switch"]
        has_action_verb = any(re.search(rf"\b{verb}\b", q_lower) for verb in action_verbs)
        target_status = resolve_status_from_text(q_lower)

        if has_action_verb and (target_status or "status" in q_lower):
            cand, err, disambig = resolve_candidate_for_query(q, selected_candidate_id, self.db_path)
            if err:
                return {"answer": err, "needs_disambiguation": False}
            if disambig:
                opts = [f"- **{m['name']}** (ID: `{m['candidate_id']}`, Email: `{m.get('email')}`, Role: `{m.get('current_designation')}`)" for m in disambig]
                return {
                    "answer": f"⚠️ Multiple candidates match your status update request. Please specify which candidate:\n\n" + "\n".join(opts),
                    "needs_disambiguation": True,
                    "candidates": disambig,
                }
            if not cand:
                return {
                    "answer": "⚠️ Please specify which candidate's status you would like to update (e.g., *Change Shubhangi's status to Shortlisted*).",
                    "needs_disambiguation": False,
                }
            if not target_status:
                valid_list = ", ".join([f"`{s}`" for s in registry.CANDIDATE_STATUSES])
                return {
                    "answer": f"⚠️ Please specify a valid recruitment status for **{cand['name']}**.\n\nValid options: {valid_list}",
                    "candidate_id": cand["candidate_id"],
                    "needs_disambiguation": False,
                }

            prev_status = cand.get("current_status", "Screened")
            ok = registry.update_candidate_status(
                candidate_id=cand["candidate_id"],
                new_status=target_status,
                notes="Updated via Fitment Assistant",
                changed_by="Fitment Assistant",
                db_path=self.db_path,
            )
            if ok:
                screenings = registry.get_candidate_screenings(cand["candidate_id"], self.db_path)
                score_str = f"**{screenings[0]['deterministic_score']}/100**" if screenings else "*Not Screened*"
                return {
                    "answer": (
                        f"✅ Candidate status updated to **{target_status}**.\n\n"
                        f"- **Candidate:** **{cand['name']}**\n"
                        f"- **Screening Reference:** `{cand['candidate_id']}`\n"
                        f"- **Previous Status:** `{prev_status}`\n"
                        f"- **New Recruitment Status:** `{target_status}`\n"
                        f"- **Fitment Score:** {score_str} *(Preserved & Unaltered)*\n\n"
                        f"The transition has been permanently recorded in the Candidate Records audit timeline."
                    ),
                    "candidate_id": cand["candidate_id"],
                    "needs_disambiguation": False,
                }
            else:
                return {
                    "answer": f"❌ Could not update status for **{cand['name']}**. Please verify candidate record.",
                    "candidate_id": cand["candidate_id"],
                    "needs_disambiguation": False,
                }

        # ----------------------------------------------------------------------
        # 2. GLOBAL PORTAL & MULTI-CANDIDATE QUERIES (Evaluated when query is broad)
        # ----------------------------------------------------------------------

        # 2A: Follow-ups due / pending / overdue / tomorrow / Bharat's list
        if any(w in q_lower for w in ["follow-up", "follow up", "followups", "follow-ups", "due today", "overdue", "tomorrow", "followup list", "follow-up list"]) or ("bharat" in q_lower and "list" in q_lower):
            overview = registry.get_follow_ups_overview(self.db_path)
            due_today = overview["due_today"]
            overdue = overview["overdue"]
            upcoming = overview["upcoming"]

            header_title = "### 📅 Recruiter Bharat Raparthy — Candidate Follow-Up Pipeline\n" if "bharat" in q_lower else "### 📅 Candidate Follow-Up Status\n"

            if "tomorrow" in q_lower:
                tomorrow_str = (date.today() + timedelta(days=1)).isoformat()
                tomorrow_fus = [u for u in upcoming if u.get("follow_up_date") == tomorrow_str]
                if not tomorrow_fus:
                    return {"answer": "ℹ️ No candidate follow-ups currently scheduled for tomorrow.", "needs_disambiguation": False}
                ans_lines = [f"### 📅 Follow-Ups Scheduled for Tomorrow ({tomorrow_str})\n"]
                for f in tomorrow_fus:
                    ans_lines.append(f"- **{f['candidate_name']}** (Role: {f.get('current_designation', 'N/A')}) — Note: *{f.get('notes') or 'Follow-up'}*")
                return {"answer": "\n".join(ans_lines), "needs_disambiguation": False}

            ans_lines = [header_title]
            if overdue:
                ans_lines.append(f"**⚠️ Overdue Follow-ups ({len(overdue)}):**")
                for f in overdue:
                    ans_lines.append(f"- **{f['candidate_name']}** (Due: `{f['follow_up_date']}`) — Role: {f.get('current_designation', 'N/A')} | Note: *{f.get('notes') or 'Pending outreach'}*")
                ans_lines.append("")

            if due_today:
                ans_lines.append(f"**⚡ Follow-ups Due Today ({len(due_today)}):**")
                for f in due_today:
                    ans_lines.append(f"- **{f['candidate_name']}** (Role: {f.get('current_designation', 'N/A')}) — Note: *{f.get('notes') or 'Routine follow-up'}*")
                ans_lines.append("")
            elif not overdue:
                ans_lines.append("✅ **No follow-ups due today.**\n")

            if upcoming:
                ans_lines.append(f"**🗓️ Upcoming Follow-ups ({len(upcoming)}):**")
                for f in upcoming[:5]:
                    ans_lines.append(f"- **{f['candidate_name']}** on `{f['follow_up_date']}`")

            return {"answer": "\n".join(ans_lines).strip(), "needs_disambiguation": False}

        # 2A.1: Candidates with specific skill / company / technology experience
        # e.g., "Find candidates with Cisco experience", "Candidates with Python experience"
        exp_match = re.search(r'(?:find|show|list|search|which|get)\s+candidates\s+(?:with|having)\s+([a-zA-Z0-9_\-+#. ]+?)\s+(?:experience|skills|background)', q_lower)
        if not exp_match:
            exp_match = re.search(r'candidates\s+(?:with|having)\s+([a-zA-Z0-9_\-+#. ]+?)\s+experience', q_lower)
        if exp_match:
            exp_term = exp_match.group(1).strip()
            cands = registry.search_candidates_portal_wide(query_term=exp_term, db_path=self.db_path)
            if not cands:
                return {
                    "answer": f"ℹ️ No candidates found in the registry with **{exp_term}** experience.",
                    "needs_disambiguation": False,
                }
            ans_lines = [f"### 💼 Candidates with `{exp_term.title()}` Experience ({len(cands)})\n"]
            for c in cands:
                score_str = f"Score: **{c['deterministic_score']}/100**" if c.get("deterministic_score") is not None else "Not yet screened"
                role_str = c.get("job_title") or c.get("current_designation") or "N/A"
                org_str = c.get("current_organization") or "Not Specified"
                ans_lines.append(f"- **{c['name']}** — {role_str} (*{org_str}*) | {score_str} | Status: `{c.get('current_status', 'Screened')}`")
            return {"answer": "\n".join(ans_lines), "needs_disambiguation": False}

        # 2A.2: Candidate Comparison
        # e.g. "Compare two candidates for Voice T2", "Compare Tarun and Shubhangi"
        if "compare" in q_lower:
            role_cmp = re.search(r'compare\s+(?:two\s+)?candidates\s+for\s+([^?.,]+)', q, re.IGNORECASE)
            if role_cmp:
                r_target = role_cmp.group(1).strip()
                cands = registry.get_candidates_screened_for_role(r_target, self.db_path)
                if len(cands) >= 2:
                    display_role = cands[0].get("job_title") or r_target
                    ans_lines = [
                        f"### ⚖️ Candidate Comparison for `{display_role}`\n",
                        "| Candidate Name | Score | Verdict | Status | Experience | Current Org |",
                        "|---|---|---|---|---|---|",
                    ]
                    for c in cands:
                        score_val = f"**{c.get('deterministic_score', 'N/A')}/100**"
                        ans_lines.append(
                            f"| **{c['name']}** | {score_val} | {c.get('verdict', 'N/A')} | `{c.get('current_status', 'Screened')}` | {c.get('total_experience', 'N/A')} | {c.get('current_organization', 'N/A')} |"
                        )
                    return {"answer": "\n".join(ans_lines), "needs_disambiguation": False}
                elif len(cands) == 1:
                    return {"answer": f"ℹ️ Only one candidate (**{cands[0]['name']}**) has been screened for `{r_target}` in the registry.", "needs_disambiguation": False}
                else:
                    return {"answer": f"ℹ️ No candidates have been screened for `{r_target}` in the registry.", "needs_disambiguation": False}

            # Check if 2 candidates are explicitly named
            all_c_names = self.get_registered_candidate_names()
            found_cands = [name for name in all_c_names if name.split()[0].lower() in q_lower]
            if len(found_cands) >= 2:
                c1 = registry.find_candidate_by_name(found_cands[0], self.db_path)
                c2 = registry.find_candidate_by_name(found_cands[1], self.db_path)
                if c1 and c2:
                    sc1 = registry.get_candidate_screenings(c1["candidate_id"], self.db_path)
                    sc2 = registry.get_candidate_screenings(c2["candidate_id"], self.db_path)
                    s1 = sc1[0] if sc1 else {}
                    s2 = sc2[0] if sc2 else {}
                    ans_lines = [
                        f"### ⚖️ Candidate Comparison: **{c1['name']}** vs **{c2['name']}**\n",
                        f"| Dimension | **{c1['name']}** | **{c2['name']}** |",
                        "|---|---|---|",
                        f"| **Current Designation** | {c1.get('current_designation', 'N/A')} | {c2.get('current_designation', 'N/A')} |",
                        f"| **Current Organization** | {c1.get('current_organization', 'N/A')} | {c2.get('current_organization', 'N/A')} |",
                        f"| **Total Experience** | {c1.get('total_experience', 'N/A')} | {c2.get('total_experience', 'N/A')} |",
                        f"| **Fitment Score** | **{s1.get('deterministic_score', 'N/A')}/100** | **{s2.get('deterministic_score', 'N/A')}/100** |",
                        f"| **Screening Verdict** | {s1.get('verdict', 'N/A')} | {s2.get('verdict', 'N/A')} |",
                        f"| **Recruitment Status** | `{c1.get('current_status', 'Screened')}` | `{c2.get('current_status', 'Screened')}` |",
                    ]
                    return {"answer": "\n".join(ans_lines), "needs_disambiguation": False}

        # 2B: Which candidates were screened for a specific role?
        # e.g., "Which candidates were screened for Voice T2?", "Who was screened for Cisco Network Voice"
        role_screened_match = re.search(r'(?:screened\s+for|candidates\s+for|for\s+the\s+role)\s+([^?.,]+)', q_lower)
        if role_screened_match and any(w in q_lower for w in ["which", "who", "show", "list", "candidates"]):
            raw_role = role_screened_match.group(1).strip()
            # Clean punctuation
            clean_role = re.sub(r'[\'"]', '', raw_role).strip()
            role_cands = registry.get_candidates_screened_for_role(clean_role, self.db_path)
            if not role_cands:
                return {
                    "answer": f"ℹ️ No candidates found who have been screened for **{clean_role}**.",
                    "needs_disambiguation": False,
                }
            ans_lines = [f"### 🎯 Candidates Screened for: `{clean_role}` ({len(role_cands)})\n"]
            for c in role_cands:
                score = c.get("deterministic_score", "N/A")
                verdict = c.get("verdict", "N/A")
                ts = c.get("screening_timestamp", "")[:10]
                ans_lines.append(f"- **{c['name']}** — Fitment Score: **{score}/100** ({verdict}) | Screened: `{ts}` | Status: `{c.get('current_status', 'Screened')}`")
            return {"answer": "\n".join(ans_lines), "needs_disambiguation": False}

        # 2C: Multi-Candidate by Specific Status (e.g. 'Show all shortlisted candidates', 'Show all candidates currently marked Rejected', 'Who is awaiting review?')
        if any(w in q_lower for w in ["show", "list", "which", "who", "find", "candidates", "awaiting"]) and target_status and target_status != "Screened":
            named_cand, _, _ = resolve_candidate_for_query(q, selected_candidate_id, self.db_path)
            if not named_cand:
                cands = registry.search_candidates_portal_wide(status_filter=target_status, db_path=self.db_path)
                if not cands:
                    return {"answer": f"ℹ️ No candidates currently in **{target_status}** status.", "needs_disambiguation": False}

                ans_lines = [f"### 📋 Candidates with status: `{target_status}` ({len(cands)})\n"]
                for c in cands:
                    score_str = f"Fitment: **{c['deterministic_score']}/100**" if c.get("deterministic_score") is not None else "Not yet screened"
                    role_str = c.get("job_title") or c.get("current_designation") or "N/A"
                    ans_lines.append(f"- **{c['name']}** | {role_str} | {score_str} | Mobile: `{c.get('mobile', 'Not available in CV')}`")
                return {"answer": "\n".join(ans_lines), "needs_disambiguation": False}

        # 2D: Show all screened candidates
        if any(phrase in q_lower for phrase in ["show all screened candidates", "show all candidates", "list all candidates", "all screened candidates", "screened candidate records", "browse candidates"]):
            all_records = registry.get_all_candidates_with_latest_screening(db_path=self.db_path)
            if not all_records:
                return {"answer": "ℹ️ No screened candidates currently in the FITMENT.AI registry.", "needs_disambiguation": False}
            ans_lines = [f"### 📋 All Screened Candidates in Registry ({len(all_records)})\n"]
            for c in all_records:
                score_str = f"**{c.get('deterministic_score')}/100**" if c.get("deterministic_score") is not None else "Not screened"
                role_str = c.get("job_title") or c.get("current_designation") or "N/A"
                ans_lines.append(f"- **{c['name']}** (ID: `{c['candidate_id']}`) — Role: {role_str} | Latest Score: {score_str} | Status: `{c.get('current_status', 'Screened')}`")
            return {"answer": "\n".join(ans_lines), "needs_disambiguation": False}

        # 2E: Screened status query specifically (when user asks for candidates with status 'screened')
        if any(w in q_lower for w in ["show", "list", "which", "who", "find"]) and target_status == "Screened" and "all screened" not in q_lower and "all candidates" not in q_lower:
            named_cand, _, _ = resolve_candidate_for_query(q, selected_candidate_id, self.db_path)
            if not named_cand:
                cands = registry.search_candidates_portal_wide(status_filter="Screened", db_path=self.db_path)
                if not cands:
                    return {"answer": "ℹ️ No candidates currently in **Screened** status.", "needs_disambiguation": False}
                ans_lines = [f"### 📋 Candidates with status: `Screened` ({len(cands)})\n"]
                for c in cands:
                    score_str = f"Fitment: **{c['deterministic_score']}/100**" if c.get("deterministic_score") is not None else "Not yet screened"
                    role_str = c.get("job_title") or c.get("current_designation") or "N/A"
                    ans_lines.append(f"- **{c['name']}** | {role_str} | {score_str} | Mobile: `{c.get('mobile', 'Not available in CV')}`")
                return {"answer": "\n".join(ans_lines), "needs_disambiguation": False}

        # 2F: Score threshold queries (e.g., 'scores above 70', 'fitment > 60')
        score_thresh_match = re.search(r'(?:above|greater\s+than|over|higher\s+than|>)\s*(\d{1,3})', q_lower)
        if score_thresh_match and any(w in q_lower for w in ["score", "fitment", "candidate", "which"]):
            threshold = int(score_thresh_match.group(1))
            cands = registry.search_candidates_portal_wide(min_score=threshold, db_path=self.db_path)
            if not cands:
                return {"answer": f"ℹ️ No candidates found with deterministic fitment score >= **{threshold}**.", "needs_disambiguation": False}
            ans_lines = [f"### 🎯 Candidates with Fitment Score ≥ {threshold} ({len(cands)})\n"]
            for c in cands:
                role_str = c.get("job_title") or c.get("current_designation") or "N/A"
                ans_lines.append(f"- **{c['name']}** — Score: **{c.get('deterministic_score')}/100** | Role: {role_str} | Status: `{c.get('current_status', 'Screened')}`")
            return {"answer": "\n".join(ans_lines), "needs_disambiguation": False}

        # ----------------------------------------------------------------------
        # 3. CANDIDATE-SPECIFIC QUERIES (Resolving strictly via Registry Precedence)
        # ----------------------------------------------------------------------
        cand_record, err_msg, disambig_list = resolve_candidate_for_query(q, selected_candidate_id, self.db_path)

        if err_msg:
            # Candidate explicitly queried but 0 matches found in the registry
            return {"answer": err_msg, "needs_disambiguation": False}

        if disambig_list:
            opts = [f"- **{m['name']}** (ID: `{m['candidate_id']}`, Email: `{m.get('email')}`, Role: `{m.get('current_designation')}`)" for m in disambig_list]
            return {
                "answer": f"⚠️ Multiple candidates match your query. Please specify which candidate you would like to inspect:\n\n" + "\n".join(opts),
                "needs_disambiguation": True,
                "candidates": disambig_list,
            }

        if not cand_record:
            # Check for Ambiguous query between candidate database and general technical guidance
            ambiguous_keywords = [
                "status", "check status", "score", "fitment score",
                "interview questions", "check candidate", "candidate details",
                "view profile", "check profile", "review candidate", "screening results"
            ]
            if q_lower in ambiguous_keywords or (len(q_lower.split()) <= 2 and any(k == q_lower for k in ambiguous_keywords)):
                return {
                    "answer": (
                        "🤔 **Clarification:** Would you like me to look up candidate screening records from the recruitment database, "
                        "or provide general technical guidance on this topic?\n\n"
                        "- **To inspect candidate records:** Mention the candidate's name (e.g. *What is Shubhangi's score?*) or select a candidate from the dashboard.\n"
                        "- **For general assistance:** Ask any technical question (e.g. *Explain SIP call flow* or *Explain Python decorators*)!"
                    ),
                    "needs_disambiguation": False,
                }

            # Mode B: General AI Assistant Query (Routed to configured LLM)
            gen_res = llm_manager.generate_general_assistant_response(
                user_query=q,
                conversation_history=conversation_history,
                preferred_provider=active_p,
                preferred_model=active_m,
            )
            if gen_res.get("status") == "success":
                return {
                    "answer": gen_res["text"],
                    "needs_disambiguation": False,
                    "provider": gen_res.get("provider"),
                    "model": gen_res.get("model"),
                }
            else:
                return {
                    "answer": gen_res.get("message") or (
                        "⚠️ The general AI assistant service is currently unavailable. "
                        "Please verify that an active AI provider (Gemini, OpenRouter, or NVIDIA NIM) "
                        "is configured and connected in Settings or `.env`."
                    ),
                    "needs_disambiguation": False,
                }

        cid = cand_record["candidate_id"]
        screenings = registry.get_candidate_screenings(cid, self.db_path)
        latest_screening = screenings[0] if screenings else None

        # 3A: Mobile Number / Contact / Phone
        if any(w in q_lower for w in ["mobile", "phone", "contact", "cell", "number"]):
            mob = cand_record.get("mobile") or "Not available in CV"
            return {
                "answer": f"📱 **{cand_record['name']}** — Contact Number:\n\n`{mob}`",
                "candidate_id": cid,
                "needs_disambiguation": False,
            }

        # 3B: Company / Current Organization / Employer
        if any(w in q_lower for w in ["company", "organization", "employer", "work for", "works for"]):
            org = cand_record.get("current_organization") or "Not Detected"
            desig = cand_record.get("current_designation") or "Not Detected"
            return {
                "answer": (
                    f"🏢 **{cand_record['name']} — Organization**\n\n"
                    f"- **Current Organization:** {org}\n"
                    f"- **Current Designation:** {desig}"
                ),
                "candidate_id": cid,
                "needs_disambiguation": False,
            }

        # 3C: Current Designation / Title / Role
        if any(w in q_lower for w in ["current designation", "designation", "title", "position"]) and not any(w in q_lower for w in ["all roles", "previous", "history"]):
            desig = cand_record.get("current_designation") or "Not Detected"
            org = cand_record.get("current_organization") or "Not Detected"
            latest_role = latest_screening.get("job_title", "N/A") if latest_screening else "N/A"
            return {
                "answer": (
                    f"💼 **{cand_record['name']}**\n\n"
                    f"- **Current Designation:** {desig}\n"
                    f"- **Current Organization:** {org}\n"
                    f"- **Latest Screening Role:** {latest_role}"
                ),
                "candidate_id": cid,
                "needs_disambiguation": False,
            }

        # 3D: Multiple Screenings / All Roles for Candidate
        # e.g., "Show all roles for which Shubhangi has been screened"
        if any(phrase in q_lower for phrase in ["all roles", "roles for which", "screened for which", "which roles", "screening history", "past screenings"]):
            if not screenings:
                return {
                    "answer": f"ℹ️ **{cand_record['name']}** has been registered but has not been screened for any roles yet.",
                    "candidate_id": cid,
                    "needs_disambiguation": False,
                }
            ans_lines = [f"📜 **Screening Records for {cand_record['name']} ({len(screenings)} total):**\n"]
            for s in screenings:
                ts = s["screening_timestamp"][:10]
                ans_lines.append(f"- **{s.get('job_title', 'Role')}** (Screened: `{ts}`) ➔ Score: **{s['deterministic_score']}/100** ({s['verdict']})")
            return {"answer": "\n".join(ans_lines), "candidate_id": cid, "needs_disambiguation": False}

        # 3E: Previous Job Score (Multiple screenings support)
        # e.g., "What was Prachi's score for the previous job?"
        if any(w in q_lower for w in ["previous job", "past job", "earlier job", "previous role", "earlier role"]):
            if len(screenings) >= 2:
                prev = screenings[1]
                return {
                    "answer": (
                        f"📜 **{cand_record['name']} — Previous Job Screening Score**\n\n"
                        f"- **Previous Job:** {prev.get('job_title', 'Role')}\n"
                        f"- **Score:** **{prev['deterministic_score']}/100**\n"
                        f"- **Verdict:** {prev['verdict']}\n"
                        f"- **Screening Date:** `{prev['screening_timestamp'][:10]}`\n\n"
                        f"*(Latest screening was for {latest_screening.get('job_title')} with score **{latest_screening['deterministic_score']}/100**)*"
                    ),
                    "candidate_id": cid,
                    "needs_disambiguation": False,
                }
            elif len(screenings) == 1:
                return {
                    "answer": (
                        f"ℹ️ **{cand_record['name']}** currently has only 1 recorded screening in the registry:\n\n"
                        f"- **Role:** {screenings[0].get('job_title', 'Role')}\n"
                        f"- **Score:** **{screenings[0]['deterministic_score']}/100** ({screenings[0]['verdict']})\n"
                        f"- **Date:** `{screenings[0]['screening_timestamp'][:10]}`"
                    ),
                    "candidate_id": cid,
                    "needs_disambiguation": False,
                }
            else:
                return {
                    "answer": f"ℹ️ **{cand_record['name']}** has not been screened for any roles yet.",
                    "candidate_id": cid,
                    "needs_disambiguation": False,
                }

        # 3F: Latest Fitment Score / Specific Job Score
        # e.g., "What is Tarun's latest fitment score?"
        if any(w in q_lower for w in ["score", "fitment score", "fitment", "rating", "verdict"]):
            if not latest_screening:
                return {
                    "answer": f"⚠️ **{cand_record['name']}** has been registered but has not been screened yet.",
                    "candidate_id": cid,
                    "needs_disambiguation": False,
                }
            score = latest_screening["deterministic_score"]
            verdict = latest_screening["verdict"]
            job_title = latest_screening.get("job_title", "Target Role")
            ts = latest_screening["screening_timestamp"][:10]

            # Qualitative explain query handling
            if any(w in q_lower for w in ["why", "explain", "reason"]):
                factual_ctx = (
                    f"Candidate Name: {cand_record['name']}\n"
                    f"Target Role: {job_title}\n"
                    f"Deterministic Score: {score}/100\n"
                    f"Verdict: {verdict}\n"
                    f"Recommendation: {latest_screening.get('recommendation', '')}\n"
                    f"Matched Skills: {latest_screening.get('matched_skills', '[]')}\n"
                    f"Missing Skills: {latest_screening.get('missing_skills', '[]')}\n"
                    f"Total Experience: {cand_record.get('total_experience', '')}\n"
                    f"Relevant Experience: {cand_record.get('relevant_experience', '')}\n"
                )
                llm_res = llm_manager.generate_qualitative_chat_response(
                    system_instruction="Explain the deterministic scoring breakdown clearly using only the provided facts.",
                    user_query=q,
                    factual_context=factual_ctx,
                )
                if llm_res.get("status") == "success" and llm_res.get("text"):
                    return {
                        "answer": f"🎯 **{cand_record['name']} — Fitment Analysis ({job_title})**\n\n{llm_res['text']}",
                        "candidate_id": cid,
                        "needs_disambiguation": False,
                    }

            return {
                "answer": (
                    f"🎯 **{cand_record['name']} — Latest Fitment Score**\n\n"
                    f"- **Target Role:** {job_title}\n"
                    f"- **Fitment Score:** **{score}/100**\n"
                    f"- **Verdict:** {verdict}\n"
                    f"- **Recommendation:** {latest_screening.get('recommendation', 'N/A')}\n"
                    f"- **Screening Date:** `{ts}`\n\n"
                    f"💡 *The score is deterministically calculated by analyzing technical keyword coverage, accreditations, and verified experience against {job_title}.*"
                ),
                "candidate_id": cid,
                "needs_disambiguation": False,
            }

        # 3G: Missing Skills / Gaps / Competencies
        if any(w in q_lower for w in ["missing", "gap", "lacking", "skill", "competency"]):
            if not latest_screening:
                return {
                    "answer": f"⚠️ No screening record available for **{cand_record['name']}**.",
                    "candidate_id": cid,
                    "needs_disambiguation": False,
                }
            try:
                missing = json.loads(latest_screening.get("missing_skills", "[]"))
                matched = json.loads(latest_screening.get("matched_skills", "[]"))
            except Exception:
                missing, matched = [], []

            missing_display = ", ".join(f"`{s}`" for s in missing[:15]) if missing else "None"
            matched_display = ", ".join(f"`{s}`" for s in matched[:15]) if matched else "None"

            return {
                "answer": (
                    f"🛠️ **{cand_record['name']} — Skill Alignment ({latest_screening.get('job_title', 'Target Role')})**\n\n"
                    f"**⚠️ Missing / Unverified Skills ({len(missing)} total):**\n"
                    f"{missing_display}\n\n"
                    f"**✅ Matched Skills ({len(matched)} total):**\n"
                    f"{matched_display}"
                ),
                "candidate_id": cid,
                "needs_disambiguation": False,
            }

        # 3H: Professional Experience / Tenure
        if any(w in q_lower for w in ["experience", "tenure", "years", "career"]):
            total_exp = cand_record.get("total_experience") or "Not Detected"
            rel_exp = cand_record.get("relevant_experience") or "Not Detected"
            return {
                "answer": (
                    f"⏳ **{cand_record['name']} — Professional Experience**\n\n"
                    f"- **Total Experience:** {total_exp}\n"
                    f"- **Relevant Domain Experience:** {rel_exp}\n"
                    f"- **Current Organization:** {cand_record.get('current_organization', 'Not Detected')}\n"
                    f"- **Current Designation:** {cand_record.get('current_designation', 'Not Detected')}"
                ),
                "candidate_id": cid,
                "needs_disambiguation": False,
            }

        # 3I: Recruitment Status & Transition History
        if any(w in q_lower for w in ["status", "stage", "pipeline", "progress"]):
            status = cand_record.get("current_status", "Screened")
            history = registry.get_candidate_status_history(cid, self.db_path)

            table_rows = []
            for h in history[:5]:
                dt = h['changed_at'][:16].replace('T', ' ')
                prev_s = h.get('previous_status') or 'None'
                new_s = h.get('new_status', 'Screened')
                by = h.get('changed_by') or 'Recruiter'
                notes = h.get('notes') or '-'
                table_rows.append(f"| {dt} | {prev_s} | **{new_s}** | {by} | {notes} |")

            history_md = ""
            if table_rows:
                history_md = (
                    "\n\n**Status Transition History:**\n"
                    "| Date | Previous Status | New Status | Changed By | Notes |\n"
                    "|---|---|---|---|---|\n"
                    + "\n".join(table_rows)
                )
            else:
                history_md = "\n\n*No status transitions recorded yet.*"

            score_display = f"**{latest_screening['deterministic_score']}/100**" if latest_screening else "Not Screened"
            target_role = latest_screening.get('job_title', 'Not specified') if latest_screening else 'N/A'

            return {
                "answer": (
                    f"📋 **{cand_record['name']} — Recruitment Status**\n\n"
                    f"- **Current Recruitment Status:** `{status}`\n"
                    f"- **Candidate ID:** `{cid}`\n"
                    f"- **Target Role:** {target_role}\n"
                    f"- **Fitment Score:** {score_display}\n"
                    f"- **Last Updated:** `{cand_record.get('updated_at', 'N/A')}`"
                    f"{history_md}"
                ),
                "candidate_id": cid,
                "needs_disambiguation": False,
            }

        # 3J: Interview Questions / Probes / Recruiter Recommendations
        if any(w in q_lower for w in ["question", "interview", "ask", "probe", "validate", "recommendation"]):
            if latest_screening:
                try:
                    questions = json.loads(latest_screening.get("interview_questions", "[]"))
                except Exception:
                    questions = []
            else:
                questions = []

            if not questions:
                questions = [
                    f"Can you detail your production experience in enterprise network infrastructure?",
                    f"Walk us through a critical P1 outage or high-severity escalation you resolved.",
                    f"How do you approach root cause analysis when working in complex telecommunications setups?",
                ]

            q_formatted = "\n\n".join([f"**{i+1}.** {q_text}" for i, q_text in enumerate(questions)])
            return {
                "answer": (
                    f"🎤 **Recommended Technical Interview Probes for {cand_record['name']}:**\n\n"
                    f"{q_formatted}\n\n"
                    f"💡 *Probes targeted towards verified experience gaps and operational depth.*"
                ),
                "candidate_id": cid,
                "needs_disambiguation": False,
            }

        # 3K: Default: Standardized Candidate Profile (Adhering strictly to Section 8)
        return {
            "answer": format_candidate_profile(cand_record, latest_screening),
            "candidate_id": cid,
            "needs_disambiguation": False,
        }
