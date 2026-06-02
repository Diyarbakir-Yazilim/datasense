import os
from backend.app.core.celery_app import celery_app
from backend.app.services.data_engine import DataEngine

@celery_app.task(name="backend.app.tasks.execute_autonomous_cleaning", bind=True)
def execute_autonomous_cleaning(self, file_path: str, cleaning_plan: dict, output_path: str) -> dict:
    """
    Executes the Polars-powered autonomous data cleaning pipeline asynchronously.
    Maintains strict compliance with the project's privacy-centric metadata guidelines.
    """
    try:
        engine = DataEngine(file_path)
        processed_path = engine.execute_cleaning(cleaning_plan, output_path)
        
        return {
            "status": "completed",
            "input_file": file_path,
            "output_file": processed_path,
            "error": None
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "input_file": file_path,
            "output_file": None,
            "error": str(e)
        }