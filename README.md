# AI Resume Analyzer System

## 1. Project Overview
The modern job market relies heavily on Applicant Tracking Systems (ATS) that ruthlessly filter candidates based strictly on semantic constraints and structural readability. 
This project mathematically maps raw candidate resumes against targeted Job Descriptions (JDs), identifies critical keyword gaps, and synthetically reconstructs a highly optimized, fully formatted one-page PDF artifact directly tailored to the job. It completely eliminates the manual, time-consuming overhead of restructuring and rewriting resumes for individual applications.

## 2. System Architecture
The application runs on a decoupled, microservice-inspired architecture to ensure scalability and separation of concerns:
- **Client Layer (Bots)**: Asynchronous Telegram (and optional Discord) bots act as the primary interface, maintaining fast, conversational UX state machines.
- **Backend API Layer (FastAPI)**: A purely stateless HTTP server responsible for business logic, data validation, and load orchestration.
- **AI Intelligence Layer**: Integrates Mistral AI via Prompt Engineering to parse semantic meaning, score data, and rebuild text structures.
- **Document Rendering Engine**: A programmatic PDF rendering module (`reportlab`) that seamlessly translates unstructured text strings into specific mathematical coordinates on a document canvas.

## 3. Workflow / Execution Flow
1. **Intake Phase**: The user passes a target JD. The bot instantiates a transient session dictionary in memory. The user then uploads a base Resume (TXT or PDF).
2. **Analysis Pipeline**: The payload is dispatched to the backend API. The FastAPI service orchestrates an LLM call enforcing rigid JSON extraction. The system returns quantitative insights, ATS scoring, and missing hard skills.
3. **Template Selection & Rewrite**: The user selects a desired visual structure (e.g., *ATS*, *Modern*, *Creative*). The backend triggers a generative rewrite heavily restricted by a max-400-word constraint to guarantee a 1-page fit.
4. **Rendering & Dispatch**: The system intercepts the returned text, dynamically switches rendering logic based on the user's template selection, maps the font/margin boundaries via `reportlab`, generates binary PDF data in a memory buffer, and streams it instantly back to the user interface.

## 4. Core Modules Breakdown

- **`main.py` (FastAPI Server)**
  - **Responsibility**: Expose HTTP endpoints and handle request validation.
  - **Internal Working**: Defines strict Pydantic schemas (`AnalyzeRequest`, `RewriteRequest`) to validate raw data bounds before initiating heavy external API calls.
  
- **`bot.py` (Client State Handler)**
  - **Responsibility**: Handle multi-step conversational UI and inline hardware feedback.
  - **Internal Working**: Employs `python-telegram-bot` state machines to cache contexts. It dynamically updates inline callback buttons so users can repeatedly regenerate the same resume in diverse formats without needing to re-upload the base documents.

- **`ai_service.py` (LLM Integration Engine)**
  - **Responsibility**: Orchestrate prompts, inject context, and map string responses into programmatically usable properties.
  - **Internal Working**: Employs zero-shot structured prompts that strictly mandate JSON-schema outputs, parsing them back out into mapped Python dataclasses like `AnalysisResult`.

- **`resume_pdf.py` (Document Generation Renderer)**
  - **Responsibility**: Convert plain text into dynamically structured, visually distinct PDFs.
  - **Internal Working**: Utilizes Regex to heuristically identify ATS section headings, dynamically modifies line height/font points based on programmatic spatial constraints, and applies different structural layouts sequentially through the `reportlab.platypus` rendering engine.

## 5. Key Functionalities
- **Context-Aware Scoring**: Analyzes structural matches and dynamically aggregates both Strengths and Missing Keywords.
- **Non-Destructive Generative Rewriting**: Trims old, irrelevant technical padding and focuses specifically on matching JD attributes while preserving the underlying truthfulness of the applicant’s experience.
- **Persistent Generation Session**: Allows users to render the same resulting artifact iteratively across multiple template pipelines (ATS, Modern, Creative) directly from initial cached memory.
- **Architectural Formatting Constraints**: Automates margin generation and strict 1-page summarization sizing to simulate industry-standard constraints perfectly.

## 6. API / Interface Design
- **`POST /analyze`**
  - **Payload**: `{"jd": "...", "resume_text": "..."}`
  - **Purpose**: Returns an objective analysis schema mapping `score`, `match_percentage`, `missing_keywords`, and qualitative feedback.
- **`POST /rewrite`**
  - **Payload**: `{"jd": "...", "resume_text": "...", "template": "..."}`
  - **Purpose**: Forces LLM output synthesis, returning a heavily optimized `improved_resume` string alongside an array of explicit `changes_made`.

## 7. Technical Highlights
- **Decoupled Architecture**: By completely decoupling the Bot UX from the FastAPI backend, the AI generation service can instantly be consumed by future platforms (e.g., Web, Mobile Apps) without major refactoring.
- **Strict Schema Enforcement**: Utilizing structured JSON formatting tightly couples LLM generation with reliable pythonic objects, mitigating string-manipulation errors and hallucination bleed.
- **Design-Agnostic Extensibility**: Document generation is entirely decoupled from the threading logic, isolating template variations to `ResumeTheme` configuration dataclasses. Injecting a new styling layout requires modifying almost zero core logic.

## 8. Challenges & Solutions
- **Challenge - Spatial Overflow constraints**: Early iterations of the LLM hallucinated excessive filler details causing the generated output to aggressively spill beyond standard PDF margins into unreadable 2-page documents.
- **Solution**: Engineered dynamic spatial intelligence by modifying base `reportlab` margins natively, fine-tuning paragraph line `leading`, and creating heavily defensive prompts explicitly commanding a 400-word ceiling optimization. 
- **Challenge - Context Resetting**: Telegram conversational pipelines inherently discard historical states upon terminating the flow, forcing users to repeatedly upload JDs.
- **Solution**: Refactored states via `context.user_data["session"]` dict storage overriding traditional `ConversationHandler` boundaries, allowing the server interface to become globally "sticky" across recurring callback events.

## 9. Future Improvements
- **Data Persistence**: Implement a PostgreSQL database schema running via SQLAlchemy to track user metrics overtime, manage application sessions, and strictly enforce functional rate-limiting.
- **Queue Handlers**: Migrate massive asynchronous AI computation blocking to a Background Job Queue (via Celery & Redis) to accommodate concurrent bulk throughput without throttling edge HTTP workers.

## 10. Conclusion
The AI Resume Analyzer provides a completely automated, programmatic pipeline for deterministic doc-rendering, asynchronous processing, and intelligent entity refactoring. Built to bypass traditional scaling hurdles, it acts as a resilient scaffolding blueprint for local LLM orchestration and real-time generation.
