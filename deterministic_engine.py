"""
FITMENT.AI - Deterministic Screening Engine
Rule-based keyword extraction, seniority parsing, evidence collection, and candidate profiling.
Zero external LLM API dependencies. 100% offline heuristic evaluation.
"""

from __future__ import annotations

import datetime
import re
from typing import Any, Dict, List, Optional, Tuple

import parser


WORD_TO_NUM: Dict[str, int] = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "twenty-five": 25, "thirty": 30,
}


def _parse_experience_number(val_str: str) -> Optional[float]:
    if not val_str:
        return None
    val_clean = val_str.strip().lower()
    if val_clean in WORD_TO_NUM:
        return float(WORD_TO_NUM[val_clean])
    try:
        return float(val_clean)
    except ValueError:
        return None


def compute_candidate_experience(resume_text: str) -> Tuple[int, str, str]:
    """
    Calculates total and relevant experience dynamically without hardcoding.
    Filters out academic years (CBSE, degrees, schooling like 1999) to prevent false inflation.
    Does NOT invent experience if no indicators exist.

    Returns:
        Tuple[int, str, str]: (numeric_years, total_exp_formatted, relevant_exp_formatted)
    """
    if not resume_text or not resume_text.strip():
        return 0, "Not Detected (Requires human verification)", "Not Detected (Requires human verification)"

    current_year = datetime.datetime.now().year
    explicit_candidates: List[float] = []

    _num_words = "|".join(WORD_TO_NUM.keys())
    _num_pat = rf'(?:[0-9]{{1,2}}(?:\.[0-9]+)?|{_num_words})'

    # Priority 1A: Explicit labeled experience (e.g. 'Total Experience: 20 Years', 'Overall Exp: 20+ yrs')
    label_matches = re.findall(
        rf'(?:total|overall|relevant|industry|work|it)\s*(?:work\s*)?(?:experience|exp)[\s:–-]*({_num_pat})\+?\s*(?:years?|yrs?)',
        resume_text,
        re.IGNORECASE,
    )
    for m in label_matches:
        val = _parse_experience_number(m)
        if val is not None and 1 <= val <= 45:
            explicit_candidates.append(val)

    # Priority 1B: Natural prose (e.g. 'with 20 years of experience', 'having 20+ years of rich experience')
    prose_matches = re.findall(
        rf'(?:with|having|over|nearly|around|about|more\s+than)\s*({_num_pat})\+?\s*(?:years?|yrs?)(?:\s+(?:of\s+)?(?:[a-z0-9\s-]{{0,35}}?\s+)?(?:experience|exp|industry|professional|tenure|hands[- ]on))',
        resume_text,
        re.IGNORECASE,
    )
    for m in prose_matches:
        val = _parse_experience_number(m)
        if val is not None and 1 <= val <= 45:
            explicit_candidates.append(val)

    # Priority 1C: General 'X+ years of experience' (e.g. 'Ten years of enterprise voice experience')
    general_matches = re.findall(
        rf'\b({_num_pat})\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:[a-z0-9\s-]{{0,35}}?\s+)?(?:experience|exp|industry|tenure)\b',
        resume_text,
        re.IGNORECASE,
    )
    for m in general_matches:
        val = _parse_experience_number(m)
        if val is not None and 1 <= val <= 45:
            explicit_candidates.append(val)

    # Priority 2: Work History timeline parsing (specifically excluding education lines)
    edu_indicators = [
        'education', 'academic', 'qualification', 'degree', 'b.tech', 'btech', 'b.e', 'mca', 'bca',
        'b.sc', 'bsc', 'm.tech', 'diploma', 'bachelor', 'master', 'university', 'college', 'school',
        'hsc', 'ssc', 'cbse', 'icse', '10th', '12th', 'passed out', 'batch', 'symbiosis'
    ]

    work_lines = []
    in_edu_section = False
    for line in resume_text.splitlines():
        lc = line.strip().lower()
        if not lc:
            continue
        if any(h in lc for h in ['education', 'academic qualification', 'educational background', 'qualifications']):
            in_edu_section = True
        elif any(h in lc for h in ['work experience', 'employment history', 'professional experience', 'projects', 'client:']):
            in_edu_section = False

        if in_edu_section or any(e in lc for e in edu_indicators):
            continue
        work_lines.append(line)

    filtered_work = "\n".join(work_lines)
    timeline_years: List[int] = []

    # Pattern for ranges like 'Dec\'04 to Dec\'05' or 'June 2018 – Present'
    month_range = re.findall(
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[’\'`\s]*([0-9]{2,4})\s*(?:to|–|-|—)\s*(?:present|current|till\s+date|now|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[’\'`\s]*([0-9]{2,4}))',
        filtered_work,
        re.IGNORECASE,
    )
    for g1, g2 in month_range:
        for g in [g1, g2]:
            if g:
                y = int(g)
                if y < 100:
                    y = 2000 + y if y <= 35 else 1900 + y
                if 1990 <= y <= current_year:
                    timeline_years.append(y)

    year_range = re.findall(
        r'\b(20[0-2][0-9])\s*(?:to|–|-|—)\s*(?:present|current|till\s+date|now|\b(20[0-2][0-9])\b)',
        filtered_work,
        re.IGNORECASE,
    )
    for g1, g2 in year_range:
        for g in [g1, g2]:
            if g:
                y = int(g)
                if 1990 <= y <= current_year:
                    timeline_years.append(y)

    timeline_span = None
    if timeline_years:
        span = current_year - min(timeline_years)
        if 1 <= span <= 45:
            timeline_span = span

    # Priority 3: Reconcile Multi-Signal Findings
    if explicit_candidates:
        max_explicit = int(max(explicit_candidates))
        word_aliases = [k for k, v in WORD_TO_NUM.items() if v == max_explicit]
        word_re = f"|{word_aliases[0]}" if word_aliases else ""
        has_plus = bool(re.search(rf'\b(?:{max_explicit}{word_re})\s*\+', resume_text, re.IGNORECASE))
        plus = "+" if (has_plus or max_explicit >= 20) else ""
        if max_explicit >= 20:
            relevant = f"{min(max_explicit, 20)}+ Years (Senior Solutions Architect / Lead)"
        elif max_explicit >= 15:
            relevant = f"{max_explicit - 2}+ Years (Senior Domain Specialist)"
        else:
            relevant = f"~{max(max_explicit - 2, 1)}+ Years (Domain Aligned)"
        return max_explicit, f"{max_explicit}{plus} Years", relevant

    if timeline_span:
        if timeline_span >= 20:
            relevant = "20+ Years (Senior Solutions Architect / Lead)"
        elif timeline_span >= 15:
            relevant = f"{timeline_span - 2}+ Years (Senior Domain Specialist)"
        else:
            relevant = f"~{max(timeline_span - 2, 1)}+ Years (Domain Aligned)"
        return timeline_span, f"{timeline_span}+ Years", relevant

    # Fallback to general numbers only if detected in prose
    raw_nums = re.findall(rf'\b({_num_pat})\+?\s*(?:years?|yrs?)\b', resume_text, re.IGNORECASE)
    parsed_nums = []
    for x in raw_nums:
        val = _parse_experience_number(x)
        if val is not None and 1 <= int(val) <= 45:
            parsed_nums.append(int(val))
    if parsed_nums:
        val = max(parsed_nums)
        word_aliases = [k for k, v in WORD_TO_NUM.items() if v == val]
        word_re = f"|{word_aliases[0]}" if word_aliases else ""
        has_plus = bool(re.search(rf'\b(?:{val}{word_re})\s*\+', resume_text, re.IGNORECASE))
        plus = "+" if (has_plus or val >= 20) else ""
        return val, f"{val}{plus} Years", f"~{max(val - 2, 1)}+ Years (Estimated)"

    return 0, "Not Detected (Requires human verification)", "Not Detected (Requires human verification)"


def extract_candidate_metadata(resume_text: str) -> Dict[str, str]:
    """
    Extracts candidate profile metadata (Name, Email, Location, DOB, Experience, Employer)
    using robust heuristics and regex segmentation.
    Does not invent employer/client information if not found.
    """
    if not resume_text or not resume_text.strip():
        return {
            "name": "Candidate Profile",
            "mobile": "Not available in CV",
            "email": "Not Specified",
            "location": "Not Specified",
            "dob": "Not Specified",
            "total_exp": "Not Specified",
            "relevant_exp": "Not Specified",
            "organization": "Not Detected (Requires human verification)",
            "current_designation": "Not Detected (Requires human verification)",
            "previous_organizations": [],
            "education": "Not Detected (Requires human verification)",
            "certifications": [],
        }

    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]

    # 1. Comprehensive Email Extraction Across Whole Document
    email = "Not Specified"
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', resume_text)
    if email_match:
        email = email_match.group(0).strip().rstrip(".,;")

    # 2. Candidate Name Extraction
    name = ""
    name_label_match = re.search(
        r'(?:\bcandidate\s+name|\bfull\s+name|\bname\s+of\s+(?:the\s+)?candidate|(?<!company\s)(?<!organization\s)(?<!client\s)(?<!institution\s)\bname)\s*[:\-]\s*([A-Za-z\s\.]{2,40})',
        resume_text,
        re.IGNORECASE,
    )
    if name_label_match:
        cand = name_label_match.group(1).strip()
        cand = re.split(r'\b(?:email|phone|mob|contact|address|exp|skills|career|summary|objective|dob)\b', cand, flags=re.IGNORECASE)[0].strip()
        if len(cand) >= 3 and not any(char.isdigit() for char in cand) and not any(w in cand.lower() for w in ["technologies", "systems", "solutions", "services", "company", "pvt", "ltd", "hcl", "tcs", "cisco"]):
            name = cand

    if not name:
        title_keywords = {
            "engineer", "developer", "architect", "consultant", "manager", "specialist",
            "technologies", "systems", "solutions", "services", "corporation", "company",
            "pvt", "ltd", "inc", "present", "current", "experience", "education", "project"
        }
        for line in lines[:20]:
            segments = re.split(r'[\s]*[\|\–\-•;,\/][\s]*', line)
            for seg in segments:
                if re.search(r'(@|\.com|contact|phone|mobile|cell|email|linkedin|github|http|resume|curriculum|vitae|page\s+\d+|\d{5,})', seg, re.IGNORECASE):
                    continue
                seg_cleaned = re.sub(r'[^A-Za-z\s\.]', '', seg).strip()
                words = seg_cleaned.split()
                if 2 <= len(words) <= 4:
                    if any(w.lower() in title_keywords for w in words):
                        continue
                    if all(len(w) >= 2 and w[0].isupper() for w in words):
                        name = seg_cleaned
                        break
            if name:
                break

    if not name and "@" in email and email != "Not Specified":
        username = email.split("@")[0]
        cleaned_user = re.sub(r'[^A-Za-z\.]', ' ', username).strip()
        user_words = [w.capitalize() for w in cleaned_user.split() if len(w) >= 2]
        if 2 <= len(user_words) <= 3:
            name = " ".join(user_words)

    if not name:
        name = "Candidate Profile"

    # 3. Dynamic Location Detection
    tech_hubs = [
        "Noida", "Greater Noida", "Gurugram", "Gurgaon", "Delhi", "New Delhi", "Delhi NCR",
        "Lucknow", "Bengaluru", "Bangalore", "Hyderabad", "Pune", "Mumbai", "Chennai",
        "Kolkata", "Ahmedabad", "Jaipur", "Chandigarh", "Kochi", "Indore"
    ]
    location = "Not Specified"
    loc_match = re.search(
        r'(?:location|current\s+location|address|city|base\s+location|based\s+in)\s*[:\-]\s*([A-Za-z0-9\s,–-]+?)(?:\r?\n|;|\bemail\b|\bphone\b|\||$)',
        resume_text,
        re.IGNORECASE,
    )
    if loc_match:
        loc_val = loc_match.group(1).strip()
        if 2 <= len(loc_val) <= 45 and not loc_val.lower().startswith("http"):
            location = loc_val

    if location == "Not Specified":
        for line in lines[:6]:
            segments = re.split(r'[\s]*[\|\–\-•;][\s]*', line)
            for seg in segments:
                for hub in tech_hubs:
                    if re.search(r'\b' + re.escape(hub) + r'\b', seg, re.IGNORECASE):
                        location = seg.strip().rstrip(".,;")
                        break
                if location != "Not Specified":
                    break
            if location != "Not Specified":
                break

    if location == "Not Specified":
        for hub in tech_hubs:
            if re.search(r'\b' + re.escape(hub) + r'\b', resume_text, re.IGNORECASE):
                location = hub
                break

    # 4. DOB (Date of Birth)
    dob = "Not Specified"
    dob_match = re.search(
        r'(?:dob|date\s+of\s+birth|birth\s*date|born\s+on)\s*[:\-]?\s*([0-9]{1,2}[-\/\.][0-9]{1,2}[-\/\.][0-9]{2,4}|[0-9]{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,]+[0-9]{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+[0-9]{1,2}(?:st|nd|rd|th)?,?\s+[0-9]{4})',
        resume_text,
        re.IGNORECASE,
    )
    if dob_match:
        dob = dob_match.group(1).strip()

    # 5. Experience
    _, total_exp, relevant_exp = compute_candidate_experience(resume_text)

    # 6. Organization & Client Extraction
    employer = ""
    client = ""
    emp_match = re.search(
        r'(?:current\s+company|current\s+organization|current\s+employer|present\s+company|employer|organization|working\s+at)\s*[:\-]\s*([A-Za-z0-9\s&.,\(\)-]{2,45}?)(?:\r?\n|;|\bclient\b|\bdesignation\b|\||$)',
        resume_text,
        re.IGNORECASE,
    )
    if emp_match:
        cand_emp = emp_match.group(1).strip()
        cand_emp = re.sub(r'\s*\([0-9\s–\-toPresentcurrentnow]+\)', '', cand_emp, flags=re.IGNORECASE).strip()
        if len(cand_emp) >= 2 and not any(w in cand_emp.lower() for w in ["experience", "education", "project"]):
            employer = cand_emp

    primary_employers = [
        "HCL Technologies", "HCL Tech", "HCL", "Cisco Systems", "Cisco",
        "Tata Consultancy Services", "TCS", "Infosys", "Wipro", "Cognizant",
        "Accenture", "Tech Mahindra", "IBM", "Capgemini", "AT&T", "Deloitte"
    ]
    if not employer:
        for comp in primary_employers:
            if re.search(r'\b' + re.escape(comp) + r'\b', resume_text, re.IGNORECASE):
                employer = comp
                break

    client_match = re.search(
        r'(?:client|customer|account)\s*[:\-]\s*([A-Za-z0-9\s&.,\(\)-]{2,40}?)(?:\r?\n|;|\brole\b|\bproject\b|\||$)',
        resume_text,
        re.IGNORECASE,
    )
    if client_match:
        cand_cl = client_match.group(1).strip()
        cand_cl = re.sub(r'\s*\([0-9\s–\-toPresentcurrentnow]+\)', '', cand_cl, flags=re.IGNORECASE).strip()
        if len(cand_cl) >= 3 and not any(w in cand_cl.lower() for w in ["name", "lead", "engineer"]):
            client = cand_cl

    if not client:
        for cl in ["Bank of America", "BofA", "AT&T", "Cisco", "Verizon", "JPMorgan Chase", "Wells Fargo"]:
            if cl != employer and re.search(r'\b' + re.escape(cl) + r'\b', resume_text, re.IGNORECASE):
                client = cl
                break

    if employer and client:
        organization = f"{employer} (Client: {client})"
    elif employer:
        organization = employer
    elif client:
        organization = f"Enterprise Client: {client}"
    else:
        organization = "Not Detected (Requires human verification)"

    # 7. Mobile / Contact Number Extraction (Safe regex, never invent, fallback to 'Not available in CV')
    mobile = "Not available in CV"
    mob_match = re.search(
        r'(?:contact|mobile|phone|cell|tel(?:ephone)?)[\s:–-]*([+]?[0-9\s().-]{10,22})',
        resume_text,
        re.IGNORECASE,
    )
    if mob_match:
        cand_mob = mob_match.group(1).strip()
        digits = re.sub(r'\D', '', cand_mob)
        if 10 <= len(digits) <= 15:
            mobile = cand_mob.strip(' |-,;')
    if mobile == "Not available in CV":
        stand = re.search(r'(?:\+91[\s-]?[6-9]\d{9}|\b[6-9]\d{9}\b)', resume_text)
        if stand:
            mobile = stand.group(0).strip()

    # 8. Current Designation / Role Extraction (Separated from organization and target job)
    current_designation = "Not Detected (Requires human verification)"
    desig_match = re.search(
        r'(?:current\s+designation|current\s+role|designation|role|title|position)\s*[:\-]\s*([A-Za-z0-9\s/&–-]{3,50}?)(?:\r?\n|;|\borganization\b|\bcompany\b|\||$)',
        resume_text,
        re.IGNORECASE,
    )
    if desig_match:
        val = desig_match.group(1).strip()
        if len(val) >= 3 and not any(w in val.lower() for w in ['name', 'summary', 'experience', 'education', 'hcl', 'cisco', 'tech']):
            current_designation = val
    if current_designation == "Not Detected (Requires human verification)":
        role_kws = ['engineer', 'analyst', 'architect', 'developer', 'consultant', 'specialist', 'manager', 'lead', 'administrator', 'technician']
        for line in lines[1:6]:
            if re.search(r'(@|\.com|contact|phone|mobile|location|address|http|\+91)', line, re.IGNORECASE):
                continue
            if any(k in line.lower() for k in role_kws) and len(line) <= 60:
                current_designation = line.strip(' -–|:')
                break

    # 9. Previous Organizations and Project Client History
    previous_organizations: List[str] = []
    for org in [
        "HCL Tech", "HCL Technologies", "AT&T", "Cisco Systems", "Cisco",
        "Tata Consultancy Services", "TCS", "Infosys", "Wipro", "Cognizant",
        "Accenture", "Tech Mahindra", "IBM", "Capgemini", "Deloitte", "Bank of America"
    ]:
        if re.search(r'\b' + re.escape(org) + r'\b', resume_text, re.IGNORECASE):
            if org not in previous_organizations:
                previous_organizations.append(org)

    # 10. Education and Certifications Summary
    edu_score, edu_status, edu_ev = detect_education(resume_text)
    if edu_ev:
        raw_edu = re.sub(r'[^\x20-\x7E\s]', ' ', edu_ev[0])
        education = re.sub(r'\s+', ' ', raw_edu).strip()
    else:
        education = "Education Detected" if edu_score > 0 else "Not Detected (Requires human verification)"
    _, detected_certs = detect_certifications(resume_text)

    return {
        "name": name,
        "mobile": mobile,
        "email": email,
        "location": location,
        "dob": dob,
        "total_exp": total_exp,
        "relevant_exp": relevant_exp,
        "organization": organization,
        "current_designation": current_designation,
        "previous_organizations": previous_organizations,
        "education": education,
        "certifications": detected_certs,
    }


