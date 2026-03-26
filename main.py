from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ai_service import AIServiceError, get_ai_service


app = FastAPI(
    title="AI Resume Analyzer Bot API",
    version="1.0.0",
    description="Analyze and rewrite resumes against a job description.",
)


class AnalyzeRequest(BaseModel):
    jd: str = Field(..., min_length=20, description="Job description text")
    resume_text: str = Field(..., min_length=20, description="Resume content")


class RewriteRequest(BaseModel):
    jd: str = Field(..., min_length=20, description="Job description text")
    resume_text: str = Field(..., min_length=20, description="Resume content")
    template: str = Field(..., min_length=3, description="Selected resume template")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "AI Resume Analyzer Bot API is running.",
        "docs": "/docs",
        "health": "/health",
    }


@app.post("/analyze")
async def analyze_resume(payload: AnalyzeRequest) -> dict:
    try:
        service = get_ai_service()
        analysis = await service.analyze_resume(payload.jd, payload.resume_text)
        return {"analysis": analysis.to_dict()}
    except AIServiceError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/rewrite")
async def rewrite_resume(payload: RewriteRequest) -> dict:
    try:
        service = get_ai_service()
        improved_resume = await service.rewrite_resume(
            jd=payload.jd,
            resume_text=payload.resume_text,
            template=payload.template,
        )
        rescored = await service.analyze_resume(payload.jd, improved_resume)
        return {
            "improved_resume": improved_resume,
            "analysis": rescored.to_dict(),
        }
    except AIServiceError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
