from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from mistralai import Mistral
from dotenv import load_dotenv


load_dotenv()


class AIServiceError(Exception):
    """Raised when the Mistral service call fails or returns invalid data."""


@dataclass
class AnalysisResult:
    score: float
    match_percentage: int
    missing_skills: list[str]
    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]
    missing_keywords: list[str]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "match_percentage": self.match_percentage,
            "missing_skills": self.missing_skills,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "suggestions": self.suggestions,
            "missing_keywords": self.missing_keywords,
            "summary": self.summary,
        }


class MistralResumeService:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        self.model = model or os.getenv("MISTRAL_MODEL", "mistral-small-latest")
        if not self.api_key:
            raise AIServiceError("MISTRAL_API_KEY is not configured.")
        self.client = Mistral(api_key=self.api_key)

    async def analyze_resume(self, jd: str, resume_text: str) -> AnalysisResult:
        prompt = self._build_analysis_prompt(jd=jd, resume_text=resume_text)
        data = await self._request_json(prompt)
        return self._parse_analysis_result(data)

    async def rewrite_resume(self, jd: str, resume_text: str, template: str) -> tuple[str, list[str]]:
        prompt = self._build_rewrite_prompt(jd=jd, resume_text=resume_text, template=template)
        data = await self._request_json(prompt)

        improved_resume = str(data.get("improved_resume", "")).strip()
        changes_made = data.get("changes_made", [])
        if not isinstance(changes_made, list):
            changes_made = []
        changes_made = [str(c) for c in changes_made if str(c).strip()]
        
        if not improved_resume:
            raise AIServiceError("Mistral did not return an improved resume.")
        return improved_resume, changes_made

    async def _request_json(self, prompt: str) -> dict[str, Any]:
        try:
            response = await self.client.chat.complete_async(
                model=self.model,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert ATS resume analyst and resume writer. "
                            "Always return valid JSON only."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
        except Exception as exc:  # pragma: no cover - network/API failure path
            raise AIServiceError(f"Mistral request failed: {exc}") from exc

        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise AIServiceError("Mistral returned an empty response.")

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise AIServiceError("Mistral returned invalid JSON.") from exc

    def _parse_analysis_result(self, data: dict[str, Any]) -> AnalysisResult:
        def as_string_list(value: Any) -> list[str]:
            if not isinstance(value, list):
                return []
            return [str(item).strip() for item in value if str(item).strip()]

        score = round(float(data.get("score", 0)), 1)
        match_percentage = int(data.get("match_percentage", 0))
        return AnalysisResult(
            score=max(0.0, min(score, 10.0)),
            match_percentage=max(0, min(match_percentage, 100)),
            missing_skills=as_string_list(data.get("missing_skills")),
            strengths=as_string_list(data.get("strengths")),
            weaknesses=as_string_list(data.get("weaknesses")),
            suggestions=as_string_list(data.get("suggestions")),
            missing_keywords=as_string_list(data.get("missing_keywords")),
            summary=str(data.get("summary", "")).strip(),
        )

    def _build_analysis_prompt(self, jd: str, resume_text: str) -> str:
        return f"""
Analyze the resume against the job description and return JSON with this exact schema:
{{
  "score": 0-10 number,
  "match_percentage": 0-100 integer,
  "missing_skills": ["skill"],
  "strengths": ["point"],
  "weaknesses": ["point"],
  "suggestions": ["point"],
  "missing_keywords": ["keyword"],
  "summary": "short summary"
}}

Rules:
- Be strict but fair.
- Do not invent resume experience, projects, or qualifications.
- Missing skills must reflect the JD and not generic filler.
- Suggestions must be actionable and ATS-focused.
- Score should reflect how well the resume matches the JD today.

Job Description:
{jd}

Resume:
{resume_text}
""".strip()

    def _build_rewrite_prompt(self, jd: str, resume_text: str, template: str) -> str:
        return f"""
Rewrite the resume to better match the job description using the "{template}" template style.
Return JSON with this exact schema:
{{
  "improved_resume": "full rewritten resume in plain text",
  "changes_made": ["bullet point describing a specific change you made", "another specific change"]
}}

Rules:
- Keep the candidate truthful. Do not invent jobs, degrees, certifications, metrics, or technical skills.
- Improve structure, wording, relevance, keyword alignment, and ATS readability.
- IMPORTANT: Use space cleverly to fill exactly one full page. Do not aggressively cut off the Education or Experience sections. Provide detailed, strong bullet points.
- Only trim older, irrelevant jobs or minor details if absolutely necessary to prevent the text from spilling onto a second page. Ensure the resume looks complete and well-rounded.
- Make the output clean, readable, and ready to paste into a resume editor.
- Include these sections when supported by the source material: Summary, Skills, Experience, Projects, Education.
- Emphasize JD keywords only when they are legitimately supported by the original resume.
- Use strong bullet points and concise professional language.

Job Description:
{jd}

Original Resume:
{resume_text}
""".strip()


_service: MistralResumeService | None = None


def get_ai_service() -> MistralResumeService:
    global _service
    if _service is None:
        _service = MistralResumeService()
    return _service
