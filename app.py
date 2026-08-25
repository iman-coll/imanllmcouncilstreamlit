import streamlit as st

from council import run_council

st.set_page_config(page_title="LLM Council", page_icon="🤖", layout="wide")

st.title("🤖 LLM Council")
st.caption("Ask a question and let multiple AI models independently reason, critique, and synthesize an answer.")

with st.sidebar:
    st.header("Council Settings")
    st.info("Add provider API keys in Streamlit secrets for live model responses. Without keys, the app can use its demo/fallback behavior.")

question = st.text_area("Your question", placeholder="Ask the council anything…", height=150)

if st.button("Run Council", type="primary", use_container_width=True):
    if not question.strip():
        st.warning("Please enter a question first.")
    else:
        with st.spinner("The council is working…"):
            try:
                result = run_council(question.strip())
                if isinstance(result, dict):
                    for key, value in result.items():
                        st.subheader(str(key).replace("_", " ").title())
                        st.write(value)
                else:
                    st.write(result)
            except Exception as exc:
                st.error(f"Council error: {exc}")
