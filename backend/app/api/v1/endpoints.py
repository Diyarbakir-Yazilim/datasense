# DataSense Backend - API v1 Endpoints
# TODO: Yükleme, durum sorgulama ve indirme endpoint'leri eklenecek

import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import BaseModel
from backend.app.services.data_engine import DataEngine
from backend.app.tasks import execute_autonomous_cleaning

router = APIRouter()

# Ensure the upload directory exists
UPLOAD_DIR = "/tmp/datasense_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class MetadataResponse(BaseModel):
    status: str
    file_path: str
    metadata: dict


class CleanRequest(BaseModel):
    file_path: str
    cleaning_plan: dict = {
        "drop_nulls": True,
        "remove_outliers": True,
        "strip_whitespace": True
    }


class CleanResponse(BaseModel):
    status: str
    task_id: str
    message: str


@router.post("/upload", response_model=MetadataResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...)):
    """
    Receives the raw dataset file via API, saves it to a secure temporal directory,
    and initializes the DataEngine pipeline to extract privacy-centric metadata.
    """
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".csv", ".xlsx", ".xls"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Only CSV and Excel files are allowed."
        )

    # Securely construct the destination path
    safe_file_name = f"raw_{file.filename}"
    destination_path = os.path.join(UPLOAD_DIR, safe_file_name)

    try:
        # Stream the uploaded file chunks into the local disk to prevent memory overhead
        with open(destination_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Initialize our Polars-powered DataEngine
        engine = DataEngine(destination_path)
        metadata_summary = engine.initialize_pipeline()

        return MetadataResponse(
            status="success",
            file_path=destination_path,
            metadata=metadata_summary
        )

    except Exception as e:
        # Ensure cleanup if something fails during the initialization
        if os.path.exists(destination_path):
            os.remove(destination_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process the uploaded file: {str(e)}"
        )


@router.post("/clean", response_model=CleanResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_cleaning(payload: CleanRequest):
    """
    Dispatches the heavy data cleaning transformations to the background Celery workers.
    """
    if not os.path.exists(payload.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target data file not found on server."
        )

    base_dir = os.path.dirname(payload.file_path)
    file_name = os.path.basename(payload.file_path)
    output_path = os.path.join(base_dir, file_name.replace("raw_", "cleaned_"))

    try:
        # Pass parameters as explicit keyword arguments to the Celery task
        task = execute_autonomous_cleaning.delay(
            file_path=payload.file_path,
            cleaning_plan=payload.cleaning_plan,
            output_path=output_path
        )

        return CleanResponse(
            status="accepted",
            task_id=task.id,
            message="Autonomous cleaning task has been successfully queued in the background."
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to dispatch background task: {str(e)}"
        )