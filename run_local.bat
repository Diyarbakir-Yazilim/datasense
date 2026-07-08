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
echo [5/6] Installing AI API Dependencies...
cd ai_api
pip install -r requirements.txt --user
cd ..

echo.
echo [6/6] Starting AI_API Microservice...
start cmd /k "cd ai_api && uvicorn main:app --reload --port 8001"

echo.
echo ==========================================
echo Success! 
echo The backend is running on port 8000.
echo The AI API is running on port 8001.
echo The frontend is running on port 3000.
echo ==========================================
pause
