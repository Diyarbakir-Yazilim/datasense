from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import endpoints
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend for AI-powered data cleaning and analysis.",
    version="1.0.0"
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router, prefix="/api/v1", tags=["datasets"])

@app.get("/")
def read_root():
    return {"message": "Welcome to DataSense API"}
