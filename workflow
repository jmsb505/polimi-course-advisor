.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.app.main:app --reload
cd frontend; pnpm dev