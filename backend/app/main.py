from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import endpoints

app = FastAPI(
    title="DataSense API",
    description="Backend for AI-powered data cleaning and analysis.",
    version="1.0.0"
)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Geliştirme ortamı için. Üretimde spesifik URL'ler girilmelidir.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to DataSense API"}