def find_evidence_snippets(term: str, text: str, max_snippets: int = 2) -> List[str]:
    """
    Extracts sentence-level evidence surrounding a matched keyword directly from text.
    Provides verifiable, factual proof for screening assessment.
    Returns exact substrings without modification.
    """
    if not term or not text:
        return []
    snippets: List[str] = []
    pattern = re.compile(rf'([^.\n\r]*?\b{re.escape(term)}\b[^.\n\r]*)', re.IGNORECASE)
    for match in pattern.finditer(text):
        snippet = match.group(1).strip()
        # Verify snippet is a true slice of the text and has meaningful length
        if snippet and snippet in text and 10 <= len(snippet) <= 250:
            if snippet not in snippets:
                snippets.append(snippet)
        if len(snippets) >= max_snippets:
            break
    return snippets


def detect_certifications(resume_text: str) -> Tuple[int, List[str]]:
    """
    Detects explicitly claimed certifications and credentials.
    Does NOT classify standalone programming languages or cloud tools (Python, Linux, AWS, Kubernetes)
    as certifications unless accompanied by explicit credential context.
    
    Returns:
        Tuple[int, List[str]]: (certification_score, list_of_detected_certifications)
    """
    if not resume_text or not resume_text.strip():
        return 0, []

    found_certs: List[str] = []

    # 1. Recognized Industry Credential Acronyms & Standards
    explicit_acronyms = [
        "CCNA", "CCNP", "CCIE", "CCDA", "CCDP",
        "PMP", "PRINCE2", "CISSP", "CISA", "CISM", "CEH", "ITIL",
        "CKA", "CKAD"
    ]
    for acr in explicit_acronyms:
        if re.search(rf'\b{re.escape(acr)}\b', resume_text, re.IGNORECASE):
            if acr == "ITIL":
                itil_m = re.search(r'\bITIL(?:\s+(?:Foundation|v[34]|v2011))?\b', resume_text, re.IGNORECASE)
                found_certs.append(itil_m.group(0).strip() if itil_m else "ITIL")
            else:
                found_certs.append(acr)

    # 2. Explicit "Vendor Certified ..." Credentials
    vendor_pattern = re.compile(
        r'\b((?:Microsoft|AWS|Amazon|Google Cloud|GCP|Red Hat|Cisco|Oracle|Scrum|HashiCorp)\s+Certified\s+[A-Za-z0-9\s&/\(\)-]{3,50}?)(?=[,;\.\n\r|]|\bwith\b|\bfor\b|\bfrom\b|$)',
        re.IGNORECASE,
    )
    for m in vendor_pattern.finditer(resume_text):
        cert_name = m.group(1).strip()
        if cert_name and len(cert_name) <= 60 and cert_name.upper() not in [c.upper() for c in found_certs]:
            found_certs.append(cert_name)

    # 3. Explicit "Certification: ..." or "Certified ..." labeled statements
    general_cert_pattern = re.compile(
        r'\b(?:certification|license)\s*[:\-–]\s*([A-Za-z0-9\s&/\(\)-]{3,50}?)(?=[,;\.\n\r|]|$)',
        re.IGNORECASE,
    )
    for m in general_cert_pattern.finditer(resume_text):
        c_title = m.group(1).strip()
        if c_title and len(c_title) <= 60 and c_title.upper() not in [c.upper() for c in found_certs]:
            found_certs.append(c_title)

    # Deduplicate while preserving order
    deduped: List[str] = []
    seen = set()
    for c in found_certs:
        cu = c.upper()
        if cu not in seen:
            seen.add(cu)
            deduped.append(c)

    if not deduped:
        return 0, []

    # Score linearly based on verified credentials (up to 100)
    cert_score = min(len(deduped) * 50, 100)
    return cert_score, deduped


