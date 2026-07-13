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
    # Inject file_id into logs via extra parameter
    log_extra = {"file_id": file_id}
    logger.info(f"Data processing task started. Path: {file_path}", extra=log_extra)
    
    self.update_state(state='PROGRESS', meta={'current': 10, 'total': 100, 'status': 'Reading file...'})
    
    try:
        # --- 1. FILE READING AND VALIDATION STEP ---
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
                raise ValueError(f"Unsupported file format: {file_path}")

        except FileNotFoundError as fnf_err:
            logger.error(f"Critical Error: File not found on server: {str(fnf_err)}", extra=log_extra)
            self.update_state(state='FAILED_TASK', meta={'status': 'Error: Target file not found.'})
            return {"status": "FAILED", "error": "File not found"}
            
        except Exception as read_err:
            logger.error(f"Critical Error: Structural issue while reading file: {str(read_err)}", extra=log_extra)
            self.update_state(state='FAILED_TASK', meta={'status': 'Error: Could not read file, format might be corrupted.'})
            return {"status": "FAILED", "error": "Read error"}

        # Check if dataset is empty
        if num_rows == 0:
            logger.warning("Warning: No rows found in the loaded dataset (Empty data).", extra=log_extra)
            self.update_state(state='FAILED_TASK', meta={'status': 'Error: Uploaded file is empty.'})
            return {"status": "FAILED", "error": "Empty dataset"}

        self.update_state(state='PROGRESS', meta={'current': 30, 'total': 100, 'status': 'Extracting metadata...'})
        time.sleep(1) # Simulation effect
        
        # --- 2. METADATA AND STATISTICS STEP ---
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
            logger.error(f"Polars Statistics Computation Error: {str(comp_err)}", extra=log_extra)
            self.update_state(state='FAILED_TASK', meta={'status': 'Error: Could not calculate column statistics.'})
            return {"status": "FAILED", "error": "Computation error in metadata"}
            
        self.update_state(state='PROGRESS', meta={'current': 60, 'total': 100, 'status': 'Contacting AI Engine...'})
        time.sleep(1) # Simulation effect
        
        # --- AI_API integration OR Override Decisions ---
        try:
            if manual_decisions:
                logger.info("Manual override detected. Skipping AI engine.", extra=log_extra)
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
                logger.info(f"A/B Test - Prompt Version Used: {prompt_version}", extra=log_extra)
        except Exception as ai_err:
            logger.error(f"Could not communicate with AI API: {str(ai_err)}", extra=log_extra)
            self.update_state(state='FAILED_TASK', meta={'status': 'Error: Could not reach decision engine (AI).'})
            return {"status": "FAILED", "error": "AI Engine connection error"}
        
        self.update_state(state='PROGRESS', meta={'current': 80, 'total': 100, 'status': 'Applying data cleaning...'})
        
        # --- 3. DATA CLEANING AND WRITING STEP ---
        try:
            # 1. Dropping Columns
            columns_to_drop = ai_decisions.get("columns_to_drop", [])
            if columns_to_drop:
                existing_cols_to_drop = [col for col in columns_to_drop if col in columns_list]
                df_lazy = df_lazy.drop(existing_cols_to_drop)
                for col in existing_cols_to_drop:
                    schema.pop(col, None)
                    columns_list.remove(col)
                    
            # 2. Missing Value Imputation
            missing_strategy = ai_decisions.get("missing_value_strategy") or {}
            cleaning_expressions = []
            
            for col, strategy in missing_strategy.items():
                if col not in columns_list:
                    continue
                
                # Find missing count for the column
                missing_cnt = next((c["missing_count"] for c in metadata["columns"] if c["name"] == col), 0)
                if missing_cnt == 0:
                    continue
                
                # If entire column is null, mean/median cannot be calculated, fill with 0
                if missing_cnt == num_rows:
                    cleaning_expressions.append(pl.col(col).fill_null(0))
                    continue
                
                # Apply strategy
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
                
            if cleaned_file_path.endswith('.csv'):
                df_lazy.sink_csv(cleaned_file_path)
                # Take first 10k rows (or all) to protect RAM for charts
                if num_rows > 10000:
                    final_df = df_lazy.head(10000).collect()
                else:
                    final_df = df_lazy.collect()
            else:
                final_df = df_lazy.collect()
                try:
                    final_df.write_excel(cleaned_file_path)
                except Exception:
                    final_df.to_pandas().to_excel(cleaned_file_path, index=False)
            
        except Exception as clean_err:
            logger.error(f"Error during data cleaning or disk write: {str(clean_err)}", extra=log_extra)
            self.update_state(state='FAILED_TASK', meta={'status': 'Error: Data cleaning step failed.'})
            return {"status": "FAILED", "error": "Cleaning or saving error"}
        
        # --- 4. PREPARING CHART DATA ---
        self.update_state(state='PROGRESS', meta={'current': 90, 'total': 100, 'status': 'Calculating charts...'})
        
        chart_data = {
            "correlation_matrix": None,
            "target_distribution": None
        }
        
        try:
            # 4.1 Correlation Matrix (#51)
            numeric_cols = [col for col in final_df.columns if final_df.schema[col].is_numeric()]
            if len(numeric_cols) > 1:
                corr_df = final_df.select(numeric_cols).corr().fill_nan(0).fill_null(0)
                chart_data["correlation_matrix"] = {
                    "columns": numeric_cols,
                    "values": corr_df.to_numpy().tolist()
                }
                
                # Top correlated pair scatter plot (# Phase 4+)
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
                    logger.warning(f"Could not calculate scatter plot data: {e}", extra=log_extra)
                
            # 4.2 Distribution Chart (#50)
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
            logger.error(f"Error calculating chart data: {str(chart_err)}", extra=log_extra)
            
        self.update_state(state='PROGRESS', meta={'current': 100, 'total': 100, 'status': 'Process Completed!'})
        logger.info("Data engine successfully completed all operations.", extra=log_extra)
        
        return {
            'status': 'Task completed successfully!',
            'original_file': file_path,
            'cleaned_file_path': cleaned_file_path,
            'metadata': metadata,
            'ai_decisions': ai_decisions,
            'chart_data': chart_data
        }
        
    except Exception as general_error:
        # Catch unexpected outer errors to prevent Celery worker crash
        logger.critical(f"SYSTEM CRASH PREVENTED: {str(general_error)}", extra=log_extra)
        self.update_state(state='FAILED_TASK', meta={'status': f'Error: {str(general_error)}'})
        return {"status": "FAILED", "error": str(general_error)}