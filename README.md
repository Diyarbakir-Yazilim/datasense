# DataSense 🧠

![DataSense Cover](/C:/Users/mahsu/.gemini/antigravity/brain/16f7dc52-7317-4873-94ea-0641760fbb13/datasense_cover_1781082140128.png)

**An LLM-powered autonomous agent for intelligent data cleaning, EDA, and preprocessing.**

DataSense automates the essential stages of the data science workflow. Upload raw data, and our AI agent will autonomously analyze, clean, and prepare your files for machine learning tasks.

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

### Installation & Running Locally

We provide a `Makefile` to make running the project via Docker extremely simple.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Diyarbakir-Yazilim/datasense.git
   cd datasense
   ```

2. **Environment Variables:**
   Rename `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```

3. **Run the application:**
   You can easily start the whole stack (Frontend, Backend, AI Engine, Redis, Worker) using the Makefile:
   ```bash
   make up
   ```

### 🔧 Useful Makefile Commands
- `make build` : Build all docker images
- `make up` : Start all services in the background
- `make logs` : View live logs of all services
- `make down` : Stop all services
- `make clean` : Stop services and delete volumes/data

---
*Autonomous Data Analysis Pipeline.*