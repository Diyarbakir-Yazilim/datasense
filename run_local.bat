@echo off
echo ==========================================
echo DataSense - Local Windows Native Runner
echo ==========================================
echo.

set LOCAL_MODE=True

echo [1/4] Installing Backend Dependencies...
cd backend
pip install -r requirements.txt
cd ..

echo.
echo [2/4] Installing Frontend Dependencies...
cd frontend
call npm install
cd ..

echo.
echo [3/4] Starting FastAPI Backend...
start cmd /k "cd backend && set LOCAL_MODE=True && uvicorn app.main:app --reload --port 8000"

echo.
echo [4/4] Starting React Frontend...
start cmd /k "cd frontend && npm run dev"

echo.
echo ==========================================
echo Success! 
echo The backend is running in a new window on port 8000.
echo The frontend is running in a new window on port 3000.
echo Note: Celery tasks will run synchronously since LOCAL_MODE=True.
echo ==========================================
pause
