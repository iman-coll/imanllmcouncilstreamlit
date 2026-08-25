from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from council import run_council

app = FastAPI(title="The Council API", description="Ask four LLMs one question, get suggestions and a verdict.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class CouncilRequest(BaseModel):
    question: str
    mode: str = "general"

@app.get("/api/council")
def council_docs():
    return {"name":"The Council API", "usage":{"method":"POST","endpoint":"/api/council"}}

@app.post("/api/council")
def council(req: CouncilRequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Missing required field: question")
    mode = req.mode if req.mode in ("general", "uiux") else "general"
    return run_council(question, mode)