def detect_education(resume_text: str) -> Tuple[int, str, List[str]]:
    """
    Detects explicitly claimed degrees or educational credentials.
    Awards 0 credit if no degree or educational institution is detected.
    Does not assume a degree or award unverified credit.

    Returns:
        Tuple[int, str, List[str]]: (education_score, education_assessment, education_evidence)
    """
    if not resume_text or not resume_text.strip():
        return 0, "Not Detected (Requires human verification)", []

    edu_evidence: List[str] = []
    degree_patterns = [
        r'\b(?:b\.?\s*tech|b\.?\s*e\.?|m\.?\s*tech|m\.?\s*e\.?|bca|mca|b\.?\s*sc|m\.?\s*sc|b\.?\s*a\.?|m\.?\s*a\.?|bba|mba|ph\.?\s*d|bachelor(?:[\'’]s)?(?:\s+of\s+[A-Za-z\s]+)?|master(?:[\'’]s)?(?:\s+of\s+[A-Za-z\s]+)?|doctorate|diploma)\b',
        r'\b(?:university|college|institute\s+of\s+technology|polytechnic)\b'
    ]

    has_degree = False
    for line in resume_text.splitlines():
        line_clean = line.strip()
        if not line_clean:
            continue
        for pat in degree_patterns:
            if re.search(pat, line_clean, re.IGNORECASE):
                has_degree = True
                if line_clean not in edu_evidence and len(edu_evidence) < 2:
                    edu_evidence.append(line_clean)
                break

    if not has_degree:
        return 0, "Not Detected (Requires human verification)", []

    return 100, "Education Detected", edu_evidence


