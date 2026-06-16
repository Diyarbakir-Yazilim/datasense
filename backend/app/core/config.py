from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "DataSense API"
    REDIS_URL: str = "redis://redis:6379/0" # Default for docker-compose
    UPLOAD_DIR: str = "./uploads" # Changed for Windows compatibility
    LOCAL_MODE: bool = False # If True, Celery runs synchronously and avoids Redis
    GROQ_API_KEY: str | None = None
    
    class Config:
        env_file = ".env"

settings = Settings()
