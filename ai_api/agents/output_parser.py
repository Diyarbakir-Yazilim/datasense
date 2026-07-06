from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Literal, Optional, Any
import json

class DataCleaningDecision(BaseModel):
    """Schema for the LLM's data cleaning decision output."""
    target_column: str = Field(description="Name of the column to predict")
    task_type: Literal["Classification", "Regression"] = Field(description="Machine learning task type")
    columns_to_drop: Optional[List[str]] = Field(default_factory=list, description="List of unnecessary columns to drop")
    missing_value_strategy: Optional[Dict[str, Literal["mean", "median", "mode", "drop"]]] = Field(
        default_factory=dict, 
        description="Dictionary mapping column names to missing value strategy"
    )
    reasoning: str = Field(description="A 1-2 sentence short text explaining why these decisions were made")

    @field_validator('columns_to_drop', mode='before')
    def parse_columns(cls, v: Any) -> Optional[List[str]]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list): return parsed
            except:
                return [x.strip() for x in v.split(',') if x.strip()]
        return v
        
    @field_validator('missing_value_strategy', mode='before')
    def parse_strategy(cls, v: Any) -> Optional[Dict[str, Literal["mean", "median", "mode", "drop"]]]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, dict): return parsed
            except:
                return {}
        return v
