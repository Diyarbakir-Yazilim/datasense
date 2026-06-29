import time
import polars as pl
from app.core.celery_app import celery_app

@celery_app.task(bind=True)
def analyze_dataset_task(self, file_path: str, file_id: str):
    """
    Refactored data processing task using Polars for high performance profiling,
    metadata extraction, and optimized memory management.
    """
    self.update_state(state='PROGRESS', meta={'current': 10, 'total': 100, 'status': 'Dosya okunuyor...'})
    
    try:
        # 1. Veriyi Oku (CSV için Lazy, Excel için Eager okuma kullanıyoruz)
        if file_path.endswith('.csv'):
            # scan_csv ile veriyi RAM'e yüklemeden sadece bir sorgu planı (LazyFrame) oluşturuyoruz
            df_lazy = pl.scan_csv(file_path)
            cleaned_file_path = file_path.replace(".csv", "_cleaned.csv")
            
            # Metadata için hızlıca şemayı alıyoruz
            schema = df_lazy.schema
            num_rows = df_lazy.select(pl.len()).collect().item() # Satır sayısını optimize hesapla
            num_cols = len(schema)
            columns_list = list(schema.keys())
            
        else:
            # Excel dosyaları Polars'ta doğrudan 'read_excel' ile okunur (Eager mod)
            df_eager = pl.read_excel(file_path)
            cleaned_file_path = file_path.replace(".xlsx", "_cleaned.csv").replace(".xls", "_cleaned.csv")
            
            # Excel için Lazy olmadığı için doğrudan eager dataframe üzerinden bilgileri alıyoruz
            df_lazy = df_eager.lazy() # Sonraki işlemler ortak olsun diye lazy'ye çeviriyoruz
            schema = df_eager.schema
            num_rows = df_eager.height
            num_cols = df_eager.width
            columns_list = df_eager.columns

        self.update_state(state='PROGRESS', meta={'current': 30, 'total': 100, 'status': 'Metadata çıkarılıyor...'})
        time.sleep(1) # Simülasyon efekti
        
        # 2. Temel Metadata Analizi
        metadata = {
            "num_rows": num_rows,
            "num_cols": num_cols,
            "columns": []
        }
        
        # Her sütunun eksik veri ve benzersiz değer analizini Polars Expression'ları ile topluca hazırlıyoruz
        # Bu yöntem Pandas'taki for döngüsünden çok daha hızlı çalışır.
        stats_expressions = []
        for col in columns_list:
            stats_expressions.extend([
                pl.col(col).null_count().alias(f"{col}_missing"),
                pl.col(col).n_unique().alias(f"{col}_unique")
            ])
        
        # Tüm sütunların istatistiklerini tek bir seferde ve paralel olarak hesaplıyoruz
        calculated_stats = df_lazy.select(stats_expressions).collect()
        
        for col in columns_list:
            col_info = {
                "name": col,
                "dtype": str(schema[col]), # Polars veri tipini string'e çeviriyoruz
                "missing_count": int(calculated_stats.get_column(f"{col}_missing")[0]),
                "unique_count": int(calculated_stats.get_column(f"{col}_unique")[0])
            }
            metadata["columns"].append(col_info)
            
        self.update_state(state='PROGRESS', meta={'current': 60, 'total': 100, 'status': 'AI Engine ile iletişime geçiliyor...'})
        time.sleep(1) # Simülasyon efekti
        
        # TODO: Burada AI_API'ye metadata gönderilip (JSON formatında) geri dönüş alınacak.
        ai_decisions = {
            "task_type": "Regression",
            "applied_steps": ["Eksik veriler ortalama ile dolduruldu.", "Gereksiz sütunlar atıldı."]
        }
        
        self.update_state(state='PROGRESS', meta={'current': 80, 'total': 100, 'status': 'Veri temizleme uygulanıyor...'})
        
        # 3. Veri Temizleme Uygulaması
        # Sayısal sütunları (Float ve Integer olanları) seçip boş değerleri ortalama (mean) ile dolduruyoruz
        numeric_cols = [col for col, dtype in schema.items() if dtype.is_numeric()]
        
        cleaning_expressions = [
            pl.col(col).fill_null(pl.col(col).mean()) for col in numeric_cols
        ]
        
        if cleaning_expressions:
            df_lazy = df_lazy.with_columns(cleaning_expressions)
            
        # 4. Tüm Değişiklikleri Çalıştır ve CSV olarak diske yaz
        # collect() ile nihai dataframe'i oluşturup write_csv ile kaydediyoruz
        final_df = df_lazy.collect()
        final_df.write_csv(cleaned_file_path)
        
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