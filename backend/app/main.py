# DataSense Backend - Main
# TODO: FastAPI uygulama başlatma eklenecek
# DataSense Backend - Main
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings

# FastAPI Uygulamasını Ayarlarımızla Başlatıyoruz
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS (Köprü) Ayarlarını Tanımlıyoruz (Frontend bağlantısı için)
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# İlk Canlı Test Rotamız (Root Endpoint)
@app.get("/")
def read_root():
    return {
        "status": "working",
        "message": "DataSense Backend Canavar Gibi Calisiyor!",
        "project_name": settings.PROJECT_NAME
    }