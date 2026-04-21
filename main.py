from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ai_service import AIServiceError, get_ai_service

logger = logging.getLogger(__name__)

async def keep_awake_task():
    """Background task to self-ping the Hugging Face Space to prevent it from sleeping."""
    space_host = os.getenv("SPACE_HOST")
    if not space_host:
        logger.info("SPACE_HOST not found. Self-ping disabled.")
        return
    
    url = f"https://{space_host}/health"
    logger.info(f"Starting self-ping task for {url}")
    
    async with httpx.AsyncClient() as client:
        while True:
            await asyncio.sleep(600)  # Wait 10 minutes
            try:
                await client.get(url, timeout=10.0)
                logger.info("Self-ping successful - kept container awake.")
            except Exception as e:
                logger.warning(f"Self-ping failed: {e}")

from bot import build_application

# Native Telegram integration
telegram_app = build_application()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Keep awake task
    task = asyncio.create_task(keep_awake_task())
    
    # GUARANTEED NATIVE BOOT: Start Telegram bot inside the FastAPI event loop
    logger.info("Initializing Telegram Bot natively...")
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()
    logger.info("Telegram Bot is polling successfully!")
    
    yield
    
    # Shutdown
    if not task.done():
        task.cancel()
    if telegram_app.updater:
        await telegram_app.updater.stop()
    await telegram_app.stop()
    await telegram_app.shutdown()


app = FastAPI(
    title="AI Resume Analyzer Bot API",
    version="1.0.0",
    description="Analyze and rewrite resumes against a job description.",
    lifespan=lifespan,
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
        improved_resume, changes_made = await service.rewrite_resume(
            jd=payload.jd,
            resume_text=payload.resume_text,
            template=payload.template,
        )
        rescored = await service.analyze_resume(payload.jd, improved_resume)
        return {
            "improved_resume": improved_resume,
            "changes_made": changes_made,
            "analysis": rescored.to_dict(),
        }
    except AIServiceError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
