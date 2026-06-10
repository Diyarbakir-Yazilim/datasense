from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "DataSense API"
    REDIS_URL: str = "redis://redis:6379/0" # Default for docker-compose
    UPLOAD_DIR: str = "/tmp/datasense_uploads"
    
    class Config:
        env_file = ".env"

settings = Settings()
