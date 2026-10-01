Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Starting Trading Analytics Backend (FastAPI)..." -ForegroundColor Cyan
Write-Host "Docs: http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan

& .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
