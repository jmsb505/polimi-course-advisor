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
