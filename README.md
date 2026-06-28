# DataSense 🧠

![DataSense Cover](/C:/Users/mahsu/.gemini/antigravity/brain/16f7dc52-7317-4873-94ea-0641760fbb13/datasense_cover_1781082140128.png)

**An LLM-powered autonomous agent for intelligent data cleaning, EDA, and preprocessing.**

DataSense automates the essential stages of the data science workflow. Upload raw data, and our AI agent will autonomously analyze, clean, and prepare your files for machine learning tasks

## 🚀 Key Features
- **AI-Powered Cleaning:** Intelligent handling of missing values and data inconsistencies.
- **Task Identification:** Automatic detection of classification or regression problem types.
- **Automated EDA:** Data profiling and dynamic visualization generation.
- **Privacy-Centric:** Only metadata is processed by the LLM to ensure data security.

## 🏗️ System Architecture & Data Flow

```mermaid
sequenceDiagram
    participant User as 👤 Kullanıcı
    participant UI as 🖥️ Frontend (React)
    participant API as ⚙️ Backend (FastAPI)
    participant Worker as 🛠️ Celery Worker
    participant LLM as 🧠 AI Engine (LangChain)

    User->>UI: CSV Dosyası Yükler
    UI->>API: POST /api/v1/analyze (multipart/form-data)
    API->>API: Dosyayı Diske/S3'e Kaydet
    API->>Worker: Asenkron Görev Başlat (Celery)
    API-->>UI: 202 Accepted (job_id)
    
    UI->>API: GET /api/v1/status/{job_id} (Polling)
    
    Worker->>Worker: Pandas ile Metadata Çıkar (Schema, NaN counts)
    Worker->>LLM: Sadece Metadata Gönder (Veri Gizliliği)
    LLM-->>Worker: Temizleme & Analiz Kararları (JSON)
    Worker->>Worker: Kararları Fiziksel Veriye Uygula
    Worker->>API: İşlem Tamamlandı, Raporu Kaydet
    
    API-->>UI: 200 OK (status: completed, download_url)
    UI->>User: Raporu ve Grafikleri Göster
    User->>API: Temizlenmiş CSV'yi İndir
```

## 🛠 Tech Stack
- **Backend:** FastAPI
- **AI Engine:** LangChain + Gemini API
- **Data Processing:** Pandas/Polars
- **Task Queue:** Celery + Redis

## 💻 Getting Started

### Prerequisites
- Docker & Docker Compose
- OpenAI / Gemini API Keys

### Installation & Running Locally (with Docker)

The easiest way to run the entire DataSense stack is using Docker Compose. This will automatically build and link the Frontend, Backend, AI Engine, Celery Worker, and Redis container.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Diyarbakir-Yazilim/datasense.git
   cd datasense
   ```

2. **Environment Variables:**
   Rename `.env.example` to `.env` and fill in your API keys (e.g., GROQ_API_KEY, OPENAI_API_KEY):
   ```bash
   cp .env.example .env
   ```

3. **Run the application (Docker):**
   Execute the following command in the root directory to build and start all services:
   ```bash
   docker-compose up --build
   ```
   *Note: If you want to run it in the background, add the `-d` flag: `docker-compose up --build -d`*

Once the containers are running:
- **Frontend (UI)** will be available at: http://localhost:3000
- **Backend (API)** will be available at: http://localhost:8000/docs

### 🛑 Stopping the Application
To stop all services and preserve data:
```bash
docker-compose stop
```
To shut down completely and remove containers:
```bash
docker-compose down
```

---
*Autonomous Data Analysis Pipeline.*