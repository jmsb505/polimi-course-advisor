# Polimi Course Advisor Demo Guide

This document outlines a 5-minute live demonstration flow for the Polimi Course Advisor system.

## Prerequisites
- **Environment**: Ensure `OPENAI_API_KEY` is set.
- **Backend**: Running on `http://localhost:8000`
  ```bash
  python -m uvicorn backend.app.main:app --port 8000 --reload
  ```
- **Frontend**: Running on `http://localhost:5173`
  ```bash
  cd frontend && pnpm dev
  ```
- **Evaluation**: To run the offline evaluation harness:
  ```bash
  make eval
  ```

## 5-Minute Demo Flow

| Time | Segment | Description |
|------|---------|-------------|
| 0:00-0:30 | **The Hook** | Introduce the problem: MSc students at Polimi often struggle to find courses that align with their niche interests (e.g., "Game Dev" or "ML"). Show the clean, dark-mode UI. |
| 0:30-1:30 | **Demo Scenarios** | Use the **Demo Scenarios** panel on the right. Click "ML Engineer". Point out how the chat updates and the profile sidebar reflects extracted interests immediately. |
| 1:30-2:30 | **The Graph** | Show the **Course Graph**. Hover over "Machine Learning" node. Show the edge to "Neural Networks". Explain how personalization PageRank highlights relevant neighbors. |
| 2:30-3:30 | **Interactive Chat** | Type a custom follow-up (see Prompt 2 below). Show how recommendations adapt. Click a recommendation card to see the LLM-generated explanation. |
| 3:30-4:30 | **Stability & Persistence**| Click "Replay Last Run". Explain that state is persisted per session (`run_id`). This enables auditability and quick context restoration. |
| 4:30-5:00 | **Closing** | Show the **Evaluation Report** (`backend/reports/eval_report.md`) to prove the system works consistently across multiple personas without LLM variance. |

## Canned Prompts

1. **Scenario: Machine Learning** (Use Button)
   > "I want to become a Machine Learning Engineer. I love Python, data structures, and I'm interested in neural networks and big data."

2. **Refining Interests** (Type manually)
   > "I actually prefer practical projects over heavy mathematical theory. Can you suggest courses with project-based exams?"

3. **Scenario: Game Dev** (Use Button)
   > "I'm interested in computer graphics and game development. I like C++ and real-time rendering. I want to build a game engine."

## UI Highlights to Point Out
- **Profile Chips**: Watch them appear in the sidebar as the LLM extracts info.
- **Rich Recommendation Cards**: Point out the "Explanation" and "Reason Tags" (e.g., `matched_interest`).
- **Course Graph**:
  - Nodes represent **Courses**.
  - **Edge Tooltips**: Hover over a connection to see the **Shared Concepts** (e.g., Shared SSD, Shared Group) that link the courses.
  - **Sync**: Click a node in the graph -> the recommendation card highlights synchronously.
  - **Interaction**: Drag nodes to observe the force-directed layout stability.

## Troubleshooting / Fallbacks
- **OpenAI issues**: Use the "Replay Last Run" feature to show a pre-recorded session.
- **Backend crash**: Check the uvicorn terminal. If `init_data` fails, ensure `backend/data/courses.json` is present.
- **CORS error**: Ensure the backend is on port 8000 and the origins in `main.py` include `localhost:5173`.
