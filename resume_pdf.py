from __future__ import annotations

import io
import re
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, StyleSheet1, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


SECTION_HEADINGS = {
    "summary",
    "professional summary",
    "skills",
    "technical skills",
    "experience",
    "professional experience",
    "work experience",
    "projects",
    "education",
    "certifications",
    "achievements",
}


@dataclass(frozen=True)
class ResumeTheme:
    name: str
    top_band_color: colors.Color
    heading_color: colors.Color
    accent_color: colors.Color
    body_text_color: colors.Color
    title_alignment: int
    heading_font: str
    body_font: str


THEMES = {
    "ATS Resume": ResumeTheme(
        name="ATS Resume",
        top_band_color=colors.HexColor("#1F2937"),
        heading_color=colors.HexColor("#111827"),
        accent_color=colors.HexColor("#D1D5DB"),
        body_text_color=colors.HexColor("#111827"),
        title_alignment=TA_LEFT,
        heading_font="Helvetica-Bold",
        body_font="Helvetica",
    ),
    "Modern Resume": ResumeTheme(
        name="Modern Resume",
        top_band_color=colors.HexColor("#0F766E"),
        heading_color=colors.HexColor("#134E4A"),
        accent_color=colors.HexColor("#99F6E4"),
        body_text_color=colors.HexColor("#0F172A"),
        title_alignment=TA_LEFT,
        heading_font="Helvetica-Bold",
        body_font="Helvetica",
    ),
    "Creative Resume": ResumeTheme(
        name="Creative Resume",
        top_band_color=colors.HexColor("#C2410C"),
        heading_color=colors.HexColor("#9A3412"),
        accent_color=colors.HexColor("#FDBA74"),
        body_text_color=colors.HexColor("#431407"),
        title_alignment=TA_CENTER,
        heading_font="Helvetica-Bold",
        body_font="Helvetica",
    ),
}


def build_resume_pdf(resume_text: str, template: str, source_filename: str | None = None) -> tuple[bytes, str]:
    theme = THEMES.get(template, THEMES["ATS Resume"])
    sections = _parse_resume_sections(resume_text)
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.6 * inch,
    )
    styles = _build_styles(theme)
    story = _build_story(sections, styles)
    doc.build(story, onFirstPage=lambda canvas, _: _draw_page_frame(canvas, doc, theme))

    return buffer.getvalue(), _make_output_filename(source_filename)


def _draw_page_frame(canvas, doc, theme: ResumeTheme) -> None:
    page_width, page_height = LETTER
    canvas.saveState()
    canvas.setFillColor(theme.top_band_color)
    canvas.rect(0, page_height - 0.42 * inch, page_width, 0.42 * inch, fill=1, stroke=0)
    canvas.setStrokeColor(theme.accent_color)
    canvas.setLineWidth(2)
    canvas.line(doc.leftMargin, page_height - 0.52 * inch, page_width - doc.rightMargin, page_height - 0.52 * inch)
    canvas.restoreState()


def _build_story(sections: list[tuple[str | None, list[str]]], styles: StyleSheet1) -> list:
    story: list = []

    if not sections:
        story.append(Paragraph("Resume", styles["resume_title"]))
        story.append(Spacer(1, 0.18 * inch))
        return story

    first_heading, first_lines = sections[0]
    if first_heading is None and first_lines:
        identity_lines = first_lines[:3]
        body_lines = first_lines[3:]
        story.append(Paragraph(_escape(identity_lines[0]), styles["resume_title"]))
        if len(identity_lines) > 1:
            story.append(Paragraph(_escape(" | ".join(identity_lines[1:])), styles["resume_subtitle"]))
        story.append(Spacer(1, 0.18 * inch))
        if body_lines:
            sections = [(None, body_lines), *sections[1:]]
        else:
            sections = sections[1:]

    for heading, lines in sections:
        if heading:
            story.append(Paragraph(_escape(heading.upper()), styles["section_heading"]))
            story.append(Spacer(1, 0.06 * inch))

        for line in lines:
            if _is_bullet(line):
                story.append(Paragraph(_bullet_html(line), styles["resume_bullet"]))
            else:
                style_name = "resume_body"
                if heading and "skills" in heading.lower():
                    style_name = "skills_body"
                story.append(Paragraph(_escape(line), styles[style_name]))
        story.append(Spacer(1, 0.12 * inch))

    return story


def _build_styles(theme: ResumeTheme) -> StyleSheet1:
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="resume_title",
            parent=styles["Title"],
            fontName=theme.heading_font,
            fontSize=20,
            leading=24,
            textColor=theme.heading_color,
            alignment=theme.title_alignment,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="resume_subtitle",
            parent=styles["BodyText"],
            fontName=theme.body_font,
            fontSize=10.5,
            leading=13,
            textColor=theme.body_text_color,
            alignment=theme.title_alignment,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="section_heading",
            parent=styles["Heading2"],
            fontName=theme.heading_font,
            fontSize=11.5,
            leading=14,
            textColor=theme.heading_color,
            borderPadding=0,
            borderWidth=0,
            backColor=theme.accent_color,
            leftIndent=0,
            rightIndent=0,
            spaceBefore=8,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="resume_body",
            parent=styles["BodyText"],
            fontName=theme.body_font,
            fontSize=10,
            leading=13,
            textColor=theme.body_text_color,
            alignment=TA_LEFT,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="skills_body",
            parent=styles["BodyText"],
            fontName=theme.body_font,
            fontSize=10,
            leading=13,
            textColor=theme.body_text_color,
            alignment=TA_LEFT,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="resume_bullet",
            parent=styles["BodyText"],
            fontName=theme.body_font,
            fontSize=10,
            leading=13,
            textColor=theme.body_text_color,
            leftIndent=14,
            firstLineIndent=0,
            bulletIndent=0,
            spaceAfter=4,
        )
    )
    return styles


def _parse_resume_sections(resume_text: str) -> list[tuple[str | None, list[str]]]:
    sections: list[tuple[str | None, list[str]]] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    for raw_line in resume_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if _is_section_heading(line):
            if current_lines:
                sections.append((current_heading, current_lines))
            current_heading = _normalize_heading(line)
            current_lines = []
            continue

        current_lines.append(line)

    if current_lines:
        sections.append((current_heading, current_lines))

    return sections


def _is_section_heading(line: str) -> bool:
    normalized = _normalize_heading(line)
    if normalized.lower() in SECTION_HEADINGS:
        return True
    return line.isupper() and 2 <= len(normalized.split()) <= 4


def _normalize_heading(line: str) -> str:
    return re.sub(r"[:\-\s]+$", "", line).strip()


def _is_bullet(line: str) -> bool:
    return bool(re.match(r"^([-\u2022*]|[0-9]+\.)\s+", line))


def _bullet_html(line: str) -> str:
    text = re.sub(r"^([-\u2022*]|[0-9]+\.)\s+", "", line, count=1).strip()
    return f'&bull;&nbsp;&nbsp;{_escape(text)}'


def _escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _make_output_filename(source_filename: str | None) -> str:
    if source_filename:
        stem = Path(source_filename).stem.strip()
        if stem:
            return f"{stem}_improved.pdf"
    return "improved_resume.pdf"
