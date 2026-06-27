# 🤝 Team Contributions & Roles

This document outlines the roles and contributions of the team members in the development of the **DataSense** project. As discussed in [Issue #21](https://github.com/Diyarbakir-Yazilim/datasense/issues/21), we use color-coded labels on GitHub to track the areas of responsibility.

## 👥 Role Definitions & GitHub Labels

| Role | GitHub Label Color | Description |
|------|-------------------|-------------|
| **DevOps / CI-CD** | 🔵 `#0075ca` (Blue) | Deployment, local environment setups, CI/CD pipelines, background task infrastructure. |
| **Backend** | 🟢 `#0e8a16` (Green) | FastAPI architecture, endpoint routing, state management, Celery queue handling. |
| **Frontend** | 🟡 `#fbca04` (Yellow) | React UI/UX development, state management, API integration, styling (Glassmorphism). |
| **Data Science / AI** | 🔴 `#d73a4a` (Red) | LLM integration (LangChain/Groq), Pandas dataframe manipulation, AI prompt engineering. |

---

## 🚀 Key Contributions Log

### Phase 1: MVP & Local Environment Stabilization
*Contributions made during the initial stabilization and UI overhaul.*

#### 🔵 DevOps & Infrastructure
- Designed and implemented **Local Mode** (`LOCAL_MODE=True`) to bypass Docker & Redis requirements for seamless local development.
- Migrated Celery's result backend from Redis to a local SQLite database (`celery_results.sqlite`) to prevent connection crashes on Windows environments.
- Implemented FastAPI `BackgroundTasks` to decouple heavy file processing from the main HTTP thread, preventing the UI from hanging during large uploads.
- Resolved environment dependency conflicts (e.g., TensorFlow vs LangChain runtime clashes).

#### 🟢 Backend Architecture
- Developed asynchronous file upload endpoints (`/api/v1/analyze`) with reliable status polling (`/api/v1/status/{job_id}`).
- Constructed the backend architecture to support eager task execution while propagating states safely to the SQLite backend.
- Integrated `python-dotenv` for secure loading of `.env` files and API keys (e.g., `GROQ_API_KEY`).

#### 🟡 Frontend UI/UX
- Designed a modern, premium **Glassmorphism** aesthetic using dynamic gradients and hover micro-animations.
- Built the `UploadArea.jsx` component with drag-and-drop support for CSV/Excel datasets and a real-time progress bar.
- Developed the interactive `AgentChat.jsx` interface, allowing users to converse directly with the Synapse-AI agent.
- Configured Vite Proxy to seamlessly route `/api` requests to the FastAPI backend while bypassing CORS limits.

#### 🔴 AI & Data Science Integration
- Integrated **ChatGroq (Llama-3)** for lightning-fast, autonomous data analysis capabilities.
- Wired the LangChain Pandas DataFrame Agent into the backend to execute dynamic Python code against user datasets.
- Developed the data ingestion pipeline, capable of parsing and pre-processing both `.csv` and `.xlsx` files securely before LLM interaction.

---
*This document serves as a historical record of our collaborative efforts to build the DataSense MVP.*
