import json
from backend.app.services.data_engine import DataEngine

def main():
    print("=" * 50)
    print("Starting Autonomous Cleaning Test...")
    print("=" * 50)
    
    csv_path = "test_data.csv"
    output_path = "cleaned_data_output.csv"
    
    # Mock cleaning plan simulating LLM decisions
    mock_llm_plan = {
        "drop_columns": [],
        "fill_missing": [
            {"column": "price", "strategy": "mean"},
            {"column": "is_active", "strategy": "mode"}
        ],
        "cast_types": [
            {"column": "sale_date", "target_type": "Datetime"}
        ]
    }
    
    try:
        engine = DataEngine(csv_path)
        
        # Step 1: Initial Profiling
        metadata = engine.initialize_pipeline()
        print("\n[STEP 1] Metadata extracted successfully.")
        
        # Step 2: Autonomous Cleaning and Streaming Export
        print(f"\n[STEP 2] Applying LLM cleaning plan via streaming...")
        engine.execute_cleaning(mock_llm_plan, output_path)
        print(f"[SUCCESS] Cleaned data written to: {output_path}")
        
    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {str(e)}")
        
    print("=" * 50)

if __name__ == "__main__":
    main()