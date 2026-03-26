# AI Resume Analyzer Bot

A hackathon-ready project that combines a FastAPI backend, Telegram and Discord bots, PDF resume parsing, and Mistral-powered resume analysis/rewrite workflows.

## Features

- Accepts a job description and a resume from Telegram or Discord users
- Parses PDF or text resumes
- Analyzes resume-to-JD fit with:
  - Score out of 10
  - Match percentage
  - Missing skills
  - Strengths
  - Weaknesses
  - Suggestions
  - Missing keywords
- Lets the user pick a template:
  - ATS Resume
  - Modern Resume
  - Creative Resume
- Rewrites the resume without inventing fake experience
- Re-scores the improved resume
- Sends the improved resume back as a downloadable styled PDF

## Project Structure

```text
project/
|-- main.py
|-- bot.py
|-- discord_bot.py
|-- ai_service.py
|-- parser.py
|-- resume_pdf.py
|-- resume_parser.py
|-- resume_workflow.py
|-- requirements.txt
`-- README.md
```

## Requirements

- Python 3.9+
- A Telegram bot token from BotFather
- A Discord bot token from the Discord Developer Portal
- A Mistral API key

## Environment Variables

Set these before running:

```powershell
$env:MISTRAL_API_KEY="your_mistral_api_key"
$env:TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
$env:DISCORD_BOT_TOKEN="your_discord_bot_token"
$env:API_BASE_URL="http://127.0.0.1:8000"
$env:MISTRAL_MODEL="mistral-small-latest"
```

`API_BASE_URL` and `MISTRAL_MODEL` are optional. The defaults shown above are used if they are not set.

## Installation

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run the FastAPI Server

```powershell
uvicorn main:app --reload
```

API will be available at:

- `http://127.0.0.1:8000`
- Swagger docs: `http://127.0.0.1:8000/docs`

## Run the Telegram Bot

In a second terminal:

```powershell
python bot.py
```

## Run the Discord Bot

In another terminal:

```powershell
python discord_bot.py
```

Enable the `Message Content Intent` for your bot in the Discord Developer Portal so the bot can read JD and resume text messages.

## API Endpoints

### `POST /analyze`

Request:

```json
{
  "jd": "Backend engineer role requiring Python, FastAPI, Docker, AWS...",
  "resume_text": "John Doe\nPython Developer..."
}
```

Response:

```json
{
  "analysis": {
    "score": 7.5,
    "match_percentage": 78,
    "missing_skills": ["AWS", "Docker"],
    "strengths": ["Strong Python background"],
    "weaknesses": ["No cloud deployment experience shown"],
    "suggestions": ["Highlight API performance work"],
    "missing_keywords": ["microservices", "CI/CD"],
    "summary": "Solid engineering match with clear cloud gaps."
  }
}
```

### `POST /rewrite`

Request:

```json
{
  "jd": "Backend engineer role requiring Python, FastAPI, Docker, AWS...",
  "resume_text": "John Doe\nPython Developer...",
  "template": "ATS Resume"
}
```

Response:

```json
{
  "improved_resume": "PROFESSIONAL SUMMARY\n...",
  "analysis": {
    "score": 8.6,
    "match_percentage": 88,
    "missing_skills": ["AWS"],
    "strengths": ["Better keyword coverage"],
    "weaknesses": ["Cloud experience still limited"],
    "suggestions": ["Add deployment results if available"],
    "missing_keywords": ["terraform"],
    "summary": "Resume is now more targeted and ATS-friendly."
  }
}
```

## Telegram Bot Flow

1. User sends `/start`
2. Bot asks for the job description
3. User sends JD text
4. Bot asks for the resume
5. User uploads a PDF/TXT resume or pastes text
6. Bot returns initial analysis
7. Bot shows inline keyboard template options
8. User selects a template
9. Bot rewrites the resume, re-scores it, and sends:
   - Old Score
   - New Score
   - Improvement
   - Improved resume text
   - Downloadable styled `.pdf` file

## Discord Bot Flow

1. User sends `!start` or `!analyze`
2. Bot asks for the job description
3. User sends JD text
4. Bot asks for the resume
5. User uploads a PDF/TXT resume or pastes text
6. Bot returns initial analysis
7. Bot shows style buttons
8. User selects a style
9. Bot rewrites the resume, re-scores it, and sends:
   - Old Score
   - New Score
   - Improvement
   - Improved resume text
   - Downloadable styled `.pdf` file

## Notes

- Telegram session state is stored in memory through `context.user_data`
- Discord sessions are stored in memory keyed by Discord user id
- PDF parsing uses `pdfplumber`
- PDF export uses `reportlab`
- The bots talk to the FastAPI backend over HTTP using `httpx`
- For production deployment, move session state to Redis or a database and run the bots/web app behind a process manager

## Example Output Format

Initial Response:

```text
Score: 6.8/10
Match: 67%
Missing Skills: [Docker, AWS]
Suggestions: [Add cloud tooling, Highlight FastAPI projects]
```

Final Response:

```text
Old Score: 6.8/10
New Score: 8.4/10
Improvement: +1.6
```
