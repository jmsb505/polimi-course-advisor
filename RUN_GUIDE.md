# Running the Project

Follow these steps to start the backend and frontend services.

## 1. Backend Setup

From the **project root** directory:

### Activate Virtual Environment
```powershell
.venv\Scripts\Activate.ps1
```

### Run the Backend API
```powershell
python -m uvicorn backend.app.main:app --port 8000 --reload
```
The API will be available at `http://localhost:8000`.

---

## 2. Frontend Setup

From the **project root** directory:

### Navigate to Frontend
```powershell
cd frontend
```

### Install Dependencies (First time only)
```powershell
pnpm install
```

### Run the Development Server
```powershell
pnpm dev
```
The application will be available at `http://localhost:5173`.

---

## Troubleshooting

- **Address already in use**: If port 8000 or 5173 is already taken, check if you have other terminal windows running the project.
- **Python not found**: Ensure you have activated the `.venv` first.
- **PNPM not found**: Install it via `npm install -g pnpm` if necessary.
