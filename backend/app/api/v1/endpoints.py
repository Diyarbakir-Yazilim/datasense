import os
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import pandas as pd
from langchain_groq import ChatGroq
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from celery.result import AsyncResult
from app.worker.tasks import analyze_dataset_task
from app.core.config import settings
import uuid

router = APIRouter()

@router.post("/analyze")
async def upload_and_analyze(file: UploadFile = File(...)):
    """
    Kullanıcıdan dosyayı alır, geçici alana kaydeder ve Celery işçisine gönderir.
    """
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Sadece CSV veya Excel dosyaları desteklenmektedir.")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}_{file.filename}")

    try:
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
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
        response = {
            "state": task_result.state,
            "status": str(task_result.info),
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
    
    result_data = task_result.result
    if 'cleaned_file_path' not in result_data:
        raise HTTPException(status_code=404, detail="Temizlenmiş dosya bulunamadı.")
        
    cleaned_path = result_data['cleaned_file_path']
    if os.path.exists(cleaned_path):
        return FileResponse(path=cleaned_path, filename=f"cleaned_{job_id}.csv", media_type='text/csv')
    else:
        raise HTTPException(status_code=404, detail="Dosya sunucuda yok.")

class ChatRequest(BaseModel):
    job_id: str
    message: str
    use_cleaned_data: bool = True

@router.post("/chat")
async def chat_with_agent(request: ChatRequest):
    """
    Synapse-AI Entegrasyonu: Yüklenen veya temizlenen veri seti üzerinde
    doğal dil ile soru sorma imkanı sağlar.
    """
    if "GROQ_API_KEY" not in os.environ:
        return {"response": "System Error: GROQ_API_KEY bulunamadı. Lütfen .env dosyanızı kontrol edin."}
        
    # Dosya yolunu belirle
    search_dir = settings.UPLOAD_DIR
    target_file = None
    
    # Tüm dosyaları tara ve job_id ile eşleşen dosyayı bul
    for f in os.listdir(search_dir):
        if request.job_id in f:
            if request.use_cleaned_data and "_cleaned.csv" in f:
                target_file = os.path.join(search_dir, f)
                break
            elif not request.use_cleaned_data and "_cleaned.csv" not in f:
                target_file = os.path.join(search_dir, f)
                break
                
    if not target_file:
        raise HTTPException(status_code=404, detail="Belirtilen job_id için dosya bulunamadı.")
        
    try:
        # Pandas ile oku
        df = pd.read_csv(target_file)
        
        # LangChain Agent oluştur
        llm = ChatGroq(temperature=0, model_name="llama-3.3-70b-versatile")
        agent = create_pandas_dataframe_agent(
            llm, 
            df, 
            verbose=True, 
            allow_dangerous_code=True
        )
        
        result = agent.invoke(request.message)
        return {"response": result["output"]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent Hatası: {str(e)}")
