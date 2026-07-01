import time
import logging
import polars as pl
from app.core.celery_app import celery_app

# 1. Loglama Yapılandırması (Dosyaya ve Terminale yazar)
logger = logging.getLogger("data_engine")
logger.setLevel(logging.INFO)

# Eğer handler'lar daha önce eklenmediyse ekleyelim (Celery reload durumlarında logların yinelenmesini önler)
if not logger.handlers:
    file_handler = logging.FileHandler("data_engine.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - [FileID: %(file_id)s] - %(message)s"))
    logger.addHandler(file_handler)

@celery_app.task(bind=True)
def analyze_dataset_task(self, file_path: str, file_id: str):
    """
    Refactored data processing task using Polars for high performance profiling,
    metadata extraction, and optimized memory management. Includes advanced error handling.
    """
    # Loglara file_id enjekte etmek için extra parametresi kullanıyoruz
    log_extra = {"file_id": file_id}
    logger.info(f"Veri işleme görevi başlatıldı. Yol: {file_path}", extra=log_extra)
    
    self.update_state(state='PROGRESS', meta={'current': 10, 'total': 100, 'status': 'Dosya okunuyor...'})
    
    try:
        # --- 1. DOSYA OKUMA VE KONTROL ADIMI ---
        try:
            if file_path.endswith('.csv'):
                df_lazy = pl.scan_csv(file_path)
                cleaned_file_path = file_path.replace(".csv", "_cleaned.csv")
                
                schema = df_lazy.schema
                num_rows = df_lazy.select(pl.len()).collect().item()
                num_cols = len(schema)
                columns_list = list(schema.keys())
                
            elif file_path.endswith(('.xlsx', '.xls')):
                df_eager = pl.read_excel(file_path)
                cleaned_file_path = file_path.replace(".xlsx", "_cleaned.csv").replace(".xls", "_cleaned.csv")
                
                df_lazy = df_eager.lazy()
                schema = df_eager.schema
                num_rows = df_eager.height
                num_cols = df_eager.width
                columns_list = df_eager.columns
            else:
                raise ValueError(f"Desteklenmeyen dosya formatı: {file_path}")

        except FileNotFoundError as fnf_err:
            logger.error(f"Kritik Hata: Dosya sunucuda bulunamadı: {str(fnf_err)}", extra=log_extra)
            self.update_state(state='FAILURE', meta={'status': 'Hata: İşlenecek dosya bulunamadı.'})
            return {"status": "FAILED", "error": "File not found"}
            
        except Exception as read_err:
            logger.error(f"Kritik Hata: Dosya okunurken yapısal sorun oluştu: {str(read_err)}", extra=log_extra)
            self.update_state(state='FAILURE', meta={'status': 'Hata: Dosya okunamadı, formatı bozuk olabilir.'})
            return {"status": "FAILED", "error": "Read error"}

        # Veri seti boş mu kontrolü
        if num_rows == 0:
            logger.warning("Uyarı: Okunan veri setinde hiç satır bulunamadı (Boş veri).", extra=log_extra)
            self.update_state(state='FAILURE', meta={'status': 'Hata: Yüklenen dosya içeriği boş.'})
            return {"status": "FAILED", "error": "Empty dataset"}

        self.update_state(state='PROGRESS', meta={'current': 30, 'total': 100, 'status': 'Metadata çıkarılıyor...'})
        time.sleep(1) # Simülasyon efekti
        
        # --- 2. METADATA VE İSTATİSTİK ADIMI ---
        metadata = {
            "num_rows": num_rows,
            "num_cols": num_cols,
            "columns": []
        }
        
        try:
            stats_expressions = []
            for col in columns_list:
                stats_expressions.extend([
                    pl.col(col).null_count().alias(f"{col}_missing"),
                    pl.col(col).n_unique().alias(f"{col}_unique")
                ])
            
            calculated_stats = df_lazy.select(stats_expressions).collect()
            
            for col in columns_list:
                col_info = {
                    "name": col,
                    "dtype": str(schema[col]),
                    "missing_count": int(calculated_stats.get_column(f"{col}_missing")[0]),
                    "unique_count": int(calculated_stats.get_column(f"{col}_unique")[0])
                }
                metadata["columns"].append(col_info)
        except pl.exceptions.ComputeError as comp_err:
            logger.error(f"Polars İstatistik Hesaplama Hatası: {str(comp_err)}", extra=log_extra)
            self.update_state(state='FAILURE', meta={'status': 'Hata: Sütun istatistikleri hesaplanamadı.'})
            return {"status": "FAILED", "error": "Computation error in metadata"}
            
        self.update_state(state='PROGRESS', meta={'current': 60, 'total': 100, 'status': 'AI Engine ile iletişime geçiliyor...'})
        time.sleep(1) # Simülasyon efekti
        
        # TODO: AI_API entegrasyonu
        ai_decisions = {
            "task_type": "Regression",
            "applied_steps": ["Eksik veriler ortalama ile dolduruldu.", "Gereksiz sütunlar atıldı."]
        }
        
        self.update_state(state='PROGRESS', meta={'current': 80, 'total': 100, 'status': 'Veri temizleme uygulanıyor...'})
        
        # --- 3. VERİ TEMİZLEME VE DİSKE YAZMA ADIMI ---
        try:
            numeric_cols = [col for col, dtype in schema.items() if dtype.is_numeric()]
            
            cleaning_expressions = []
            for col in numeric_cols:
                # Kolonun hepsi null ise mean() hata vermesin diye kontrol ekliyoruz
                missing_cnt = next((c["missing_count"] for c in metadata["columns"] if c["name"] == col), 0)
                if missing_cnt < num_rows:
                    cleaning_expressions.append(pl.col(col).fill_null(pl.col(col).mean()))
                else:
                    cleaning_expressions.append(pl.col(col).fill_null(0)) # Tamamı boşsa 0 bas geç
            
            if cleaning_expressions:
                df_lazy = df_lazy.with_columns(cleaning_expressions)
                
            final_df = df_lazy.collect()
            final_df.write_csv(cleaned_file_path)
            
        except Exception as clean_err:
            logger.error(f"Veri temizleme veya diske yazma hatası: {str(clean_err)}", extra=log_extra)
            self.update_state(state='FAILURE', meta={'status': 'Hata: Veri temizleme adımı başarısız oldu.'})
            return {"status": "FAILED", "error": "Cleaning or saving error"}
        
        self.update_state(state='PROGRESS', meta={'current': 100, 'total': 100, 'status': 'İşlem Tamamlandı!'})
        logger.info("Veri motoru tüm işlemleri başarıyla tamamladı.", extra=log_extra)
        
        return {
            'status': 'Task completed successfully!',
            'original_file': file_path,
            'cleaned_file_path': cleaned_file_path,
            'metadata': metadata,
            'ai_decisions': ai_decisions
        }
        
    except Exception as general_error:
        # Beklenmedik en dıştaki tüm hataları yakalar, Celery worker'ın çökmesini önler
        logger.critical(f"SİSTEM ÇÖKMESİ ENGELLENDİ: {str(general_error)}", extra=log_extra)
        self.update_state(state='FAILURE', meta={'exc_type': type(general_error).__name__, 'exc_message': str(general_error)})
        raise general_error