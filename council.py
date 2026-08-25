from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

PANEL_ORDER = ["openai", "anthropic", "google", "groq"]

DEMO_LINES = {
    "openai": "Demo mode — add an OPENAI_API_KEY to hear from this panelist. Focus the brief on one clear audience, one clear action, and remove anything that does not serve either.",
    "anthropic": "Demo mode — add an ANTHROPIC_API_KEY to hear from this panelist. Lead with the strongest proof point, keep the structure scannable, and make the next step obvious.",
    "google": "Demo mode — enter a Gemini API key in the sidebar to make this panelist live.",
    "groq": "Demo mode — enter a Groq API key in the sidebar to make this panelist live.",
}


def secret(name, default="", runtime_key=""):
    if runtime_key:
        return runtime_key
    try:
        import streamlit as st
        if name in st.secrets and st.secrets[name]:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.environ.get(name, default)


def demo(provider, model):
    return {"provider": provider, "model": model, "answer": DEMO_LINES[provider], "error": None, "demo": True}


def call_openai(q, system):
    model = secret("OPENAI_MODEL", "gpt-4o-mini")
    key = secret("OPENAI_API_KEY")
    if not key: return demo("openai", f"OpenAI · {model}")
    try:
        r = requests.post("https://api.openai.com/v1/chat/completions", headers={"Authorization": f"Bearer {key}"}, json={"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": q}], "temperature": 0.7, "max_tokens": 500}, timeout=45)
        d = r.json(); r.raise_for_status()
        return {"provider": "openai", "model": f"OpenAI · {model}", "answer": d["choices"][0]["message"]["content"].strip(), "error": None, "demo": False}
    except Exception as e: return {"provider": "openai", "model": f"OpenAI · {model}", "answer": None, "error": str(e), "demo": False}


def call_anthropic(q, system):
    model = secret("ANTHROPIC_MODEL", "claude-sonnet-5"); key = secret("ANTHROPIC_API_KEY")
    if not key: return demo("anthropic", f"Anthropic · {model}")
    try:
        r = requests.post("https://api.anthropic.com/v1/messages", headers={"x-api-key": key, "anthropic-version": "2023-06-01"}, json={"model": model, "system": system, "max_tokens": 500, "messages": [{"role": "user", "content": q}]}, timeout=45)
        d = r.json(); r.raise_for_status()
        return {"provider": "anthropic", "model": f"Anthropic · {model}", "answer": d["content"][0]["text"].strip(), "error": None, "demo": False}
    except Exception as e: return {"provider": "anthropic", "model": f"Anthropic · {model}", "answer": None, "error": str(e), "demo": False}


def call_google(q, system, runtime_key=""):
    model = secret("GOOGLE_MODEL", "gemini-2.5-flash")
    key = secret("GOOGLE_API_KEY", runtime_key=runtime_key)
    if not key: return demo("google", f"Google · {model}")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        r = requests.post(url, json={"contents": [{"parts": [{"text": q}]}], "systemInstruction": {"parts": [{"text": system}]}, "generationConfig": {"maxOutputTokens": 500, "temperature": 0.7}}, timeout=45)
        d = r.json(); r.raise_for_status()
        parts = d.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        answer = "".join(x.get("text", "") for x in parts).strip()
        if not answer: raise RuntimeError("Empty response")
        return {"provider": "google", "model": f"Google · {model}", "answer": answer, "error": None, "demo": False}
    except Exception as e: return {"provider": "google", "model": f"Google · {model}", "answer": None, "error": str(e), "demo": False}


def call_groq(q, system, runtime_key=""):
    model = secret("GROQ_MODEL", "openai/gpt-oss-120b")
    key = secret("GROQ_API_KEY", runtime_key=runtime_key)
    if not key: return demo("groq", f"Groq · {model}")
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {key}"}, json={"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": q}], "temperature": 0.7, "max_tokens": 500}, timeout=45)
        d = r.json(); r.raise_for_status()
        return {"provider": "groq", "model": f"Groq · {model}", "answer": d["choices"][0]["message"]["content"].strip(), "error": None, "demo": False}
    except Exception as e: return {"provider": "groq", "model": f"Groq · {model}", "answer": None, "error": str(e), "demo": False}


def run_council(question, mode="general", google_key="", groq_key=""):
    system = ("You are a practical AI advisor. Give a clear, structured recommendation in 120-180 words. Take a position." if mode == "general" else "You are a senior UI/UX reviewer. Critique usability, hierarchy, accessibility and clarity. Give 3-5 concrete recommendations in 120-180 words.")

    callers = {
        "openai": lambda: call_openai(question, system),
        "anthropic": lambda: call_anthropic(question, system),
        "google": lambda: call_google(question, system, google_key),
        "groq": lambda: call_groq(question, system, groq_key),
    }

    responses = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        jobs = {ex.submit(callers[p]): p for p in PANEL_ORDER}
        for job in as_completed(jobs):
            responses.append(job.result())
    responses.sort(key=lambda x: PANEL_ORDER.index(x["provider"]))

    live = [r for r in responses if not r.get("demo") and not r.get("error")]
    suggestions = {r["provider"]: ("Strengthen the recommendation with a measurable outcome and one concrete next step." if not r.get("demo") else "Add the provider API key to replace this demo response with a live panelist.") for r in responses}

    if live:
        verdict = "The council recommends combining the strongest concrete recommendation from each live panelist, prioritizing clarity, audience fit, and an explicit next action."
        verdict_by = "Council synthesis"
    else:
        verdict = "The council is ready in demo mode. Enter a Gemini or Groq API key in the sidebar to receive live AI deliberation."
        verdict_by = "Local demo synthesis"

    return {"question": question, "mode": mode, "responses": responses, "suggestions": suggestions, "verdict": verdict, "verdictBy": verdict_by}
