import json

import streamlit as st

from council import run_council

st.set_page_config(page_title="The Council — Mini LLM Council Dashboard", page_icon="⚖️", layout="wide")

ACCENTS = {
    "openai": "#3fb8af",
    "anthropic": "#b5566b",
    "google": "#5b8def",
    "groq": "#7fa65c",
}

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=IBM+Plex+Mono:wght@400;500&display=swap');

.stApp {
  background:
    radial-gradient(ellipse 900px 500px at 50% -10%, rgba(201,162,39,0.10), transparent 60%),
    #12151c;
  color: #ece6d6;
}

h1, h2, h3 { font-family: 'Fraunces', Georgia, serif !important; }

.council-eyebrow {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #c9a227;
}

.council-title {
  font-family: 'Fraunces', Georgia, serif;
  font-weight: 700;
  font-size: 3rem;
  margin: 4px 0 6px;
}

.council-tagline { color: #b9b3a1; margin-bottom: 24px; }

.panelist-card {
  background: #1b2030;
  border: 1px solid rgba(201,162,39,0.16);
  border-top: 3px solid var(--accent, #c9a227);
  border-radius: 10px;
  padding: 18px 20px;
  margin-bottom: 12px;
  min-height: 260px;
}

.panelist-name {
  font-family: 'Fraunces', Georgia, serif;
  font-weight: 600;
  font-size: 1.05rem;
  color: #ece6d6;
}

.badge {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.65rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid var(--accent, #c9a227);
  color: var(--accent, #c9a227);
  float: right;
}

.panelist-answer { color: #b9b3a1; font-size: 0.92rem; margin-top: 10px; white-space: pre-wrap; }
.panelist-answer.is-error { color: #d98080; font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; }

.suggestion {
  border-top: 1px dashed rgba(201,162,39,0.16);
  margin-top: 12px;
  padding-top: 10px;
  font-size: 0.84rem;
  color: #e4c55d;
  font-style: italic;
}

.suggestion-label {
  font-style: normal;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.65rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #8790a3;
  display: block;
  margin-bottom: 4px;
}

.verdict-box {
  border: 1px solid #c9a227;
  border-radius: 10px;
  padding: 28px;
  text-align: center;
  background: linear-gradient(180deg, rgba(201,162,39,0.08), transparent);
  margin-top: 20px;
}

.verdict-text { font-family: 'Fraunces', Georgia, serif; font-size: 1.2rem; color: #ece6d6; }
.verdict-by { font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; text-transform: uppercase; color: #8790a3; margin-top: 10px; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown('<p class="council-eyebrow">AI deliberation dashboard</p>', unsafe_allow_html=True)
st.markdown('<p class="council-title">The Council</p>', unsafe_allow_html=True)
st.markdown('<p class="council-tagline">Four models. One question. A verdict you can defend.</p>', unsafe_allow_html=True)

mode_label = st.radio(
    "Council mode",
    ["General brief", "UI / UX & design critique"],
    horizontal=True,
    label_visibility="collapsed",
)
mode = "uiux" if mode_label.startswith("UI") else "general"

placeholder = (
    "Critique the checkout flow of our e-commerce site: 3 steps, no guest checkout, cart icon top-right..."
    if mode == "uiux"
    else "Design a one-page product brochure for a tech startup"
)

question = st.text_area("State your question or paste a brief", placeholder=placeholder, height=120)

submitted = st.button("Convene the council", type="primary")

if "result" not in st.session_state:
    st.session_state["result"] = None

if submitted:
    if not question.strip():
        st.warning("Enter a question or brief first.")
    else:
        with st.spinner("The council is deliberating…"):
            st.session_state["result"] = run_council(question.strip(), mode)

result = st.session_state["result"]

if result:
    cols = st.columns(2)
    for i, r in enumerate(result["responses"]):
        accent = ACCENTS.get(r["provider"], "#c9a227")
        badge = "Demo mode" if r.get("demo") else ("Error" if r.get("error") else "Live")
        if r.get("error"):
            answer_html = f'<p class="panelist-answer is-error">Error: {r["error"]}</p>'
        else:
            answer_html = f'<p class="panelist-answer">{(r["answer"] or "").replace(chr(10), "<br>")}</p>'
        suggestion = result["suggestions"].get(r["provider"])
        suggestion_html = (
            f'<div class="suggestion"><span class="suggestion-label">Suggested refinement</span>{suggestion}</div>'
            if suggestion
            else ""
        )
        with cols[i % 2]:
            st.markdown(
                f"""
                <div class="panelist-card" style="--accent:{accent}">
                  <span class="badge" style="--accent:{accent}">{badge}</span>
                  <span class="panelist-name">{r['model']}</span>
                  {answer_html}
                  {suggestion_html}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        f"""
        <div class="verdict-box">
          <p class="council-eyebrow">The verdict</p>
          <p class="verdict-text">{result['verdict']}</p>
          <p class="verdict-by">Synthesized by {result['verdictBy']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("View raw JSON (for the assignment deliverable, or for other systems)"):
        st.json(result)
        st.download_button(
            "Download JSON",
            data=json.dumps(result, indent=2),
            file_name="council_response.json",
            mime="application/json",
        )

st.markdown("---")
st.markdown(
    "**Using this from other systems:** Streamlit Community Cloud only serves this "
    "interactive app, not a raw REST endpoint. For a JSON API other systems can call "
    "(`POST /api/council`), deploy the companion Netlify version, or run "
    "`api.py` in this repo locally/on any Python host — see `README.md`."
)
