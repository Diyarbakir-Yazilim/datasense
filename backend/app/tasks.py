import os
import logging
from backend.app.core.celery_app import celery_app
from backend.app.services.data_engine import DataEngine

logger = logging.getLogger(__name__)

@celery_app.task(name="backend.app.tasks.execute_autonomous_cleaning", bind=True)
def execute_autonomous_cleaning(self, file_path: str, cleaning_plan: dict, output_path: str) -> dict:
    """
    Executes the Polars-powered autonomous data cleaning pipeline asynchronously.
    Maintains strict compliance with the project's privacy-centric metadata guidelines.
    """
    logger.info(f"Starting autonomous cleaning task [{self.request.id}] for file: {file_path}")

    try:
        # Initialize our Polars-powered DataEngine
        engine = DataEngine(file_path)
        processed_path = engine.execute_cleaning(cleaning_plan, output_path)

        logger.info(f"Task [{self.request.id}] completed successfully. Cleaned file saved at: {processed_path}")
        
        return processed_path
        
    except Exception as e:
        logger.error(f"Task [{self.request.id}] failed. Error: {str(e)}", exc_info=True)
        raise e