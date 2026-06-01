# 📊 DataSense

**LLM destekli akıllı veri temizleme ve görselleştirme platformu.**

DataSense, yüklenen veri setlerini analiz eder, LLM (Büyük Dil Modeli) ile akıllı temizlik kararları üretir ve kullanıcıya interaktif bir arayüz sunar.

---

## 🏗️ Mimari

```
┌────────────┐     ┌────────────┐     ┌────────────┐
│  Frontend   │────▶│  Backend   │────▶│  AI API    │
│  React+Vite │     │  FastAPI   │     │  Polars+LLM│
└────────────┘     └─────┬──────┘     └────────────┘
                         │
                   ┌─────▼──────┐
                   │   Redis    │
                   │  + Celery  │
                   └────────────┘
```

| Katman | Teknoloji | Açıklama |
|--------|-----------|----------|
| **Frontend** | React 18 + Vite | Sürükle-bırak arayüz, ECharts görselleştirme |
| **Backend** | FastAPI + Celery | REST API, asenkron görev yönetimi |
| **AI API** | Polars + LangChain | Veri işleme ve LLM karar motoru |
| **Kuyruk** | Redis + Celery | Asenkron iş kuyruğu |

---

## 🚀 Hızlı Başlangıç

### Docker ile Çalıştırma (Önerilen)

```bash
# .env dosyası oluşturun
cp .env.example .env
# OPENAI_API_KEY değerini ayarlayın

# Tüm servisleri başlatın
docker-compose up --build
```

Servisler:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs
- **AI API**: http://localhost:8001

### Manuel Kurulum

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### Celery Worker
```bash
cd backend
celery -A app.core.celery_app worker --loglevel=info -Q datasense_queue
```

#### AI API
```bash
cd ai_api
pip install -r requirements.txt
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 📡 API Sözleşmesi

### Endpoints

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| `POST` | `/api/v1/upload` | Veri dosyası yükleme |
| `GET` | `/api/v1/status/{task_id}` | Görev durumu sorgulama |
| `GET` | `/api/v1/cleaning-plan/{task_id}` | Temizlik planı getirme |
| `POST` | `/api/v1/override` | LLM kararlarını düzenleme |
| `POST` | `/api/v1/download` | Temizlenmiş veri indirme |
| `GET` | `/api/v1/health` | Sağlık kontrolü |

### Dosya Yükleme Örneği

```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@veri_seti.csv"
```

### Yanıt Formatı

```json
{
  "task_id": "uuid-string",
  "filename": "veri_seti.csv",
  "file_size": 1048576,
  "status": "pending",
  "message": "Dosya başarıyla yüklendi, işlem kuyruğa alındı."
}
```

---

## 🛠️ Geliştirme

### Ortam Değişkenleri

| Değişken | Varsayılan | Açıklama |
|----------|-----------|----------|
| `OPENAI_API_KEY` | — | OpenAI API anahtarı |
| `LLM_MODEL` | `gpt-4` | Kullanılacak LLM modeli |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis bağlantı adresi |
| `MAX_FILE_SIZE_MB` | `500` | Maksimum dosya boyutu (MB) |
| `DEBUG` | `false` | Hata ayıklama modu |

### Desteklenen Dosya Formatları

- CSV (`.csv`)
- Excel (`.xlsx`, `.xls`)
- JSON (`.json`)
- Parquet (`.parquet`)

---

## 📦 Proje Yapısı

```
DataSense/
├── frontend/                  # React UI katmanı
│   ├── src/
│   │   ├── components/        # UploadArea, ProgressBar, DynamicChart, OverrideModal
│   │   ├── pages/             # Sayfa bileşenleri
│   │   └── services/          # API iletişim katmanı
│   └── package.json
├── backend/                   # FastAPI API Ağ Geçidi
│   ├── app/
│   │   ├── api/v1/            # REST endpoint'leri
│   │   ├── core/              # Config, Celery
│   │   └── models/            # Pydantic şemaları
│   └── requirements.txt
├── ai_api/                    # Veri/Karar Motoru
│   ├── data_processing/       # Metadata çıkarıcı, Polars temizleyici
│   ├── agents/                # LLM karar ajanı, çıktı parser
│   └── prompts/               # LLM prompt şablonları
├── .github/workflows/         # CI/CD pipeline
├── docker-compose.yml         # Orkestrasyon
└── README.md
```

---

## 📄 Lisans

MIT License - Detaylar için [LICENSE](LICENSE) dosyasına bakın.