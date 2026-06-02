from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.api.v1.endpoints import router as api_router

# Initialize FastAPI application with settings
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set all configured origins on CORS middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include the API router under the configured API prefix
app.include_router(api_router, prefix=settings.API_V1_STR, tags=["Data Operations"])

# Root endpoint for health check
@app.get("/")
def read_root():
    return {
        "status": "working",
        "message": "DataSense Backend is running smoothly.",
        "project_name": settings.PROJECT_NAME
    }