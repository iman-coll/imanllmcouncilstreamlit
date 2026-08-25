from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

PANEL_ORDER = ["google", "groq"]

DEMO_LINES = {
    "google": "Demo mode — enter a Gemini API key in the sidebar to make this panelist live.",
    "groq": "Demo mode — enter a Groq API key in the sidebar to make this panelist live.",
}


def secret(name: str, default: str = "") -> str:
    try:
        import streamlit as st
        value = st.secrets.get(name, "")
        if value:
            return str(value)
    except Exception:
        pass
    return os.environ.get(name, default)


def demo(provider: str, model: str) -> dict:
    return {"provider": provider, "model": model, "answer": DEMO_LINES[provider], "error": None, "demo": True}


def call_google(question: str, system: str, api_key: str = "") -> dict:
    model = secret("GOOGLE_MODEL", "gemini-2.5-flash")
    key = str(api_key or secret("GOOGLE_API_KEY") or "").strip()
    if not key:
        return demo("google", f"Google · {model}")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": question}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 700},
        }
        response = requests.post(url, json=payload, timeout=45)
        data = response.json()
        response.raise_for_status()
        candidates = data.get("candidates") or []
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        answer = "".join(str(part.get("text", "")) for part in parts).strip()
        if not answer:
            raise RuntimeError("Gemini returned an empty response.")
        return {"provider": "google", "model": f"Google · {model}", "answer": answer, "error": None, "demo": False}
    except Exception as exc:
        return {"provider": "google", "model": f"Google · {model}", "answer": None, "error": f"Gemini: {exc}", "demo": False}


def call_groq(question: str, system: str, api_key: str = "") -> dict:
    model = secret("GROQ_MODEL", "openai/gpt-oss-120b")
    key = str(api_key or secret("GROQ_API_KEY") or "").strip()
    if not key:
        return demo("groq", f"Groq · {model}")
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": question}],
                "temperature": 0.7,
                "max_tokens": 700,
            },
            timeout=45,
        )
        data = response.json()
        response.raise_for_status()
        choices = data.get("choices") or []
        answer = choices[0].get("message", {}).get("content", "") if choices else ""
        answer = str(answer).strip()
        if not answer:
            raise RuntimeError("Groq returned an empty response.")
        return {"provider": "groq", "model": f"Groq · {model}", "answer": answer, "error": None, "demo": False}
    except Exception as exc:
        return {"provider": "groq", "model": f"Groq · {model}", "answer": None, "error": f"Groq: {exc}", "demo": False}


def run_council(question: str, mode: str = "general", google_key: str = "", groq_key: str = "") -> dict:
    question = str(question or "").strip()
    mode = str(mode or "general")
    system = (
        "You are a senior UI/UX reviewer. Critique usability, hierarchy, accessibility and clarity. "
        "Give 3-5 concrete recommendations in 120-180 words. Take a clear position."
        if mode == "uiux" else
        "You are a practical AI advisor. Give a clear, structured recommendation in 120-180 words. "
        "Take a clear position and include concrete next steps."
    )

    callers = {
        "google": lambda: call_google(question, system, google_key),
        "groq": lambda: call_groq(question, system, groq_key),
    }

    responses = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(fn): provider for provider, fn in callers.items()}
        for future in as_completed(futures):
            provider = futures[future]
            try:
                result = future.result()
            except Exception as exc:
                result = {"provider": provider, "model": provider.title(), "answer": None, "error": str(exc), "demo": False}
            responses.append(result)

    responses.sort(key=lambda item: PANEL_ORDER.index(item["provider"]))
    live = [r for r in responses if not r.get("demo") and not r.get("error") and r.get("answer")]

    suggestions = {}
    for item in responses:
        if item.get("error"):
            suggestions[item["provider"]] = "Check that the API key is valid and the selected model is available."
        elif item.get("demo"):
            suggestions[item["provider"]] = "Enter this provider's API key to replace the demo response with a live panelist."
        else:
            suggestions[item["provider"]] = "Strengthen the recommendation with a measurable outcome and one concrete next step."

    if live:
        verdict = "The council recommends combining the strongest concrete recommendation from each live panelist, prioritizing clarity, audience fit, and an explicit next action."
        verdict_by = "Council synthesis"
    else:
        verdict = "The council is ready in demo mode. Enter a Gemini or Groq API key in the sidebar to receive live AI deliberation."
        verdict_by = "Local demo synthesis"

    return {"question": question, "mode": mode, "responses": responses, "suggestions": suggestions, "verdict": verdict, "verdictBy": verdict_by}
