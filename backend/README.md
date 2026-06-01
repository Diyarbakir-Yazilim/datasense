# Backend

This directory contains the main API Gateway for the DataSense platform.

Built with FastAPI, this service handles file uploads, manages asynchronous background tasks via Celery and Redis, and acts as the central orchestrator connecting the frontend interface with the AI-driven data processing engine.

## Getting Started

To run the backend locally:

1. Ensure you have Python 3.11+ installed.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
