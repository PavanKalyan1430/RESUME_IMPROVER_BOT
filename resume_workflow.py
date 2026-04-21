from __future__ import annotations

import httpx
import os


# HF Spaces expose PORT=7860, local testing uses 8000 by default
PORT = os.getenv("PORT", "7860")
API_BASE_URL = os.getenv("API_BASE_URL", f"http://127.0.0.1:{PORT}")
TEMPLATE_DESCRIPTIONS = {
    "ATS Resume": "clean single-column layout for ATS-friendly submissions",
    "Modern Resume": "professional layout with a fresh accent color",
    "Creative Resume": "bolder presentation with a more expressive header",
}


async def call_analyze_api(jd: str, resume_text: str) -> dict:
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/analyze",
            json={"jd": jd, "resume_text": resume_text},
        )
    response.raise_for_status()
    return response.json()["analysis"]


async def call_rewrite_api(jd: str, resume_text: str, template: str) -> dict:
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/rewrite",
            json={"jd": jd, "resume_text": resume_text, "template": template},
        )
    response.raise_for_status()
    return response.json()


def format_initial_analysis(analysis: dict) -> str:
    suggestions = analysis.get("suggestions", [])
    missing_skills = analysis.get("missing_skills", [])
    strengths = analysis.get("strengths", [])
    weaknesses = analysis.get("weaknesses", [])

    lines = [
        "Initial Response",
        f"Score: {analysis.get('score', 0)}/10",
        f"Match: {analysis.get('match_percentage', 0)}%",
        "Missing Skills: " + (", ".join(missing_skills) if missing_skills else "None"),
        "Suggestions:",
    ]
    lines.extend(f"- {item}" for item in suggestions[:6] or ["No major suggestions returned."])
    if strengths:
        lines.append("")
        lines.append("Strengths:")
        lines.extend(f"- {item}" for item in strengths[:5])
    if weaknesses:
        lines.append("")
        lines.append("Weaknesses:")
        lines.extend(f"- {item}" for item in weaknesses[:5])
    return "\n".join(lines)


def format_final_response(old_score: float, new_score: float, improvement: float) -> str:
    sign = "+" if improvement >= 0 else ""
    return (
        "Final Response\n"
        f"Old Score: {old_score}/10\n"
        f"New Score: {new_score}/10\n"
        f"Improvement: {sign}{improvement}"
    )


def format_template_options() -> str:
    lines = ["Choose how the corrected CV should look in the final PDF:"]
    for theme_name, description in TEMPLATE_DESCRIPTIONS.items():
        lines.append(f"- {theme_name}: {description}")
    return "\n".join(lines)
