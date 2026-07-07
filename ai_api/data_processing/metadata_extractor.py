import polars as pl
import json

def extract_metadata(file_path: str) -> str:
    """
    Reads a CSV file using Polars and extracts a metadata summary
    for the LLM. It does NOT return the entire dataset to the LLM.
    """
    try:
        # Polars reads very fast, but for huge files we could use scan_csv.
        # Here we read to get accurate unique counts and nulls.
        df = pl.read_csv(file_path, ignore_errors=True)
        
        # Get column names and types
        schema = {col: str(dtype) for col, dtype in df.schema.items()}
        
        # Get null counts
        null_counts = df.null_count().to_dicts()[0]
        
        # Get unique value counts
        unique_counts = {col: df[col].n_unique() for col in df.columns}
        
        # Get first 5 rows
        head_data = df.head(5).to_dicts()
        
        metadata = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "schema": schema,
            "null_counts": null_counts,
            "unique_counts": unique_counts,
            "sample_data": head_data
        }
        
        return json.dumps(metadata, indent=2, default=str)
    except Exception as e:
        return f'{{"error": "Error extracting metadata: {str(e)}"}}'
