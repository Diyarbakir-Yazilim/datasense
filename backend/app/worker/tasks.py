import time
import pandas as pd
from app.core.celery_app import celery_app

@celery_app.task(bind=True)
def analyze_dataset_task(self, file_path: str, file_id: str):
    """
    Pandas kullanarak ham CSV dosyasını profiller, eksik verileri analiz eder
    ve yapay zekanın (LLM) kullanabilmesi için metadata çıkarır.
    """
    self.update_state(state='PROGRESS', meta={'current': 10, 'total': 100, 'status': 'Dosya okunuyor...'})
    
    try:
        # 1. Veriyi Oku
        df = pd.read_csv(file_path)
        
        self.update_state(state='PROGRESS', meta={'current': 30, 'total': 100, 'status': 'Metadata çıkarılıyor...'})
        time.sleep(1) # Simülasyon efekti
        
        # 2. Temel Metadata Analizi
        metadata = {
            "num_rows": len(df),
            "num_cols": len(df.columns),
            "columns": []
        }
        
        for col in df.columns:
            col_info = {
                "name": col,
                "dtype": str(df[col].dtype),
                "missing_count": int(df[col].isnull().sum()),
                "unique_count": int(df[col].nunique())
            }
            metadata["columns"].append(col_info)
            
        self.update_state(state='PROGRESS', meta={'current': 60, 'total': 100, 'status': 'AI Engine ile iletişime geçiliyor...'})
        time.sleep(1) # Simülasyon efekti
        
        # TODO: Burada AI_API'ye metadata gönderilip (JSON formatında) geri dönüş alınacak.
        # Şimdilik mock (sahte) bir AI kararı üretiyoruz.
        ai_decisions = {
            "task_type": "Regression",
            "applied_steps": ["Eksik veriler ortalama ile dolduruldu.", "Gereksiz sütunlar atıldı."]
        }
        
        self.update_state(state='PROGRESS', meta={'current': 80, 'total': 100, 'status': 'Veri temizleme uygulanıyor...'})
        
        # Veriyi fiziksel olarak temizleme (Basit örnek: eksikleri ortalama ile doldurma)
        for col in df.select_dtypes(include=['float64', 'int64']).columns:
            df[col] = df[col].fillna(df[col].mean())
            
        # Temizlenmiş veriyi kaydet
        cleaned_file_path = file_path.replace(".csv", "_cleaned.csv")
        df.to_csv(cleaned_file_path, index=False)
        
        self.update_state(state='PROGRESS', meta={'current': 100, 'total': 100, 'status': 'İşlem Tamamlandı!'})
        
        return {
            'status': 'Task completed successfully!',
            'original_file': file_path,
            'cleaned_file_path': cleaned_file_path,
            'metadata': metadata,
            'ai_decisions': ai_decisions
        }
        
    except Exception as e:
        self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
        raise e
