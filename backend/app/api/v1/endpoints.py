import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from celery.result import AsyncResult
from app.worker.tasks import analyze_dataset_task
import uuid

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/analyze")
async def upload_and_analyze(file: UploadFile = File(...)):
    """
    Kullanıcıdan dosyayı alır, geçici alana kaydeder ve Celery işçisine gönderir.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Sadece CSV dosyaları desteklenmektedir.")

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya kaydedilemedi: {str(e)}")

    # Görevi Celery'ye gönder
    task = analyze_dataset_task.delay(file_path, file_id)

    return JSONResponse(status_code=202, content={
        "job_id": task.id,
        "status": "queued",
        "message": "Dosya kuyruğa eklendi. Analiz başlıyor."
    })


@router.get("/status/{job_id}")
async def get_task_status(job_id: str):
    """
    Celery görev durumunu döndürür.
    """
    task_result = AsyncResult(job_id)
    
    if task_result.state == 'PENDING':
        response = {
            "state": task_result.state,
            "status": "Görev sırada bekliyor..."
        }
    elif task_result.state != 'FAILURE':
        response = {
            "state": task_result.state,
            "current": task_result.info.get('current', 0) if task_result.info else 0,
            "total": task_result.info.get('total', 100) if task_result.info else 100,
            "status": task_result.info.get('status', '') if task_result.info else '',
            "result": task_result.result if task_result.state == 'SUCCESS' else None
        }
    else:
        # Bir şeyler yanlış gitti
        response = {
            "state": task_result.state,
            "status": str(task_result.info),  # Hata mesajı
        }
    return response


@router.get("/download/{job_id}")
async def download_cleaned_file(job_id: str):
    """
    Analiz sonrası temizlenmiş dosyayı indirir.
    """
    task_result = AsyncResult(job_id)
    if task_result.state != 'SUCCESS':
        raise HTTPException(status_code=400, detail="İşlem henüz tamamlanmadı veya başarısız oldu.")
    
    # Gerçek senaryoda sonucun içinden temizlenmiş dosya yolu alınır
    result_data = task_result.result
    if 'cleaned_file_path' not in result_data:
        raise HTTPException(status_code=404, detail="Temizlenmiş dosya bulunamadı.")
        
    cleaned_path = result_data['cleaned_file_path']
    if os.path.exists(cleaned_path):
        return FileResponse(path=cleaned_path, filename=f"cleaned_{job_id}.csv", media_type='text/csv')
    else:
        raise HTTPException(status_code=404, detail="Dosya sunucuda yok.")
