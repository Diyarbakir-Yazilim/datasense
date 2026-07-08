import os
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent
from celery.result import AsyncResult
from app.worker.tasks import analyze_dataset_task
from app.core.config import settings
from app.core.celery_app import celery_app
import uuid
from dotenv import load_dotenv
from app.core.logger import logger

load_dotenv()

router = APIRouter()

@router.post("/analyze")
async def upload_and_analyze(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
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
        logger.error(f"Dosya kaydedilemedi: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Dosya kaydedilemedi: {str(e)}")

    if settings.LOCAL_MODE:
        background_tasks.add_task(analyze_dataset_task.apply_async, args=[file_path, file_id], task_id=file_id)
        job_id = file_id
    else:
        task = analyze_dataset_task.apply_async(args=[file_path, file_id], task_id=file_id)
        job_id = task.id

    return JSONResponse(status_code=202, content={
        "job_id": job_id,
        "status": "queued",
        "message": "Dosya kuyruğa eklendi. Analiz başlıyor."
    })


class OverrideRequest(BaseModel):
    job_id: str
    manual_decisions: dict

@router.post("/override")
async def override_decisions(request: OverrideRequest, background_tasks: BackgroundTasks):
    """
    Kullanıcının manuel olarak değiştirdiği kararları alır ve
    AI adımını atlayarak veri temizleme işlemlerini baştan başlatır.
    """
    search_dir = settings.UPLOAD_DIR
    target_file = None
    
    for f in os.listdir(search_dir):
        if request.job_id in f and "_cleaned" not in f:
            target_file = os.path.join(search_dir, f)
            break
            
    if not target_file:
        logger.warning(f"Override başarısız: {request.job_id} için orijinal dosya bulunamadı.")
        raise HTTPException(status_code=404, detail="Orijinal veri dosyası bulunamadı. Lütfen dosyayı tekrar yükleyin.")

    new_job_id = str(uuid.uuid4())
    
    if settings.LOCAL_MODE:
        background_tasks.add_task(analyze_dataset_task.apply_async, args=[target_file, new_job_id, request.manual_decisions], task_id=new_job_id)
    else:
        task = analyze_dataset_task.apply_async(args=[target_file, new_job_id, request.manual_decisions], task_id=new_job_id)
        new_job_id = task.id

    return JSONResponse(status_code=202, content={
        "job_id": new_job_id,
        "status": "queued",
        "message": "Manuel kararlar alındı. Analiz yeniden başlatılıyor."
    })


@router.get("/status/{job_id}")
async def get_task_status(job_id: str):
    """
    Celery görev durumunu döndürür.
    """
    task_result = AsyncResult(job_id, app=celery_app)
    
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
async def download_cleaned_file(job_id: str, format: str = "csv"):
    """
    Analiz sonrası temizlenmiş dosyayı indirir (CSV, Excel veya JSON).
    """
    task_result = AsyncResult(job_id, app=celery_app)
    if task_result.state != 'SUCCESS':
        logger.warning(f"İndirme reddedildi: {job_id} henüz bitmedi veya başarısız.")
        raise HTTPException(status_code=400, detail="İşlem henüz tamamlanmadı veya başarısız oldu.")
    
    result_data = task_result.result
    if 'cleaned_file_path' not in result_data:
        logger.error(f"Temizlenmiş dosya bilgisi yok: {job_id}")
        raise HTTPException(status_code=404, detail="Temizlenmiş dosya bulunamadı.")
        
    cleaned_path = result_data['cleaned_file_path']
    if os.path.exists(cleaned_path):
        if format.lower() == "json":
            try:
                # Convert to json dynamically
                if cleaned_path.endswith('.xlsx'):
                    df = pd.read_excel(cleaned_path)
                else:
                    df = pd.read_csv(cleaned_path)
                json_data = df.to_json(orient='records')
                # We can return it directly as JSON or a downloadable FileResponse, 
                # but for big data, FileResponse of a temp json is better.
                # However, directly returning JSONResponse with appropriate headers is easiest.
                from fastapi.responses import Response
                return Response(
                    content=json_data, 
                    media_type="application/json", 
                    headers={"Content-Disposition": f'attachment; filename="cleaned_{job_id}.json"'}
                )
            except Exception as e:
                logger.error(f"JSON çevirme hatası: {str(e)}", exc_info=True)
                raise HTTPException(status_code=500, detail="Dosya JSON formatına çevrilemedi.")
                
        is_excel = cleaned_path.endswith('.xlsx')
        media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if is_excel else 'text/csv'
        filename = f"cleaned_{job_id}.xlsx" if is_excel else f"cleaned_{job_id}.csv"
        return FileResponse(path=cleaned_path, filename=filename, media_type=media_type)
    else:
        logger.error(f"Temizlenmiş dosya sunucuda yok: {cleaned_path}")
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
    openai_key = os.getenv("OPENAI_API_KEY")
    google_key = os.getenv("GOOGLE_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")
    
    if not any([
        openai_key and openai_key != "your-openai-api-key-here" and openai_key.strip(),
        google_key and google_key != "your-gemini-api-key-here" and google_key.strip(),
        groq_key and groq_key.strip()
    ]):
        return {"response": "System Error: Geçerli bir API anahtarı (OpenAI, Gemini veya Groq) bulunamadı. Lütfen .env dosyanızı yapılandırın."}
        
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
        
        # LangChain Agent oluştur (Dinamik LLM Seçimi)
        if openai_key and openai_key != "your-openai-api-key-here" and openai_key.strip():
            llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
            agent_type = "tool-calling"
        elif google_key and google_key != "your-gemini-api-key-here" and google_key.strip():
            llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)
            agent_type = "tool-calling"
        else:
            from langchain_groq import ChatGroq
            llm = ChatGroq(model="llama3-70b-8192", temperature=0.0)
            agent_type = "tool-calling"
        agent = create_pandas_dataframe_agent(
            llm, 
            df, 
            verbose=True, 
            allow_dangerous_code=True,
            agent_type=agent_type
        )
        
        result = agent.invoke(request.message)
        
        output = result.get("output", "")
        if isinstance(output, list):
            text_parts = []
            for part in output:
                if isinstance(part, dict) and "text" in part:
                    text_parts.append(part["text"])
                elif isinstance(part, str):
                    text_parts.append(part)
            output = "\n".join(text_parts)
        elif not isinstance(output, str):
            output = str(output)
            
        return {"response": output}
        
    except Exception as e:
        logger.error(f"Agent Hatası: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent Hatası: {str(e)}")
