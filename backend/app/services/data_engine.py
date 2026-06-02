import os
import polars as pl

class DataLoader:
    def __init__(self, file_path: str):
        """
        Initializes the DataLoader with a specific file path and extracts its extension.
        Ensures memory-efficient transformation of raw data files into Polars LazyFrames.
        """
        self.file_path = file_path
        self.file_ext = os.path.splitext(file_path)[1].lower()

    def load(self) -> pl.LazyFrame:
        """
        Selects and executes the optimal loading strategy based on the file extension.
        
        Returns:
            pl.LazyFrame: The scanned layout of the dataset ready for lazy evaluation.
        Raises:
            FileNotFoundError: If the specified file does not exist.
            ValueError: If the file format is not supported.
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")

        if self.file_ext == '.csv':
            return self._load_csv()
        elif self.file_ext in ['.xlsx', '.xls']:
            return self._load_excel()
        else:
            raise ValueError(f"Unsupported file format: {self.file_ext}")

    def _load_csv(self) -> pl.LazyFrame:
        """
        Scans the CSV file without loading it entirely into memory.
        Enables downstream optimizations and streaming capabilities.
        """
        # infer_schema_length=0 forces Polars to skip data type guessing and read everything as String safely.
        # encoding="iso-8859-1" handles special western/european symbols smoothly.
        return pl.scan_csv(
            self.file_path,
            encoding="utf8-lossy",
            infer_schema_length=0
        )

    def _load_excel(self) -> pl.LazyFrame:
        """
        Handles heavy Excel files by converting them into a temporary CSV format.
        Prevents memory spikes caused by standard Excel XML decompression.
        """
        # Generates a temporary CSV path using the original file's base name.
        temp_csv_path = self.file_path.replace(self.file_ext, "_temp.csv")
        
        # Reads the Excel file using high-performance underlying engines (e.g., fastexcel/calamine).
        df_excel = pl.read_excel(self.file_path)
        df_excel.write_csv(temp_csv_path)
        

        return pl.scan_csv(
            temp_csv_path,
            encoding="utf8-lossy",
            infer_schema_length=0
        )
    

class MetadataExtractor:
    def __init__(self, lazy_frame: pl.LazyFrame):
        """
        Initializes the MetadataExtractor with a Polars LazyFrame.
        Operates lazily to compute data profiles without memory overhead.
        """
        self.lf = lazy_frame

    def extract_summary(self) -> dict:
        """
        Computes a lightweight metadata summary of the dataset for LLM consumption.
        Maintains privacy by exposing only schema characteristics and missing data statistics.
        
        Returns:
            dict: A structural profile containing column names, data types, and null counts.
        """
        # Using the optimized collect_schema() method
        schema = self.lf.collect_schema()
        
        # Build a fast aggregation query to count missing values across all columns
        # Using Polars expressions ensuring parallel computation over all CPU cores
        null_counts_query = self.lf.select([
            pl.col(col_name).null_count().alias(col_name)
            for col_name in schema.keys()
        ])
        
        # Calculate total row count efficiently via a quick fetch
        total_rows = self.lf.select(pl.len()).collect().item()
        
        # Execute the null count aggregation query
        null_counts_df = null_counts_query.collect()
        
        # Construct the structured metadata dictionary
        metadata = {
            "total_rows": total_rows,
            "columns": []
        }
        
        for col_name, data_type in schema.items():
            null_count = null_counts_df.get_column(col_name).item()
            null_percentage = (null_count / total_rows) * 100 if total_rows > 0 else 0
            
            metadata["columns"].append({
                "column_name": col_name,
                "data_type": str(data_type),
                "null_count": null_count,
                "null_percentage": round(null_percentage, 2)
            })
            
        return metadata
    

class DataEngine:
    def __init__(self, file_path: str):
        """
        The main orchestrator for the DataSense autonomous cleaning pipeline.
        Manages the lifecycle of data loading, metadata profiling, and transformations.
        """
        self.file_path = file_path
        self.loader = DataLoader(file_path)
        self.lazy_frame = None

    def initialize_pipeline(self) -> dict:
        """
        Loads the dataset into a LazyFrame and extracts its core metadata summary.
        
        Returns:
            dict: The architectural profile and missing data metrics of the file.
        """
        self.lazy_frame = self.loader.load()
        extractor = MetadataExtractor(self.lazy_frame)
        return extractor.extract_summary()

    def execute_cleaning(self, cleaning_plan: dict, output_path: str) -> str:
        """
        Applies the LLM cleaning plan and exports the cleaned dataset using streaming mode.
        
        Args:
            cleaning_plan (dict): Strategies generated by the LLM agent.
            output_path (str): File path where the cleaned data will be saved.
        Returns:
            str: Destination path of the processed file.
        """
        if self.lazy_frame is None:
            self.lazy_frame = self.loader.load()

        # Initialize transformer and build the execution graph
        transformer = DataTransformer(self.lazy_frame)
        transformed_lf = transformer.transform(cleaning_plan)

        # Trigger execution in streaming mode to handle huge files efficiently without RAM spikes
        transformed_lf.sink_csv(output_path)
        
        return output_path
    

class DataTransformer:
    def __init__(self, lazy_frame: pl.LazyFrame):
        """
        Initializes the DataTransformer with a Polars LazyFrame.
        Applies cleaning configurations lazily to maximize execution performance.
        """
        self.lf = lazy_frame

    def transform(self, cleaning_plan: dict) -> pl.LazyFrame:
        """
        Executes a series of transformations on the LazyFrame based on the provided LLM cleaning plan.
        
        Args:
            cleaning_plan (dict): JSON-like dictionary containing cleaning strategies.
        Returns:
            pl.LazyFrame: The modified LazyFrame with applied transformation steps.
        """
        #Drop specified columns
        drop_cols = cleaning_plan.get("drop_columns", [])
        if drop_cols:
            self.lf = self.lf.drop(drop_cols)

        # Handle missing values based on the strategy
        for fill_task in cleaning_plan.get("fill_missing", []):
            col_name = fill_task.get("column")
            strategy = fill_task.get("strategy")
            
            if strategy == "mean":
                self.lf = self.lf.with_columns(
                    pl.col(col_name).fill_null(pl.col(col_name).mean())
                )
            elif strategy == "mode":
                # Mode extraction in Polars returns a Series, selecting the first element safely
                self.lf = self.lf.with_columns(
                    pl.col(col_name).fill_null(pl.col(col_name).mode().first())
                )
            elif strategy == "drop":
                self.lf = self.lf.filter(pl.col(col_name).is_not_null())

        # Cast data types dynamically
        for cast_task in cleaning_plan.get("cast_types", []):
            col_name = cast_task.get("column")
            target_type = cast_task.get("target_type")
            
            if target_type == "Datetime":
                # Automatically parses standard string format to Date/Datetime
                self.lf = self.lf.with_columns(
                    pl.col(col_name).str.to_datetime()
                )

        return self.lf