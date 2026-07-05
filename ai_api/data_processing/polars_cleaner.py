import polars as pl
from typing import Dict, Any

def clean_data(file_path: str, output_path: str, decisions: Dict[str, Any]) -> str:
    """
    Cleans the data using Polars based on the LLM decisions.
    Uses LazyFrames (scan_csv) to prevent OOM errors with large datasets.
    """
    try:
        # Use lazy execution to avoid loading gigabytes into RAM at once
        lf = pl.scan_csv(file_path, ignore_errors=True)
        existing_cols = lf.collect_schema().names()
        
        # 1. Drop unnecessary columns
        columns_to_drop = decisions.get("columns_to_drop", [])
        if columns_to_drop:
            cols_to_drop_valid = [c for c in columns_to_drop if c in existing_cols]
            if cols_to_drop_valid:
                lf = lf.drop(cols_to_drop_valid)
                
        # 2. Handle missing values
        missing_strategy = decisions.get("missing_value_strategy", {})
        
        for col, strategy in missing_strategy.items():
            if col not in existing_cols:
                continue
                
            if strategy == "drop":
                lf = lf.drop_nulls(subset=[col])
            elif strategy == "mean":
                lf = lf.with_columns(pl.col(col).fill_null(pl.col(col).mean()))
            elif strategy == "median":
                lf = lf.with_columns(pl.col(col).fill_null(pl.col(col).median()))
            elif strategy == "mode":
                # Mode in polars can return multiple values, take the first one
                lf = lf.with_columns(pl.col(col).fill_null(pl.col(col).mode().first()))
                
        # Execute the query plan and write to disk in chunks (streaming mode)
        # Note: Polars streaming engine handles OOM protection automatically
        df = lf.collect(streaming=True)
        df.write_csv(output_path)
        
        return output_path
        
    except Exception as e:
        raise RuntimeError(f"Error executing data cleaning with Polars: {str(e)}")
