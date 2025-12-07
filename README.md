# Polimi Course Advisor PoC

This repository contains a proof-of-concept system for an interactive chat advisor that helps Politecnico di Milano MSc students choose courses.

The final system will:

- Let students chat in natural language about interests, dislikes, and goals.
- Build a student profile from the conversation.
- Use scraped Polimi ?Manifesto? course data and a course graph (with PageRank-style ranking) to suggest suitable courses.

---

## Phase 0 ? Current scope

Phase 0 focuses ONLY on scaffolding:

- `backend/` ? Python backend (FastAPI) with a basic health-check endpoint.
- `frontend/` ? Vite + React + TypeScript app with a simple UI that calls the backend health endpoint.
- Root-level configuration, sensible `.gitignore`, and basic documentation.

No scraping, databases, OpenAI, or ranking logic are implemented yet.

---

## Requirements

- **Python** 3.10+ (virtualenv recommended)
- **Node.js** 18+ (or newer LTS)
- **pnpm** package manager

---

## Project structure

At the end of Phase 0 the repo looks like:

```text
polimi-course-advisor/
  backend/
    app/
      __init__.py
      main.py        # FastAPI app with /api/health and CORS
    requirements.txt # Backend dependencies (FastAPI + uvicorn)
  frontend/
    package.json     # Vite React TS app
    index.html
    src/
      main.tsx
      App.tsx        # Calls backend /api/health and displays the result
  README.md
  .gitignore
```

## Phase 4 – LLM integration & `/api/chat`

The backend integrates with the OpenAI API to provide a chat-based course advisor
that:
- Generates natural-language replies.
- Maintains a structured `StudentProfile`.
- Computes course recommendations via the existing ranking logic.

### Environment variables

Set these in the shell before starting the backend:

- `OPENAI_API_KEY` (**required**)  
  OpenAI API key used for all LLM calls.

Optional overrides (all have sensible defaults):

- `OPENAI_MODEL_REPLY` (default: `gpt-4o-mini`)  
  Model used to generate natural-language replies.

- `OPENAI_MODEL_PROFILE` (default: same as `OPENAI_MODEL_REPLY`)  
  Model used for JSON `StudentProfile` extraction.

- `OPENAI_TEMPERATURE_REPLY` (default: `0.7`)  
  Creativity for chat replies.

- `OPENAI_TEMPERATURE_PROFILE` (default: `0.0`)  
  Should stay low for deterministic JSON output.

### Running the backend (dev)

From the repo root:

```bash
# activate your virtualenv first, e.g.:
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Set the OpenAI key:
$Env:OPENAI_API_KEY = "sk-...your-key..."

# Start the FastAPI app:
python -m uvicorn backend.app.main:app --reload
```

The API will be available at: http://127.0.0.1:8000.

### `/api/chat` endpoint

**Method**: POST

**URL**: `/api/chat`

**Request body** (`application/json`):

```json
{
  "messages": [
    {
      "role": "user",
      "content": "I like machine learning and coding, but I hate pure math..."
    }
  ],
  "current_profile": {
    "interests": ["machine learning"],
    "avoid": ["pure theory"],
    "language_preference": "EN"
  },
  "top_k": 5
}
```

- `messages`: full chat history (user/assistant/system). If no system message is included, the backend injects its own advisor prompt.
- `current_profile`: optional partial `StudentProfile`. The backend merges this with what it infers from the conversation.
- `top_k`: how many courses to recommend.

**Response** (200 OK on success):

```json
{
  "reply": "Given what you've told me, I would suggest...",
  "updated_profile": {
    "interests": ["machine learning", "optimization"],
    "avoid": ["pure theory"],
    "language_preference": "EN",
    "workload_tolerance": "medium",
    "preferred_exam_types": ["project"],
    "liked_courses": [],
    "disliked_courses": []
  },
  "recommendations": [
    {
      "code": "088983",
      "name": "FOUNDATIONS OF OPERATIONS RESEARCH",
      "cfu": 5.0,
      "semester": 1,
      "language": "UNKNOWN",
      "group": "GROUNDINGS",
      "score": 0.87
    }
  ]
}
```

On LLM failures (e.g. rate limit or missing quota), the endpoint returns:

**HTTP 503 Service Unavailable** with a JSON body:
```json
{ "detail": "LLM quota exceeded or temporarily unavailable. Please check your OpenAI plan/billing." }
```