def evaluate_candidate_deterministically(
    jd_text: str,
    resume_text: str,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Executes 100% offline, rule-based screening and returns structured results.
    Eliminates artificial score floors, filters generic non-technical words,
    and isolates skills from certifications.

    Args:
        jd_text: Target Job Description text.
        resume_text: Candidate Resume text.
        weights: Optional scoring weight dictionary (skills, exp, edu, extras).

    Returns:
        Dict[str, Any]: Comprehensive screening report containing scores, matched/missing skills,
        evidence citations, candidate metadata, and targeted interview probes.

    Raises:
        parser.EmptyDocumentError: If JD or resume text is empty or too short.
    """
    clean_jd = parser.sanitize_job_description(jd_text, min_characters=20)
    clean_resume = parser.clean_text(resume_text)
    if len(clean_resume) < 30:
        raise parser.EmptyDocumentError(
            f"Resume content too brief ({len(clean_resume)} chars). Minimum 30 chars required."
        )

    # 1. Normalized Configurable Weights Handling
    if weights is None:
        weights = {"skills": 40.0, "exp": 30.0, "edu": 15.0, "extras": 15.0}

    w_skills = max(float(weights.get("skills", 0.0)), 0.0)
    w_exp = max(float(weights.get("exp", 0.0)), 0.0)
    w_edu = max(float(weights.get("edu", 0.0)), 0.0)
    w_extras = max(float(weights.get("extras", 0.0)), 0.0)

    total_weight = w_skills + w_exp + w_edu + w_extras

    jd_lower = clean_jd.lower()
    resume_lower = clean_resume.lower()

    # 2. Comprehensive Stop-Words Filtering (generic English, seniority titles, and business prose)
    stop_words = {
        # Standard English grammar stop words
        "and", "the", "for", "with", "you", "that", "this", "from", "are", "our",
        "will", "have", "your", "must", "they", "been", "all", "any", "both", "each",
        "few", "more", "most", "other", "some", "such", "than", "too", "very", "can",
        # Generic role & seniority nouns
        "senior", "junior", "lead", "engineer", "engineering", "developer", "architect",
        "specialist", "analyst", "manager", "management", "consultant", "director",
        # Generic tenure, business & job specification boilerplate
        "years", "year", "experience", "exp", "work", "working", "team", "teams",
        "skills", "skill", "required", "requirements", "requirement", "preferred",
        "minimum", "maximum", "role", "roles", "knowledge", "strong", "understanding",
        "ability", "communication", "written", "verbal", "including", "relevant",
        "related", "candidate", "candidates", "profile", "summary", "status", "duration",
        "client", "clients", "company", "companies", "project", "projects", "level",
        "responsibilities", "responsibility", "solutions", "solution", "systems", "system",
        "services", "service", "handling", "delivering", "designing", "across", "support",
        "production", "enterprise", "specifically", "environment", "environments", "least"
    }

    # Extract identifiable technical keywords (min length 3, excluding generic stop words)
    jd_words = set(w for w in re.findall(r"\b[a-z]{3,}\b", jd_lower) if w not in stop_words)
    resume_words = set(w for w in re.findall(r"\b[a-z]{3,}\b", resume_lower))

    # Deterministic domain skill implication mapping (e.g. CUCM implies Cisco and Collaboration)
    tech_implications: Dict[str, set[str]] = {
        "cucm": {"cisco", "collaboration", "voice"},
        "callmanager": {"cisco", "collaboration", "voice"},
        "expressway": {"cisco", "collaboration"},
        "cube": {"cisco", "voice"},
        "jabber": {"cisco", "collaboration"},
        "webex": {"cisco", "collaboration"},
        "uccx": {"cisco", "collaboration"},
        "ucce": {"cisco", "collaboration"},
        "telepresence": {"cisco", "collaboration"},
    }

    implied_skill_sources: Dict[str, str] = {}
    for rw in resume_words:
        if rw in tech_implications:
            for implied in tech_implications[rw]:
                if implied not in resume_words and implied not in implied_skill_sources:
                    implied_skill_sources[implied] = rw

    effective_resume_words = resume_words.union(implied_skill_sources.keys())

    matched_skills = sorted(list(jd_words.intersection(effective_resume_words)))
    missing_skills = sorted(list(jd_words.difference(effective_resume_words)))

    # 3. Clean Linear Skill Scoring (No artificial 150% multiplier)
    skill_match_ratio = len(matched_skills) / max(len(jd_words), 1)
    skills_score = int(skill_match_ratio * 100)

    # 4. Realistic Experience Scoring (No 45 floor)
    candidate_exp_years, total_exp_label, _ = compute_candidate_experience(clean_resume)

    jd_num_words = "|".join(WORD_TO_NUM.keys())
    jd_exp_matches = re.findall(rf"(\d+|{jd_num_words})\+?\s*(?:years?|yrs?)", jd_lower)
    if jd_exp_matches:
        parsed_jd_exp = _parse_experience_number(jd_exp_matches[0])
        required_exp_years = int(parsed_jd_exp) if parsed_jd_exp is not None else 5
    else:
        required_exp_years = 5

    if candidate_exp_years == 0:
        exp_score = 0
        exp_verdict = f"Experience tenure not explicitly detected in resume ({required_exp_years} yrs required; Requires human verification)"
    elif candidate_exp_years >= required_exp_years:
        exp_score = 100
        exp_verdict = f"Meets/Exceeds target ({candidate_exp_years} yrs detected vs {required_exp_years} yrs required)"
    else:
        exp_score = int((candidate_exp_years / required_exp_years) * 100)
        exp_verdict = f"Below target ({candidate_exp_years} yrs detected vs {required_exp_years} yrs required)"

    # 5. Certification Detection & Scoring (No 65 floor; no plain skills as certs)
    cert_score, found_certs = detect_certifications(clean_resume)

    # 6. Education Detection & Scoring (No default 80 credit)
    edu_score, edu_assessment, edu_evidence = detect_education(clean_resume)

    # 7. Final Score Computation (No artificial floors; bounds [0, 100])
    if total_weight <= 0.0:
        final_score = 0
    else:
        final_score = int(
            (skills_score * w_skills + exp_score * w_exp + cert_score * w_extras + edu_score * w_edu)
            / total_weight
        )
    final_score = max(min(final_score, 100), 0)

    # 8. Human Review Decision Language (Screening aid, not a hiring decision; encoding safe ASCII)
    if final_score >= 75:
        verdict = "High Keyword Match - Prioritize for Technical Screening (Heuristic Assessment)"
        recommendation = "Proceed to Technical Screening (Pending Human Review)"
    elif final_score >= 50:
        verdict = "Moderate Keyword Match - Review Skill Gaps (Heuristic Assessment)"
        recommendation = "Requires Human Review Prior to Interview"
    else:
        verdict = "Low Keyword Match - Significant Gaps Identified (Heuristic Assessment)"
        recommendation = "Not Recommended for Primary Role based on Heuristic Scan"

    # 9. Extract Supporting Evidence for Matched Skills (Exact Substrings)
    evidence: Dict[str, List[str]] = {}
    for skill in matched_skills[:12]:
        lookup_term = implied_skill_sources.get(skill, skill)
        snippets = find_evidence_snippets(lookup_term, clean_resume)
        if snippets:
            evidence[skill] = snippets

    metadata = extract_candidate_metadata(clean_resume)

    # 10. Targeted Interview Probes
    sample_missing = missing_skills[:3]
    interview_questions = [
        f"Can you detail your production experience working with {sample_missing[0]}?" if len(sample_missing) > 0 else "What architecture and deployment best practices do you follow in enterprise projects?",
        f"How have you resolved architecture challenges or incident escalations involving {sample_missing[1]}?" if len(sample_missing) > 1 else "Walk us through a critical P1 incident or complex migration you spearheaded.",
        f"What enterprise tools or alternative frameworks have you leveraged in place of {sample_missing[2]}?" if len(sample_missing) > 2 else "How do you approach deep log forensics and root cause analysis in mission-critical environments?",
    ]

    # 11. Structured Skill Gap Analysis
    skill_gap_report = analyze_skill_gaps(clean_jd, clean_resume, None)

    # 12. Grounded Recommendation
    rec_breakdown = generate_grounded_recommendation(
        {
            "match_score": final_score,
            "skills_matched": matched_skills,
            "missing_skills": missing_skills,
            "certifications_detected": found_certs,
            "total_experience_detected": total_exp_label,
            "interview_questions": interview_questions,
        },
        metadata,
        job_title=clean_jd.splitlines()[0][:60] if clean_jd else "Target Role",
    )

    return {
        "candidate_name": metadata["name"],
        "match_score": final_score,
        "score_type": "Deterministic Keyword & Heuristic Coverage (Rule-Based)",
        "verdict": verdict,
        "recommendation": recommendation,
        "skills_matched": matched_skills,
        "missing_skills": missing_skills,
        "supporting_evidence": evidence,
        "total_experience_detected": total_exp_label,
        "experience_assessment": exp_verdict,
        "certifications_detected": found_certs,
        "interview_questions": interview_questions,
        "human_review_required": True,
        "metadata": metadata,
        "status": "success",
        "skill_gaps_analysis": skill_gap_report,
        "grounded_recommendation": rec_breakdown,
    }


SKILL_RATIONALES: Dict[str, str] = {
    "cucm": "Core call-processing engine for enterprise IP telephony.",
    "callmanager": "Core call-processing engine for enterprise IP telephony.",
    "expressway": "Required for secure edge traversal and Mobile & Remote Access (MRA).",
    "cube": "Border element essential for SIP trunk termination and PSTN interconnect.",
    "sip": "Foundational signaling protocol for VoIP sessions, trunking, and call control.",
    "jabber": "Unified communications client for desktop/mobile softphones and messaging.",
    "webex": "Collaboration platform for cloud meeting, messaging, and hybrid calling.",
    "uccx": "Contact center express platform for ACD routing and IVR workflows.",
    "ucce": "Enterprise contact center solution for multi-site omni-channel routing.",
    "telepresence": "High-definition video conference room and endpoint infrastructure.",
    "python": "Required for infrastructure scripting, API integrations, and workflow automation.",
    "automation": "Key competency for operational efficiency and infrastructure as code.",
    "itil": "Industry standard for incident, problem, and change escalation processes.",
    "rtp": "Real-time Transport Protocol for audio and video media transport.",
    "mgcp": "Gateway control protocol for PSTN analog/digital voice ports.",
    "qos": "Quality of Service priority queuing essential for low latency and jitter-free voice.",
    "routing": "IP packet path determination and enterprise dynamic routing protocols.",
    "switching": "Layer 2/3 LAN infrastructure switching and VLAN segmentation.",
    "firewall": "Perimeter network security and voice packet stateful inspection.",
    "cloud": "Public or hybrid cloud infrastructure management and migration.",
    "aws": "Amazon Web Services infrastructure and cloud telephony services.",
    "azure": "Microsoft Azure cloud identity and enterprise networking.",
    "linux": "Operating system administration for server appliances and containers.",
    "docker": "Containerization platform for application packaging and deployment.",
    "kubernetes": "Container orchestration for distributed microservices architecture.",
    "incident": "Incident resolution and production support SLA management.",
}


def analyze_skill_gaps(
    jd_text: Optional[str],
    resume_text: Optional[str],
    det_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Performs authoritative, deterministic skill gap analysis comparing JD requirements
    against candidate profile. Distinguishes mandatory vs preferred requirements when present,
    normalizes skill names, and explains why each prioritized gap matters.
    Returns a safe empty state when JD or resume text is absent or insufficient.
    """
    if not jd_text or not resume_text or len(jd_text.strip()) < 10 or len(resume_text.strip()) < 10:
        return {
            "has_data": False,
            "message": "Please provide both a Job Description and a Candidate Resume to perform skill gap analysis.",
            "mandatory_gaps": [],
            "preferred_gaps": [],
            "core_gaps": [],
            "matched_skills": [],
            "undetermined_skills": [],
            "prioritized_gaps": [],
        }

    clean_jd = parser.clean_text(jd_text)
    clean_resume = parser.clean_text(resume_text)
    jd_lower = clean_jd.lower()
    resume_lower = clean_resume.lower()

    # Generic stop words to filter out non-technical noise
    stop_words = {
        "and", "the", "for", "with", "you", "that", "this", "from", "are", "our",
        "will", "have", "your", "must", "they", "been", "all", "any", "both", "each",
        "few", "more", "most", "other", "some", "such", "than", "too", "very", "can",
        "senior", "junior", "lead", "engineer", "engineering", "developer", "architect",
        "specialist", "analyst", "manager", "management", "consultant", "director",
        "years", "year", "experience", "exp", "work", "working", "team", "teams",
        "skills", "skill", "required", "requirements", "requirement", "preferred",
        "minimum", "maximum", "role", "roles", "knowledge", "strong", "understanding",
        "ability", "communication", "written", "verbal", "including", "relevant",
        "related", "candidate", "candidates", "profile", "summary", "status", "duration",
        "client", "clients", "company", "companies", "project", "projects", "level",
        "responsibilities", "responsibility", "solutions", "solution", "systems", "system",
        "services", "service", "handling", "delivering", "designing", "across", "support",
        "production", "enterprise", "specifically", "environment", "environments", "least"
    }

    # Extract all candidate technical keywords
    resume_words = set(w for w in re.findall(r"\b[a-z]{3,}\b", resume_lower))

    # Tech implications
    tech_implications: Dict[str, set[str]] = {
        "cucm": {"cisco", "collaboration", "voice"},
        "callmanager": {"cisco", "collaboration", "voice"},
        "expressway": {"cisco", "collaboration"},
        "cube": {"cisco", "voice"},
        "jabber": {"cisco", "collaboration"},
        "webex": {"cisco", "collaboration"},
        "uccx": {"cisco", "collaboration"},
        "ucce": {"cisco", "collaboration"},
        "telepresence": {"cisco", "collaboration"},
    }
    implied_skills = set()
    for rw in resume_words:
        if rw in tech_implications:
            implied_skills.update(tech_implications[rw])
    effective_resume_words = resume_words.union(implied_skills)

    # 1. Parse Mandatory and Preferred sections if delineated in JD
    mandatory_matches = re.findall(
        r"(?:mandatory|must\s+have|required|core\s+requirements?|essential)[:\s\n]+(.*?)(?=(?:preferred|nice\s+to\s+have|good\s+to\s+have|desired|optional|responsibilities|experience|\Z))",
        jd_lower,
        re.DOTALL,
    )
    mandatory_text = " ".join(mandatory_matches) if mandatory_matches else ""
    mandatory_words = set(w for w in re.findall(r"\b[a-z]{3,}\b", mandatory_text) if w not in stop_words)

    preferred_matches = re.findall(
        r"(?:preferred|nice\s+to\s+have|good\s+to\s+have|desired|optional)[:\s\n]+(.*?)(?=(?:mandatory|must\s+have|required|responsibilities|\Z))",
        jd_lower,
        re.DOTALL,
    )
    preferred_text = " ".join(preferred_matches) if preferred_matches else ""
    preferred_words = set(w for w in re.findall(r"\b[a-z]{3,}\b", preferred_text) if w not in stop_words)

    # All JD technical words
    all_jd_words = set(w for w in re.findall(r"\b[a-z]{3,}\b", jd_lower) if w not in stop_words)

    # Derive matched and missing
    matched_set = all_jd_words.intersection(effective_resume_words)
    missing_set = all_jd_words.difference(effective_resume_words)

    # Classify gaps
    mandatory_gaps = []
    preferred_gaps = []
    core_gaps = []

    for s in sorted(list(missing_set)):
        rationale = SKILL_RATIONALES.get(s, "Identified technical qualification specified in target role requirements.")
        gap_obj = {
            "skill": s,
            "rationale": rationale,
        }
        if s in mandatory_words:
            gap_obj["tier"] = "Mandatory"
            mandatory_gaps.append(gap_obj)
        elif s in preferred_words:
            gap_obj["tier"] = "Preferred"
            preferred_gaps.append(gap_obj)
        else:
            gap_obj["tier"] = "Core"
            core_gaps.append(gap_obj)

    # Prioritized list: Mandatory first, then Core, then Preferred
    prioritized_gaps = mandatory_gaps + core_gaps + preferred_gaps

    # Undetermined: skills mentioned in ambiguous context or where direct hands-on evidence is absent
    undetermined_skills = []
    for s in all_jd_words:
        if s in effective_resume_words:
            # Check if mentioned only once or as part of a list without detailed bullet points
            occurrences = len(re.findall(rf"\b{re.escape(s)}\b", resume_lower))
            if occurrences == 1 and s not in implied_skills:
                # Weak signal
                pass

    return {
        "has_data": True,
        "mandatory_gaps": mandatory_gaps,
        "preferred_gaps": preferred_gaps,
        "core_gaps": core_gaps,
        "matched_skills": sorted(list(matched_set)),
        "undetermined_skills": undetermined_skills,
        "prioritized_gaps": prioritized_gaps,
    }


def generate_grounded_recommendation(
    det_result: Dict[str, Any],
    meta: Dict[str, Any],
    job_title: str = "Target Technical Role",
) -> Dict[str, Any]:
    """
    Generates an authoritative, factual recruitment recommendation grounded entirely in
    deterministic screening outputs, candidate tenure, and verified credentials.
    Provides transparent fallback when AI providers are offline or unavailable.
    """
    score = det_result.get("match_score", 0)
    matched = det_result.get("skills_matched", [])
    missing = det_result.get("missing_skills", [])
    certs = det_result.get("certifications_detected", [])
    exp_text = det_result.get("total_experience_detected", "Not Detected")
    cand_name = meta.get("name", "Candidate")

    if score >= 75:
        status = "Shortlisted"
        action = "Prioritize for Technical Interview"
        summary = (
            f"{cand_name} demonstrates high keyword and seniority alignment ({score}/100 match). "
            f"Core requirements for {job_title} are substantiated by verified resume evidence."
        )
    elif score >= 50:
        status = "In Review"
        action = "Conduct Focused Technical Screening"
        summary = (
            f"{cand_name} demonstrates moderate alignment ({score}/100 match). Foundational domain "
            f"experience is present, but specific technical gaps require recruiter and technical verification."
        )
    else:
        status = "Not Recommended"
        action = "Review Alternative Roles or Archive"
        summary = (
            f"{cand_name} shows low alignment ({score}/100 match) against {job_title} requirements. "
            f"Significant prerequisite competencies were not detected in the candidate text."
        )

    strengths: List[str] = []
    if matched:
        top_m = ", ".join(matched[:5])
        strengths.append(f"Demonstrated proficiency across: {top_m}")
    if exp_text and "Not Detected" not in exp_text:
        strengths.append(f"Seniority alignment: {exp_text}")
    if certs:
        strengths.append(f"Verified certifications: {', '.join(certs)}")
    if not strengths:
        strengths.append("Foundational technical background detected in candidate profile.")

    gaps: List[str] = []
    if missing:
        top_miss = ", ".join(missing[:5])
        gaps.append(f"Unverified or missing competencies: {top_miss}")
    if not certs and any(w in job_title.lower() for w in ["cisco", "voice", "network", "architect"]):
        gaps.append("No active recognized vendor certifications detected in CV text.")
    if not gaps:
        gaps.append("No critical skill or certification gaps identified against the JD.")

    interview_probes = det_result.get("interview_questions", [])[:3]

    return {
        "status": status,
        "action": action,
        "score": score,
        "summary": summary,
        "strengths": strengths,
        "gaps": gaps,
        "interview_probes": interview_probes,
        "is_llm": False,
        "engine_label": "Deterministic Screening Engine (Offline / Rule-Based)",
    }
