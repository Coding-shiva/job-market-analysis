import os
import sys
import subprocess
import time

def run_step(step_name, script_path):
    """
    Utility to run a python script as a subprocess, timing it and handling errors.
    """
    print(f"\n========================================================")
    print(f"[RUNNING] STEP: {step_name}")
    print(f"Executing: python {script_path}")
    print(f"========================================================")
    
    start_time = time.time()
    
    # Run the script using the current python executable
    result = subprocess.run([sys.executable, script_path], capture_output=False)
    
    elapsed = time.time() - start_time
    
    if result.returncode == 0:
        print(f"[SUCCESS] {step_name} completed successfully in {elapsed:.2f} seconds!")
        return True
    else:
        print(f"[FAILED] {step_name} failed! Please check logs and resolve runtime errors.")
        return False

def main():
    print("""
    ========================================================
       JOB MARKET ANALYTICS - ORCHESTRATION PIPELINE
    ========================================================
    This orchestrator will execute the end-to-end pipeline:
    1. Generate 55,000+ Raw Messy Job Listings
    2. Clean/Standardize Salaries, Experience, and Locations
    3. Ingest Data & Normalize relational SQL database tables
    4. Train & Serialise Machine Learning models (Regressors, Classifiers)
    """)
    
    pipeline_start = time.time()
    
    # Define steps
    steps = [
        ("Synthetic Data Generator", "src/data_generator.py"),
        ("Data Cleaning & Feature Engineering", "src/data_cleaning.py"),
        ("SQL Database Ingestion & Relational Setup", "src/database.py"),
        ("Machine Learning Model Compilation & Training", "src/ml_models.py")
    ]
    
    for step_name, script in steps:
        if not os.path.exists(script):
            print(f"[ERROR] Core script not found: '{script}'. Ensure you are in the correct directory.")
            sys.exit(1)
            
        success = run_step(step_name, script)
        if not success:
            sys.exit(1)
            
    total_elapsed = time.time() - pipeline_start
    print(f"\n========================================================")
    print(f"[SUCCESS] END-TO-END PIPELINE COMPLETED in {total_elapsed:.2f} seconds!")
    print(f"========================================================")
    print("\n-> To launch the interactive Dashboard, run:")
    print("   python app/server.py")
    print("   (Then open http://localhost:8501 in your browser)")
    print("\n   Alternative (requires Streamlit C-extensions):")
    print("   streamlit run app/main.py")
    print("========================================================\n")

if __name__ == "__main__":
    main()
