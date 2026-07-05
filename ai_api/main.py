import os
import sys
from fastapi import FastAPI
from pydantic import BaseModel

# Projenin ana dizinini yola ekleyelim ki ajanlara ulaşılabilsin
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.decision_agent import get_data_cleaning_decision

app = FastAPI()

class DecideRequest(BaseModel):
    metadata_json: str

@app.get("/")
def read_root():
    return {"message": "AI API Service is running"}

@app.post("/decide")
def decide(request: DecideRequest):
    """
    Takes dataset metadata and returns autonomous data cleaning decisions from the LLM.
    """
    decision = get_data_cleaning_decision(request.metadata_json)
    return decision
