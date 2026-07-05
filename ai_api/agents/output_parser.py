from pydantic import BaseModel, Field
from typing import List, Dict, Literal

class DataCleaningDecision(BaseModel):
    """Schema for the LLM's data cleaning decision output."""
    target_column: str = Field(description="Name of the column to predict")
    task_type: Literal["Classification", "Regression"] = Field(description="Machine learning task type")
    columns_to_drop: List[str] = Field(default_factory=list, description="List of unnecessary columns to drop")
    missing_value_strategy: Dict[str, Literal["mean", "median", "mode", "drop"]] = Field(
        default_factory=dict, 
        description="Dictionary mapping column names to missing value strategy"
    )
    reasoning: str = Field(description="A 1-2 sentence short text explaining why these decisions were made")
