# Polimi Course Advisor PoC

This repository contains a proof-of-concept system for an interactive chat advisor that helps Politecnico di Milano MSc students choose courses.

The final system will:
- Let students chat in natural language about interests, dislikes, and goals.
- Build a student profile from the conversation.
- Use scraped Polimi “Manifesto” course data and a course graph (with PageRank-style ranking) to suggest suitable courses.

## Phase 0 – Current scope

Phase 0 focuses ONLY on scaffolding:

- `backend/` – Python backend (FastAPI) with a basic health-check endpoint.
- `frontend/` – Vite + React + TypeScript app with a simple UI that can call the backend.
- Root-level configuration, sensible `.gitignore`, and basic documentation.

No scraping, databases, OpenAI, or ranking logic are implemented yet.

## Project structure (planned)

- `backend/`
  - FastAPI app (e.g. `app/main.py`)
  - `requirements.txt` for backend dependencies

- `frontend/`
  - Vite React TypeScript app

More details about setup and run commands will be added as Phase 0 progresses.