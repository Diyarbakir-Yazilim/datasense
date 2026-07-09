import time
import json
import httpx
import os
import polars as pl
from app.core.celery_app import celery_app

from app.core.logger import logger

@celery_app.task(bind=True)
def analyze_dataset_task(self, file_path: str, file_id: str, manual_decisions: dict = None):
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
                df_lazy = pl.scan_csv(file_path, ignore_errors=True, infer_schema_length=10000, null_values=["|", "NA", "N/A", "null", "", "?", "-"])
                cleaned_file_path = file_path.replace(".csv", "_cleaned.csv")
                
                schema = df_lazy.schema
                num_rows = df_lazy.select(pl.len()).collect().item()
                num_cols = len(schema)
                columns_list = list(schema.keys())
                
            elif file_path.endswith(('.xlsx', '.xls')):
                df_eager = pl.read_excel(file_path)
                if file_path.endswith('.xlsx'):
                    cleaned_file_path = file_path.replace(".xlsx", "_cleaned.xlsx")
                else:
                    cleaned_file_path = file_path.replace(".xls", "_cleaned.xlsx")
                
                df_lazy = df_eager.lazy()
                schema = df_eager.schema
                num_rows = df_eager.height
                num_cols = df_eager.width
                columns_list = df_eager.columns
            else:
                raise ValueError(f"Desteklenmeyen dosya formatı: {file_path}")

        except FileNotFoundError as fnf_err:
            logger.error(f"Kritik Hata: Dosya sunucuda bulunamadı: {str(fnf_err)}", extra=log_extra)
            self.update_state(state='FAILED_TASK', meta={'status': 'Hata: İşlenecek dosya bulunamadı.'})
            return {"status": "FAILED", "error": "File not found"}
            
        except Exception as read_err:
            logger.error(f"Kritik Hata: Dosya okunurken yapısal sorun oluştu: {str(read_err)}", extra=log_extra)
            self.update_state(state='FAILED_TASK', meta={'status': 'Hata: Dosya okunamadı, formatı bozuk olabilir.'})
            return {"status": "FAILED", "error": "Read error"}

        # Veri seti boş mu kontrolü
        if num_rows == 0:
            logger.warning("Uyarı: Okunan veri setinde hiç satır bulunamadı (Boş veri).", extra=log_extra)
            self.update_state(state='FAILED_TASK', meta={'status': 'Hata: Yüklenen dosya içeriği boş.'})
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
            self.update_state(state='FAILED_TASK', meta={'status': 'Hata: Sütun istatistikleri hesaplanamadı.'})
            return {"status": "FAILED", "error": "Computation error in metadata"}
            
        self.update_state(state='PROGRESS', meta={'current': 60, 'total': 100, 'status': 'AI Engine ile iletişime geçiliyor...'})
        time.sleep(1) # Simülasyon efekti
        
        # --- AI_API entegrasyonu VEYA Override Kararları ---
        try:
            if manual_decisions:
                logger.info("Manuel düzenleme (Override) algılandı. AI motoru atlanıyor.", extra=log_extra)
                ai_decisions = manual_decisions
                prompt_version = "override"
            else:
                ai_api_url = os.environ.get("AI_API_URL", "http://ai_api:8001")
                response = httpx.post(
                    f"{ai_api_url}/decide",
                    json={"metadata_json": json.dumps(metadata)},
                    timeout=120.0
                )
                response.raise_for_status()
                ai_decisions = response.json()
                
                prompt_version = ai_decisions.get("prompt_version", "unknown")
                logger.info(f"A/B Test - Kullanılan Prompt Versiyonu: {prompt_version}", extra=log_extra)
        except Exception as ai_err:
            logger.error(f"AI API ile iletişim kurulamadı: {str(ai_err)}", extra=log_extra)
            self.update_state(state='FAILED_TASK', meta={'status': 'Hata: Karar motoruna (AI) ulaşılamadı.'})
            return {"status": "FAILED", "error": "AI Engine connection error"}
        
        self.update_state(state='PROGRESS', meta={'current': 80, 'total': 100, 'status': 'Veri temizleme uygulanıyor...'})
        
        # --- 3. VERİ TEMİZLEME VE DİSKE YAZMA ADIMI ---
        try:
            # 1. Sütunları Düşürme (Drop)
            columns_to_drop = ai_decisions.get("columns_to_drop", [])
            if columns_to_drop:
                existing_cols_to_drop = [col for col in columns_to_drop if col in columns_list]
                df_lazy = df_lazy.drop(existing_cols_to_drop)
                for col in existing_cols_to_drop:
                    schema.pop(col, None)
                    columns_list.remove(col)
                    
            # 2. Eksik Veri Doldurma (Imputation)
            missing_strategy = ai_decisions.get("missing_value_strategy") or {}
            cleaning_expressions = []
            
            for col, strategy in missing_strategy.items():
                if col not in columns_list:
                    continue
                
                # Sütunun boşluk sayısını bul
                missing_cnt = next((c["missing_count"] for c in metadata["columns"] if c["name"] == col), 0)
                if missing_cnt == 0:
                    continue
                
                # Eğer tüm sütun null ise ortalama/medyan alınamaz, 0 ile doldur
                if missing_cnt == num_rows:
                    cleaning_expressions.append(pl.col(col).fill_null(0))
                    continue
                
                # Strateji Uygulama
                is_num = schema[col].is_numeric()
                if strategy == "mean" and is_num:
                    cleaning_expressions.append(pl.col(col).fill_null(pl.col(col).mean()))
                elif strategy == "median" and is_num:
                    cleaning_expressions.append(pl.col(col).fill_null(pl.col(col).median()))
                elif strategy == "mode":
                    # Mode returns a Series, take first
                    cleaning_expressions.append(pl.col(col).fill_null(pl.col(col).mode().first()))
                elif strategy == "drop":
                    df_lazy = df_lazy.filter(pl.col(col).is_not_null())
                else:
                    if is_num:
                        cleaning_expressions.append(pl.col(col).fill_null(pl.col(col).mean()))
                    else:
                        cleaning_expressions.append(pl.col(col).fill_null(pl.col(col).mode().first()))
            
            if cleaning_expressions:
                df_lazy = df_lazy.with_columns(cleaning_expressions)
                
            final_df = df_lazy.collect()
            if cleaned_file_path.endswith('.xlsx'):
                try:
                    final_df.write_excel(cleaned_file_path)
                except Exception:
                    final_df.to_pandas().to_excel(cleaned_file_path, index=False)
            else:
                final_df.write_csv(cleaned_file_path)
            
        except Exception as clean_err:
            logger.error(f"Veri temizleme veya diske yazma hatası: {str(clean_err)}", extra=log_extra)
            self.update_state(state='FAILED_TASK', meta={'status': 'Hata: Veri temizleme adımı başarısız oldu.'})
            return {"status": "FAILED", "error": "Cleaning or saving error"}
        
        # --- 4. GRAFİK (CHART) VERİSİ HAZIRLAMA ---
        self.update_state(state='PROGRESS', meta={'current': 90, 'total': 100, 'status': 'Grafikler hesaplanıyor...'})
        
        chart_data = {
            "correlation_matrix": None,
            "target_distribution": None
        }
        
        try:
            # 4.1 Korelasyon Matrisi (#51)
            numeric_cols = [col for col in final_df.columns if final_df.schema[col].is_numeric()]
            if len(numeric_cols) > 1:
                corr_df = final_df.select(numeric_cols).corr().fill_nan(0).fill_null(0)
                chart_data["correlation_matrix"] = {
                    "columns": numeric_cols,
                    "values": corr_df.to_numpy().tolist()
                }
                
                # Top correlated pair scatter plot (# Faz 4+)
                try:
                    corr_np = corr_df.to_numpy()
                    max_corr = -1
                    best_pair = None
                    for i in range(len(numeric_cols)):
                        for j in range(i + 1, len(numeric_cols)):
                            val = abs(corr_np[i][j])
                            if val > max_corr and val < 0.999:
                                max_corr = val
                                best_pair = (numeric_cols[i], numeric_cols[j])
                    
                    if best_pair:
                        col_x, col_y = best_pair
                        scatter_df = final_df.select([col_x, col_y]).drop_nulls()
                        if scatter_df.height > 1000:
                            scatter_df = scatter_df.sample(n=1000)
                        
                        chart_data["scatter_plot"] = {
                            "x_col": col_x,
                            "y_col": col_y,
                            "data": scatter_df.to_numpy().tolist(),
                            "correlation": float(max_corr)
                        }
                except Exception as e:
                    logger.warning(f"Scatter plot verisi hesaplanamadı: {e}", extra=log_extra)
                
            # 4.2 Dağılım Grafiği (#50)
            target_col = ai_decisions.get("target_column")
            task_type = ai_decisions.get("task_type")
            
            if target_col and target_col in final_df.columns:
                is_num = final_df.schema[target_col].is_numeric()
                if task_type == "Classification" or not is_num:
                    try:
                        dist_df = final_df.group_by(target_col).len().sort("len", descending=True).limit(10)
                        count_col = "len"
                    except Exception:
                        dist_df = final_df.group_by(target_col).count().sort("count", descending=True).limit(10)
                        count_col = "count"
                        
                    labels = [str(x) if x is not None else "Unknown" for x in dist_df.get_column(target_col).to_list()]
                    values = dist_df.get_column(count_col).to_list()
                    
                    chart_data["target_distribution"] = {
                        "type": "categorical",
                        "labels": labels,
                        "values": values
                    }
                else:
                    sample_df = final_df.select(target_col).drop_nulls()
                    if sample_df.height > 1000:
                        sample_df = sample_df.sample(n=1000)
                    chart_data["target_distribution"] = {
                        "type": "numerical",
                        "values": sample_df.get_column(target_col).to_list()
                    }
        except Exception as chart_err:
            logger.error(f"Grafik verisi hesaplama hatası: {str(chart_err)}", extra=log_extra)
            
        self.update_state(state='PROGRESS', meta={'current': 100, 'total': 100, 'status': 'İşlem Tamamlandı!'})
        logger.info("Veri motoru tüm işlemleri başarıyla tamamladı.", extra=log_extra)
        
        return {
            'status': 'Task completed successfully!',
            'original_file': file_path,
            'cleaned_file_path': cleaned_file_path,
            'metadata': metadata,
            'ai_decisions': ai_decisions,
            'chart_data': chart_data
        }
        
    except Exception as general_error:
        # Beklenmedik en dıştaki tüm hataları yakalar, Celery worker'ın çökmesini önler
        logger.critical(f"SİSTEM ÇÖKMESİ ENGELLENDİ: {str(general_error)}", extra=log_extra)
        self.update_state(state='FAILED_TASK', meta={'status': f'Hata: {str(general_error)}'})
        return {"status": "FAILED", "error": str(general_error)}