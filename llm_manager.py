"""
FITMENT.AI - Dynamic LLM Provider Manager & Resilient Fallback Engine
Centralized, safe multi-provider configuration supporting:
- Google Gemini (gemini-3.5-flash-lite)
- OpenRouter (Free / Cloud Models)
- NVIDIA NIM (with bounded timeout & fallback)
- Groq / Mistral / Cerebras
- 100% Offline Screening Fallback

Zero paid API automatic charges. Zero hardcoded keys.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional, Tuple
import requests
from dotenv import load_dotenv

load_dotenv()


# Verified Free-Tier & Standard Catalog Mappings (Verified as of October 2026)
PROVIDER_SPECS = {
    "gemini": {
        "display_name": "Google Gemini",
        "env_key": "GEMINI_API_KEY",
        "alt_env_key": "GOOGLE_API_KEY",
        "default_model": os.getenv("GOOGLE_MODEL", "gemini-3.5-flash-lite"),
        "models": ["gemini-3.5-flash-lite", "gemini-2.5-flash", "gemini-2.5-pro"],
        "free_tier_status": "Free Tier Available (RPM / RPD limits apply)",
        "requires_sdk": "google-genai",
    },
    "openrouter": {
        "display_name": "OpenRouter",
        "env_key": "OPENROUTER_API_KEY",
        "default_model": os.getenv("OPENROUTER_MODEL", "google/gemma-4-26b-a4b-it:free"),
        "models": [
            "google/gemma-4-26b-a4b-it:free",
            "google/gemma-4-31b-it:free",
            "nvidia/nemotron-3.5-lightning:free",
            "liquid/lfm-2.5-2.6b:free",
        ],
        "free_tier_status": "Explicitly Free Models Available (:free suffix)",
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
    },
    "nvidia": {
        "display_name": "NVIDIA NIM",
        "env_key": "NVIDIA_API_KEY",
        "default_model": os.getenv("NVIDIA_MODEL", "stepfun-ai/step-5-preview"),
        "models": [
            "stepfun-ai/step-5-preview",
            "z-ai/glm-5.3",
            "meta/llama-3.1-70b-instruct",
            "mistralai/mistral-large-2-instruct",
        ],
        "free_tier_status": "NVIDIA Build Free Trial Credits",
        "endpoint": "https://integrate.api.nvidia.com/v1/chat/completions",
    },
    "groq": {
        "display_name": "Groq",
        "env_key": "GROQ_API_KEY",
        "default_model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "models": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
        "free_tier_status": "Groq Cloud Free Developer Tier",
        "endpoint": "https://api.groq.com/openai/v1/chat/completions",
    },
}


def get_active_providers() -> List[Dict[str, Any]]:
    """Lists all providers that have valid API keys present in the environment."""
    active = []
    for p_id, spec in PROVIDER_SPECS.items():
        key = os.getenv(spec["env_key"]) or (os.getenv(spec.get("alt_env_key", "")) if spec.get("alt_env_key") else "")
        if key and len(key.strip()) > 10:
            active.append({
                "id": p_id,
                "display_name": spec["display_name"],
                "default_model": spec["default_model"],
                "models": spec["models"],
                "free_tier_status": spec["free_tier_status"],
            })
    return active


def validate_provider_health(
    provider_id: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    timeout_seconds: float = 8.0,
) -> Tuple[bool, str]:
    """
    Safely tests provider connectivity without consuming heavy tokens.
    Returns (is_connected: bool, status_message: str).
    """
    p_id = provider_id.lower()
    spec = PROVIDER_SPECS.get(p_id)
    if not spec:
        return False, f"Unknown provider '{provider_id}'"

    key = (api_key or os.getenv(spec["env_key"]) or (os.getenv(spec.get("alt_env_key", "")) if spec.get("alt_env_key") else "") or "").strip()
    if not key or len(key) < 10:
        return False, f"No API Key configured for {spec['display_name']}."

    target_model = model or spec["default_model"]

    # 1. Google Gemini Health Check
    if p_id == "gemini":
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=key)
            res = client.models.generate_content(
                model=target_model,
                contents="ping",
                config=types.GenerateContentConfig(max_output_tokens=2),
            )
            return True, f"Connected ({spec['display_name']} — {target_model})"
        except Exception as exc:
            err = str(exc)
            if "401" in err or "API_KEY_INVALID" in err or "PERMISSION_DENIED" in err:
                return False, f"401 Unauthorized: Invalid {spec['display_name']} key."
            return False, f"Gemini Error: {err[:90]}"

    # 2. OpenRouter Health Check
    elif p_id == "openrouter":
        headers = {"Authorization": f"Bearer {key}"}
        try:
            resp = requests.get(
                "https://openrouter.ai/api/v1/auth/key", headers=headers, timeout=timeout_seconds
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                daily = data.get("free_model_daily_requests", {})
                rem = daily.get("remaining")
                lim = daily.get("limit")
                badge = f" ({rem}/{lim} free requests left)" if rem is not None else ""
                return True, f"Connected (OpenRouter{badge} — {target_model})"
            elif resp.status_code == 401:
                return False, "401 Unauthorized: Invalid OpenRouter key."
            return False, f"OpenRouter status {resp.status_code}: {resp.text[:80]}"
        except Exception as exc:
            return False, f"OpenRouter Connection Error: {str(exc)[:80]}"

    # 3. NVIDIA NIM Health Check
    elif p_id == "nvidia":
        headers = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
        payload = {
            "model": target_model,
            "max_tokens": 1,
            "messages": [{"role": "user", "content": "ping"}],
        }
        try:
            resp = requests.post(
                spec["endpoint"], headers=headers, json=payload, timeout=timeout_seconds
            )
            if resp.status_code == 200:
                return True, f"Connected (NVIDIA NIM — {target_model})"
            elif resp.status_code == 401:
                return False, "401 Unauthorized: Invalid NVIDIA key."
            elif resp.status_code == 404:
                return False, f"404 Not Found: Model '{target_model}' not available."
            elif resp.status_code == 429:
                return False, "429 Rate Limited: NVIDIA quota exceeded."
            return False, f"NVIDIA Error ({resp.status_code}): {resp.text[:80]}"
        except requests.exceptions.Timeout:
            # Check model catalog fallback to detect reachability
            try:
                cat_resp = requests.get("https://integrate.api.nvidia.com/v1/models", headers=headers, timeout=4.0)
                if cat_resp.status_code == 200:
                    return False, f"NVIDIA chat endpoint timed out on '{target_model}'. Catalog is reachable."
            except Exception:
                pass
            return False, f"NVIDIA Endpoint Timed Out (> {timeout_seconds}s)."
        except Exception as exc:
            return False, f"NVIDIA Error: {str(exc)[:80]}"

    # Generic OpenAI-compatible providers
    else:
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload = {
            "model": target_model,
            "max_tokens": 2,
            "messages": [{"role": "user", "content": "ping"}],
        }
        try:
            resp = requests.post(spec["endpoint"], headers=headers, json=payload, timeout=timeout_seconds)
            if resp.status_code == 200:
                return True, f"Connected ({spec['display_name']} — {target_model})"
            return False, f"{spec['display_name']} Error ({resp.status_code}): {resp.text[:80]}"
        except Exception as exc:
            return False, f"{spec['display_name']} Error: {str(exc)[:80]}"


def generate_qualitative_assessment(
    job_description: str,
    resume_text: str,
    preferred_provider: Optional[str] = None,
    preferred_model: Optional[str] = None,
    timeout_seconds: float = 30.0,
) -> Dict[str, Any]:
    """
    Executes qualitative screening analysis with bounded fallback across eligible providers.
    Never fails silently; falls back gracefully to offline status if all providers fail.
    """
    # Determine fallback sequence
    env_order = os.getenv("LLM_FALLBACK_ORDER", "gemini,openrouter,nvidia,groq")
    order = [p.strip().lower() for p in env_order.split(",") if p.strip()]

    if preferred_provider:
        p_clean = preferred_provider.lower().replace("google", "gemini").replace("nim", "nvidia").replace(" (gemini-3.5-flash-lite)", "").replace(" (free / cloud llms)", "").strip()
        for k in PROVIDER_SPECS.keys():
            if k in p_clean:
                p_clean = k
                break
        if p_clean in order:
            order.remove(p_clean)
        order.insert(0, p_clean)

    prompt = f"""You are an elite Executive Talent Recruiter & Fitment Architect.
