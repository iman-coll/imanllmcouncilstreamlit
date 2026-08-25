# The Council — Mini LLM Council Dashboard (Streamlit version)

Streamlit version of the LLM Council dashboard. It sends one question to four LLM panelists, shows their answers and suggested refinements, and produces a synthesized verdict.

## Streamlit Community Cloud

Deploy with:

- Repository: `iman-coll/imanllmcouncilstreamlit`
- Branch: `main`
- Main file: `app.py`

The app works in demo mode without API keys. Add provider keys under **App settings → Secrets** to enable live responses.

Example:

```toml
OPENAI_API_KEY = ""
ANTHROPIC_API_KEY = ""
GOOGLE_API_KEY = ""
GROQ_API_KEY = ""
```

See `.streamlit/secrets.toml.example` for model settings.

## Local run

```bash
pip install -r requirements.txt
streamlit run app.py
```

The optional `api.py` provides a FastAPI `/api/council` endpoint when run on a normal Python host.
