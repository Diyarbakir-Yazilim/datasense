# AI API

This directory houses the Data/Decision Engine for DataSense.

It utilizes Polars for high-performance, out-of-memory safe data cleaning and preprocessing. Additionally, it integrates with Large Language Models (LLMs) via LangChain to autonomously profile data schemas, detect anomalies, and generate intelligent, structured cleaning decisions.

## Getting Started

To run the AI API locally:

1. Ensure you have Python 3.11+ installed.
2. Set up your environment variables (e.g., `OPENAI_API_KEY`) as defined in the root `.env` file.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the service (typically running on port 8001):
   ```bash
   python -m uvicorn main:app --reload --port 8001
   ```
