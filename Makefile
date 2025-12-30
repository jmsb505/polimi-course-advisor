.PHONY: eval run-backend run-frontend

# Run the evaluation harness
eval:
	@echo "Running evaluation harness..."
	@python -m backend.scripts.eval_profiles
	@echo "Evaluation complete. See backend/reports/eval_report.md"

# Helper to run backend
run-backend:
	@cd backend && python -m uvicorn app.main:app --port 8000 --reload

# Helper to run frontend
run-frontend:
	@cd frontend && pnpm dev

# Run migrations and seed PoC data
seed-poc:
	@echo "Pushing migrations to Supabase..."
	@npx supabase db push
	@echo "Seeding PoC data..."
	@python scripts/seed_poc.py
	@echo "PoC setup complete."
