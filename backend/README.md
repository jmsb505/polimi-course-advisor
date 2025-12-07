# Backend – Polimi Course Advisor

This backend is a FastAPI service that exposes:
- health endpoints
- course catalogue endpoints
- a ranking endpoint based on a course graph + PageRank-style logic (Phase 2).

## Running the backend

From the repo root:

```bash
cd backend
uvicorn backend.app.main:app --reload
```

By default this starts on http://127.0.0.1:8000.

- Interactive docs: http://127.0.0.1:8000/docs
- Alternative docs: http://127.0.0.1:8000/redoc

The app loads:
- `backend/data/courses.json`
- Builds an in-memory graph from that data via `backend/core/graph.py`

at startup and keeps them in memory.

## API endpoints (Phase 3)

### GET /health
Basic health check (legacy, non-API-prefixed).

**Response:**
```json
{
  "status": "ok",
  "service": "backend",
  "phase": 3,
  "path": "/health"
}
```

### GET /api/health
Health check for the API namespace.

**Sample:**
```bash
curl http://127.0.0.1:8000/api/health
```

### GET /api/courses
List all first-semester, non-ENHANCE courses.

**Optional query parameters:**
- `q`: substring filter on course name (case-insensitive).
- `group`: filter by group (e.g. MANDATORY, GROUNDINGS, METHODS).
- `semester`: filter by semester (int; dataset currently only has 1).

**Example:**
```bash
curl "http://127.0.0.1:8000/api/courses?q=DATA"
```

**Response shape (array of CourseSummary):**
```json
[
  {
    "code": "056892",
    "name": "DATA MINING",
    "cfu": 5.0,
    "semester": 1,
    "language": "EN",
    "group": "MANDATORY",
    "alpha_group_last": {
      "from": "A",
      "to": "ZZZZ",
      "lecturer": "Lanzi Pierluca"
    }
  }
]
```

### GET /api/courses/{code}
Return details for a specific course.

**Example:**
```bash
curl http://127.0.0.1:8000/api/courses/056892
```

**Response shape (CourseDetail):**
```json
{
  "code": "056892",
  "name": "DATA MINING",
  "cfu": 5.0,
  "semester": 1,
  "language": "EN",
  "group": "MANDATORY",
  "alpha_group_last": {
    "from": "A",
    "to": "ZZZZ",
    "lecturer": "Lanzi Pierluca"
  },
  "description": "Long text here...",
  "neighbors": null
}
```
(The `neighbors` field is reserved for future graph-debug info.)

### POST /api/rank
Rank courses for a given student profile using the Phase 2 graph + PageRank logic.

**Request body (StudentProfileIn):**
```json
{
  "interests": ["machine learning", "data science"],
  "avoid": ["hardware"],
  "goals": ["research"],
  "language_preference": "EN",
  "workload_tolerance": "medium",
  "preferred_exam_types": ["written"],
  "liked_courses": ["056892"],
  "disliked_courses": []
}
```
All fields are optional; empty lists / nulls are allowed.

**Example:**
```bash
curl http://127.0.0.1:8000/api/rank \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"interests":["machine learning"],"goals":["research"]}'
```

**Response shape (array of RankedCourseOut):**
```json
[
  {
    "code": "056892",
    "name": "DATA MINING",
    "cfu": 5.0,
    "semester": 1,
    "language": "EN",
    "group": "MANDATORY",
    "alpha_group_last": {
      "from": "A",
      "to": "ZZZZ",
      "lecturer": "Lanzi Pierluca"
    },
    "score": 0.0543,
    "reason_tags": ["interest_match", "graph_central"]
  }
]
```
The `reason_tags` field is derived from whatever metadata the Phase 2 ranking function returns (lists, dicts of flags, etc.), normalized into a list of human-readable tags.
