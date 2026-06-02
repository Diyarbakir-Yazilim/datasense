# DataSense Backend - Config
# TODO: CORS, dosya limitleri ve ortam değişkenleri eklenecek
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "DataSense Backend"
    API_V1_STR: str = "/api/v1"
    
    # Ortam Değişkenleri (Docker veya .env'den beslenir)
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
    AI_API_URL: str = os.getenv("AI_API_URL", "http://localhost:8001")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    
    # .env İçinden Gelen Değişkenler
    OPENAI_API_KEY: str = "sk-your-api-key-here"
    LLM_MODEL: str = "gpt-4"
    DEBUG: str = "false"
    MAX_FILE_SIZE_MB: str = "500"

    # Dosya Boyutu Limiti (Örn: 100MB)
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  
    
    # CORS Ayarları
    BACKEND_CORS_ORIGINS: list = ["*"]


    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"   
    }



settings = Settings()