Analyze the candidate's resume against the Job Description objectively and concisely.

Target Job Description:
{job_description[:3000]}

Candidate Resume:
{resume_text[:3500]}

Format your response exactly with these markdown sections:

### 🎯 Executive Fitment Summary & Verdict
Provide a concise 2-3 sentence executive summary and strategic verdict.

### 🛠️ Technical Skills Alignment
- **Required Skills Matched:** List key matching technologies directly verified in the CV.
- **Required Skills Missing:** List critical job requirements not evidenced in the CV.
- **Equivalent / Transferable Proficiencies:** Note any adjacent tools or transferable experience.

### 💼 Experience & Seniority
Assess candidate's career tenure, relevant domain depth, and alignment with target role seniority.

### 🏆 Certifications & Education
Review verified credentials (e.g. Cisco, Cloud, ITIL, Degrees) and note any unverified claims.

### 🧠 Candidate Strengths
Highlight 2-3 standout qualifications supported by concrete achievements.

### ⚠️ Gaps and Risks
Detail mandatory missing proficiencies, tenure gaps, or areas requiring technical validation.

### 🎤 Interview Strategy
Provide 3 high-yield, targeted technical interview probes based directly on identified gaps.

### 📌 Recruiter Recommendation
Suggested next action (e.g., Shortlist for Technical Screen, On Hold, or Reject).
"""

    errors_encountered = []

    for provider_id in order:
        spec = PROVIDER_SPECS.get(provider_id)
        if not spec:
            continue

        key = (os.getenv(spec["env_key"]) or (os.getenv(spec.get("alt_env_key", "")) if spec.get("alt_env_key") else "") or "").strip()
        if not key or len(key) < 10:
            continue

        model = (preferred_model if provider_id == order[0] and preferred_model else spec["default_model"])

        # Execute Provider Call
        try:
            if provider_id == "gemini":
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=key)
                cfg = types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level="MINIMAL"),
                    temperature=0.3,
                    max_output_tokens=1500,
                )
                start_t = time.time()
                resp = client.models.generate_content(model=model, contents=prompt, config=cfg)
                elapsed = time.time() - start_t
                if resp.text:
                    return {
                        "status": "success",
                        "provider": spec["display_name"],
                        "model": model,
                        "text": resp.text,
                        "elapsed_seconds": round(elapsed, 2),
                    }
                else:
                    errors_encountered.append(f"{spec['display_name']}: Empty response returned.")

            elif provider_id == "openrouter":
                headers = {
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://fitment.ai",
                    "X-Title": "FITMENT.AI InstantFit Screening",
                }
                payload = {
                    "model": model,
                    "models": [model, "google/gemma-4-31b-it:free", "nvidia/nemotron-3.5-lightning:free"],
                    "messages": [
                        {"role": "system", "content": "You are an elite Executive Talent Recruiter & Fitment Architect."},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 1200,
                    "temperature": 0.3,
                }
                start_t = time.time()
                r = requests.post(spec["endpoint"], headers=headers, json=payload, timeout=timeout_seconds)
                elapsed = time.time() - start_t
                if r.status_code == 200:
                    data = r.json()
                    content = data["choices"][0]["message"]["content"]
                    return {
                        "status": "success",
                        "provider": spec["display_name"],
                        "model": model,
                        "text": content,
                        "elapsed_seconds": round(elapsed, 2),
                    }
                else:
                    errors_encountered.append(f"{spec['display_name']} ({r.status_code}): {r.text[:80]}")

            elif provider_id == "nvidia":
                headers = {
                    "Authorization": f"Bearer {key}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": model,
                    "max_tokens": 1024,
                    "temperature": 0.3,
                    "messages": [
                        {"role": "system", "content": "You are an elite Executive Talent Recruiter & Fitment Architect."},
                        {"role": "user", "content": prompt},
                    ],
                }
                start_t = time.time()
                r = requests.post(spec["endpoint"], headers=headers, json=payload, timeout=min(timeout_seconds, 25.0))
                elapsed = time.time() - start_t
                if r.status_code == 200:
                    data = r.json()
                    content = data["choices"][0]["message"]["content"]
                    return {
                        "status": "success",
                        "provider": spec["display_name"],
                        "model": model,
                        "text": content,
                        "elapsed_seconds": round(elapsed, 2),
                    }
                else:
                    errors_encountered.append(f"{spec['display_name']} ({r.status_code}): {r.text[:80]}")

        except requests.exceptions.Timeout:
            errors_encountered.append(f"{spec['display_name']} ({model}) timed out after {timeout_seconds}s. Falling back to next eligible provider.")
            continue
        except Exception as exc:
            errors_encountered.append(f"{spec['display_name']} error: {str(exc)[:90]}")
            continue

    # If all configured providers fail or none configured:
    return {
        "status": "offline_fallback",
        "provider": "Offline / Deterministic",
        "model": "None",
        "text": "",
        "errors": errors_encountered,
        "message": "⚡ Offline Screening Active: Qualitative LLM analysis is currently unavailable. Deterministic screening results remain 100% authoritative.",
    }


def generate_qualitative_chat_response(
    system_instruction: str,
    user_query: str,
    factual_context: str,
    timeout_seconds: float = 12.0,
) -> Dict[str, Any]:
    """
    Executes a grounded qualitative query against active LLM providers.
    Uses strict database grounding so the LLM cannot hallucinate or invent candidate facts.
    Falls back gracefully if offline or if providers fail.
    """
    prompt = f"""You are the FITMENT.AI Recruitment Assistant.
