---
title: Resume Bot
emoji: 🤖
colorFrom: indigo
colorTo: blue
sdk: docker
pinned: false
---

# 📄 AI Resume Enhancer Bot

> **Mathematical JD matching. AI-driven rewriting. Pixel-perfect ATS PDF Generation.**

---

## 📌 Table of Contents

1. [Project Summary](#1-project-summary)
2. [Key Features](#2-key-features)
3. [Tech Stack](#3-tech-stack)
4. [System Architecture](#4-system-architecture)
5. [Project Structure](#5-project-structure)
6. [Detailed Component Breakdown](#6-detailed-component-breakdown)
   - [Backend (FastAPI)](#backend-fastapi)
   - [LLM Service (Mistral API)](#llm-service-mistral-api)
   - [Document Rendering Engine](#document-rendering-engine)
   - [Client State Machine](#client-state-machine)
7. [End-to-End Data Flow](#7-end-to-end-data-flow)
8. [API Reference](#8-api-reference)
9. [Setup & Installation](#9-setup--installation)
   - [Prerequisites](#prerequisites)
   - [Setup Instructions](#setup-instructions)
10. [Environment Variables](#10-environment-variables)
11. [Running the Application](#11-running-the-application)
12. [How to Use](#12-how-to-use)
13. [Design Decisions & Trade-offs](#13-design-decisions--trade-offs)
14. [Known Limitations & Future Work](#14-known-limitations--future-work)

---

## 1. Project Summary

The **AI Resume Enhancer Bot** is a full-stack, decoupled application designed to mathematically align and generate professional resumes that systematically bypass Applicant Tracking Systems (ATS). Users upload an existing resume alongside a targeted Job Description (JD), and the system conducts a semantic match to identify critical gaps and output a perfectly formatted one-page PDF. 

Unlike standard LLM wrapper scripts, this system:
- Uses rigid **JSON-schema extraction** for objective scoring.
- Incorporates dynamic **spatial intelligence** to aggressively condense output so it natively fits a single PDF page without spillover.
- Features **decoupled PDF rendering** with multiple structurally distinct aesthetic mappings.
- Maintains **conversational memory state**, allowing iterative PDF generation across multiple templates without requiring raw re-uploads.

---

## 2. Key Features

| Feature | Description |
|---|---|
| 🤖 **Multi-Platform Bots** | Async Telegram & Discord interfaces deployable instantly for frictionless user experiences. |
| 📊 **Quantitative Scoring** | Real-time ATS match percentage and missing hard-skill gap identification. |
| ♻️ **Generative Rewriting** | Condenses, restructures, and rewrites experiences specifically targeting missing JD keywords. |
| 📄 **Dynamic PDF Engine** | Translates plain text into strictly bounded, gracefully spaced PDFs using python `reportlab`. |
| 🎨 **Template Ecosystem** | Switch between distinctly structured rendering schemas (ATS, Modern, Creative) instantly. |
| 🧠 **Spatial Awareness** | Intelligent LLM prompting enforces a rigid 400-word footprint to simulate brevity and eliminate 2-page sprawl. |
| 💾 **Session Caching** | Advanced state retention caching the base Resume to allow endless re-rendering into new formats. |

---

## 3. Tech Stack

### Backend & Core Services
| Library | Purpose |
|---|---|
| **FastAPI** | REST API framework — async, exceptionally fast, orchestrates core business domains |
| **Uvicorn** | ASGI server to run FastAPI locally |
| **Mistral AI SDK** | Orchestrates hosted LLM prompt engineering, inference, and synthetic text generation |
| **ReportLab** | Generates pixel-perfect programmatic PDF binaries from Python coordinates |
| **pdfplumber** | High-fidelity extraction of text strings and metadata from raw PDF uploads |
| **Pydantic** | Assures strong typing, payload validation, and data schema definitions |

### Interfaces / Bots
| Library | Purpose |
|---|---|
| **python-telegram-bot** | Fully async Telegram client, handling conversation states and inline keyboards |
| **discord.py** | Optional asynchronous wrapper spanning discord server integrations |

---

## 4. System Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                  USER INTERFACE (Bots)                       │
│             Telegram App / Discord Client                    │
│      ┌──────────────┐          ┌──────────────────────┐      │
│      │   Upload JD  │          │    Upload Resume     │      │
│      └──────┬───────┘          └──────────┬───────────┘      │
└─────────────│─────────────────────────────│──────────────────┘
              │                             │
              ▼                             ▼
┌──────────────────────────────────────────────────────────────┐
│                FastAPI Backend (Python)                      │
│                                                              │
│  ┌──────────────────┐               ┌────────────────────┐   │
│  │   Parse Engine   │──────────────▶│   LLM Service      │   │
│  │  (pdfplumber)    │               │  (Mistral API)     │   │
│  └──────────────────┘               └─────────┬──────────┘   │
│                                               │              │
│  ┌──────────────────┐               ┌─────────▼──────────┐   │
│  │ PDF Render Engine│◀──────────────│   Business Logic   │   │
│  │   (ReportLab)    │               │  (Score & Rewrite) │   │
│  └────────┬─────────┘               └────────────────────┘   │
│           │                                                  │
└───────────│──────────────────────────────────────────────────┘
            ▼
┌───────────────────────┐
│     Returned PDF      │
│   (Memory Buffer)     │
└───────────────────────┘
```

---

## 5. Project Structure

```text
RESUME_BOT/
│
├── main.py                    # FastAPI entry point & API route handlers
├── bot.py                     # Telegram Bot interface and Conversation State Machine
├── discord_bot.py             # Discord Bot interface (Alternative client)
├── ai_service.py              # LLM Integration, prompt tuning, and JSON parsing
├── resume_workflow.py         # HTTP client utilities linking the Bot to FastAPI
├── resume_pdf.py              # Core PDF rendering engine, templates, and styles
├── parser.py / resume_parser.py # Document fetching and pdfplumber extraction logic
│
├── requirements.txt           # Python dependencies
├── .env                       # Secret keys (ignored by git)
└── .gitignore                 # Repo ignore rules
```

---

## 6. Detailed Component Breakdown

### Backend (FastAPI)
**File:** `main.py`

This centralized internal API serves two critical workflows. Decoupling the logic here means web/mobile frontends can be appended natively without modifying internal infrastructure.
- `POST /analyze` — Evaluates physical gaps and derives objective ATS matching scores.
- `POST /rewrite` — Commands Mistral to synthesize new attributes, returning the modified string alongside an array of exact changes made.

---

### LLM Service (Mistral API)
**File:** `ai_service.py`  
**Class:** `MistralResumeService`

**Step 1 — Zero-Shot Strict Prompts:**  
Employs hard-coded system instructions firing on `response_format={"type": "json_object"}` alongside highly strict schema maps. This mathematically guarantees parseable properties for scoring parameters avoiding string slicing fragility.

**Step 2 — Synthetic Constraints:**  
To solve endemic AI hallucination and extreme volume generation, the prompt forcefully injects spatial limits: *"strictly fits onto a single page (maximum 400 words, ~15 bullet points total)"*.
**Why this matters:** Solves the notorious "spillover" problem where AI produces massive resumes that completely shatter readable constraints and formatting heuristics.

---

### Document Rendering Engine
**File:** `resume_pdf.py`  

Features three physically distinct layout dimensions (`ATS`, `Modern`, `Creative`) explicitly isolated into Python Dataclasses (`ResumeTheme`).

**Process:**
1. Employs regex pattern heuristics to identify standard structural resume headers inline mathematically.
2. Segments paragraphs vs. bullets vs. titles—assigning dedicated geometric margins (`leading`, `spaceAfter`) dynamically.
3. Calculates standard global geometric frames explicitly tracking a `0.5 inch` bounds mapping alongside specific `_draw_page_frame` canvas decorations for structural diversity.

---

### Client State Machine
**File:** `bot.py`  

Orchestrates user I/O cleanly using `python-telegram-bot`'s built in `ConversationHandler` mapped against states (`WAITING_JD`, `WAITING_RESUME`).

**Smart Persistence:** Under normal constraints, ending a conversational flow wipes dict memory contexts. This bot refactors states inherently around `context.user_data["session"]`. Users can infinitely cycle inline layout buttons to seamlessly render entirely new graphic templates against historical session buffers instantly.

---

## 7. End-to-End Data Flow

### Analyze & Rewrite Flow

```text
User uploads JD & Resume via Telegram
      │
      ▼
bot.py buffers into Contextual RAM Memory
      │
      ▼
POST /analyze  →  Mistral LLM evaluates semantic disparity
                     │  Translates array: Score, Strengths, Weaknesses, Missing Skills
                     ▼
bot.py Displays inline Format Selection UI (ATS / Modern / Creative)
      │
      ▼
User selects "Modern"
      │
      ▼
POST /rewrite  →  Mistral LLM structurally synthesizes new text
                     │  Imposes 400-word constraint, exports an exact "changes_made" diff
                     ▼
resume_pdf.py  →  Builds geometrical ReportLab Canvas map
                     │  Fires Modern Theme Dataclasses (Teal borders, highlight tracking blocks)
                     ▼
bot.py Resolves Stream into binary Buffer → Sends PDF explicitly to Chat UI
```

---

## 8. API Reference

### `POST /analyze`
Analyzes text against ATS filters without mutating base experience data natively.

**Request:** `application/json`
```json
{
  "jd": "Senior Backend Engineer... [full text]",
  "resume_text": "Software Developer... [full text]"
}
```

**Response:** `200 OK`
```json
{
  "analysis": {
    "score": 7.5,
    "match_percentage": 68,
    "missing_skills": ["Kubernetes", "Redis"],
    "suggestions": ["Add metrics to bullet points"]
  }
}
```

### `POST /rewrite`
Requests complete synthetic resume generation matching structural heuristics natively.

**Request:** `application/json`
```json
{
  "jd": "...",
  "resume_text": "...",
  "template": "Modern Resume"
}
```

---

## 9. Setup & Installation

### Prerequisites
- **Python 3.9+**
- A **Mistral API Key** (from [console.mistral.ai](https://console.mistral.ai))
- A **Telegram Bot Token** (from `@BotFather`)

### Setup Instructions

**1. Clone the repository**
```bash
git clone https://github.com/PavanKalyan1430/RESUME_IMPROVER_BOT.git
cd RESUME_IMPROVER_BOT
```

**2. Create and activate a Virtual Environment**
```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

**3. Install Dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up environment variables**
Add your `MISTRAL_API_KEY` and `TELEGRAM_BOT_TOKEN` locally inside a newly created `.env` file (see Environment Variables).

---

## 10. Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `MISTRAL_API_KEY` | ✅ Yes | — | Authentic token for Mistral LLM Cloud |
| `TELEGRAM_BOT_TOKEN`| ✅ Yes | — | Secure polling token configured via Telegram's BotFather |
| `MISTRAL_MODEL` | No | `mistral-small-latest` | Specify lightweight inference model versions natively |
| `API_BASE_URL` | No | `http://127.0.0.1:8000` | Local port domain designated for internal loopback API querying |

> 🔑 **Never commit your `.env` file.** It is strictly listed in `.gitignore`.

---

## 11. Running the Application

Because of the cleanly decoupled design, the application explicitly requires concurrent staging execution.

**Terminal 1 — Start the FastAPI Service Engine:**
```bash
.\venv\Scripts\python.exe -m uvicorn main:app --reload
```
*API deployed actively at `http://127.0.0.1:8000`*

**Terminal 2 — Trigger polling Telegram Bot:**
```bash
.\venv\Scripts\python.exe bot.py
```

---

## 12. How to Use
1. Inside Telegram, interact with your uniquely created bot.
2. Type or tap the command **`/analyze`** or **`/start`**.
3. Transmit the target **Job Description** strictly as plaintext.
4. Drag and Drop your original baseline **Resume** directly as PDF or text file.
5. In milliseconds, intercept the generated ATS Match Score and missing qualifications array explicitly quantified into insights.
6. Select any of the Inline format UI hooks currently generated (e.g., `Creative Style`).
7. Extract and collect your natively translated, single-page optimized binary PDF!

---

## 13. Design Decisions & Trade-offs

| Decision | Rationale |
|---|---|
| **Decoupling Bot and Backend Server** | Segregates state-memory mechanics completely away from inference rendering natively; facilitates swapping the interface inherently toward Next.Js UI or React environments seamlessly later. |
| **Strict JSON Extraction Prompts** | General LLM syntax constantly shifts format parameters dynamically; imposing explicit logical schema dictionaries mathematically guarantees functional processing predictability. |
| **ReportLab Functional Generics vs CSS/HTML parsers** | Direct ReportLab memory generation is brutally performant dynamically; circumventing heavy DOM rendering natively scales perfectly while locking explicitly tight geometric spatial coordinates into the physical limits of 8.5x11 blocks. |
| **Persistent Context Map Override** | Bypasses `Telegram` library boundaries wiping interaction variables contextually—persisting states into isolated `user_data` environments ensures 1-click styling iteration natively. |

---

## 14. Known Limitations & Future Work

| Limitation | Future Improvement |
|---|---|
| Cache Volatility Constraints | Establish permanent schema retention mechanics actively migrating cached arrays into `PostgreSQL` via `SQLAlchemy` mapping, enabling longitudinal user insight arrays. |
| Sync Web Server Restraints | Migrate report logic into a discrete Background Queue worker via `Celery` + `Redis` instances to stabilize blocking routines over extreme computational throughput. |
| Visual Graphic Overwrite Fallbacks | Construct an optical multimodal OCR handler natively parsing graphical elements inside heavily stylistic baseline PDFs inherently missing distinct metadata extraction properties. |
| LLM Token Context Capping | Integrate full vector embedding database integration logic (FAISS/Pinecone) inherently resolving chunk extraction queries bridging >20-page portfolio documents explicitly. |

---
*Built intricately with ❤️ using FastAPI, Mistral AI, ReportLab, and Python.*
