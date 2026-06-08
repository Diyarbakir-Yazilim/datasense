from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from celery.result import AsyncResult
import os
import aiofiles
from app.core.config import settings
from app.worker.tasks import analyze_dataset_task

router = APIRouter()

@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Uploads a dataset and starts a Celery background task for analysis."""
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only CSV or Excel files are allowed.")
        
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
    
    # Save the file asynchronously
    async with aiofiles.open(file_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)
        
    # Trigger celery task
    task = analyze_dataset_task.delay(file_path)
    
    return {"message": "File uploaded successfully. Analysis started.", "task_id": task.id}

@router.get("/status/{task_id}")
def get_status(task_id: str):
    """Check the status of a Celery background task."""
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result if task_result.ready() else None
    }
    
    if task_result.state == 'PROGRESS':
        result.update({
            "current": task_result.info.get('current', 0),
            "total": task_result.info.get('total', 100),
            "status_details": task_result.info.get('status', '')
        })
        
    return result