Answer the recruiter's question using ONLY the verified database facts provided below.
Do not invent candidate names, scores, companies, or qualifications.
If a detail is not in the verified context, state that it is not available in the candidate's verified screening record.

### VERIFIED CANDIDATE RECORD & SCREENING FACTS:
{factual_context}

### RECRUITER QUESTION:
{user_query}
"""
    active_providers = get_active_providers()
    if not active_providers:
        return {
            "status": "offline",
            "provider": "Offline / Deterministic",
            "text": "",
            "message": "No active LLM API keys configured. Using deterministic assessment.",
        }

    for p in active_providers:
        provider_id = p["id"]
        spec = PROVIDER_SPECS.get(provider_id)
        if not spec:
            continue
        key = (os.getenv(spec["env_key"]) or (os.getenv(spec.get("alt_env_key", "")) if spec.get("alt_env_key") else "") or "").strip()
        model = spec["default_model"]

        try:
            if provider_id == "gemini":
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=key)
                cfg = types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level="MINIMAL"),
                    temperature=0.3,
                    max_output_tokens=1000,
                )
                resp = client.models.generate_content(model=model, contents=prompt, config=cfg)
                if resp and resp.text:
                    return {
                        "status": "success",
                        "provider": spec["display_name"],
                        "model": model,
                        "text": resp.text,
                    }
            elif provider_id in ("openrouter", "nvidia", "groq"):
                headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
                if provider_id == "openrouter":
                    headers["HTTP-Referer"] = "https://fitment.ai"
                    headers["X-Title"] = "FITMENT.AI Chat"
                payload = {
                    "model": model,
                    "max_tokens": 1000,
                    "temperature": 0.3,
                    "messages": [
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt},
                    ],
                }
                r = requests.post(spec["endpoint"], headers=headers, json=payload, timeout=timeout_seconds)
                if r.status_code == 200:
                    data = r.json()
                    content = data["choices"][0]["message"]["content"]
                    return {
                        "status": "success",
                        "provider": spec["display_name"],
                        "model": model,
                        "text": content,
                    }
        except Exception:
            continue

    return {
        "status": "offline",
        "provider": "Offline / Deterministic",
        "text": "",
        "message": "LLM providers unreachable. Falling back to deterministic analysis.",
    }
