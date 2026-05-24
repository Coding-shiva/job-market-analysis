import os
import csv
import json
import re
import sqlite3

def verify_pipeline():
    print("========================================================")
    print("[DIAGNOSTIC] PURE-PYTHON PIPELINE & MODEL DIAGNOSTIC TESTS")
    print("========================================================")
    
    # 1. Check File System Artifacts
    files_to_check = {
        "Raw Dataset": "data/raw/job_postings_raw.csv",
        "Cleaned Dataset": "data/processed/job_postings_cleaned.csv",
        "SQLite DB": "data/job_market.db",
        "Pure ML Model Assets": "models/pure_ml_assets.json"
    }
    
    missing_files = []
    print("\n[FILES] Checking system files:")
    for name, path in files_to_check.items():
        if os.path.exists(path):
            size_kb = os.path.getsize(path) / 1024
            print(f"  [OK] {name} exists at '{path}' ({size_kb:.2f} KB)")
        else:
            print(f"  [MISSING] {name} not found at '{path}'")
            missing_files.append(path)
            
    if missing_files:
        print("\n[ERROR] Diagnostics failed due to missing files. Please run the full pipeline.")
        return False
        
    # 2. Check Cleaned DataFrame Integrity
    print("\n[DATASET] Checking Cleaned Dataset Dimensions:")
    row_count = 0
    with open("data/processed/job_postings_cleaned.csv", "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for _ in reader:
            row_count += 1
            
    print(f"  Row Count: {row_count:,}")
    print(f"  Columns: {header}")
    
    assert row_count >= 50000, f"Error: Dataset row count {row_count} is below the required 50,000 threshold."
    print("  [PASS] Dataset meets the 50,000+ job listings requirement.")
    
    # 3. Check SQLite database integrity
    print("\n[DATABASE] Checking SQLite Relational Tables:")
    conn = sqlite3.connect("data/job_market.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM jobs")
    jobs_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM job_skills")
    skills_count = cursor.fetchone()[0]
    
    print(f"  Jobs Table count: {jobs_count:,}")
    print(f"  Job Skills (Normalized) count: {skills_count:,}")
    
    assert jobs_count > 0, "Error: SQLite jobs table is empty."
    assert skills_count > 0, "Error: SQLite job_skills table is empty."
    conn.close()
    print("  [PASS] SQLite tables parsed and populated successfully.")
    
    # 4. Check ML model inference
    print("\n[INFERENCE] Performing Model Inference Tests:")
    try:
        with open("models/pure_ml_assets.json", "r", encoding="utf-8") as f:
            ml_assets = json.load(f)
            
        salary_predictor = ml_assets["salary_predictor"]
        
        # Test Input Parameters
        category = "AI/ML"
        city = "San Francisco"
        jtype = "Remote"
        experience = 4.0
        selected_skills = ["Python", "PyTorch", "SQL"]
        
        # Pure Python Inference logic
        predicted_avg = salary_predictor["global_average"]
        predicted_avg += salary_predictor["category_offsets"].get(category, 0)
        predicted_avg += salary_predictor["city_offsets"].get(city, 0)
        predicted_avg += salary_predictor["type_offsets"].get(jtype, 0)
        predicted_avg += experience * salary_predictor["experience_slope"]
        
        for skill in selected_skills:
            predicted_avg += salary_predictor["skill_offsets"].get(skill, 0)
            
        print(f"  Mock Input Parameters:")
        print(f"    - Category: {category} | Arrangement: {jtype} | City: {city} | Exp: {experience} years")
        print(f"    - Skills: {', '.join(selected_skills)}")
        print(f"  Predicted Salary Output: Rs {predicted_avg:,.2f} INR")
        
        assert predicted_avg > 1000000, "Error: Predicted salary is implausibly low."
        print("  [PASS] Salary Prediction Engine inference test passed.")
        
    except Exception as e:
        print(f"  [FAIL] Model validation encountered an error: {e}")
        return False
        
    # 5. Check text classifier inference
    try:
        classifier = ml_assets["classifier"]
        mock_text = "Senior Deep Learning Engineer working with LLMs PyTorch Transformers"
        
        # Pure-Python classifier scoring
        words = re.findall(r'\b\w+\b', mock_text.lower())
        best_cat = "Software Engineering"
        best_score = -1
        
        for cat in classifier["categories"]:
            score = 0
            scores_dict = classifier["vocab_scores"].get(cat, {})
            for w in words:
                score += scores_dict.get(w, 0)
            if score > best_score:
                best_score = score
                best_cat = cat
                
        print(f"  Classifier Test: '{mock_text}' -> Classified as: '{best_cat}'")
        
        assert best_cat == "AI/ML", f"Error: Category classifier failed, got {best_cat}"
        print("  [PASS] Job Category Text Classifier test passed.")
    except Exception as e:
        print(f"  [FAIL] Classifier validation encountered an error: {e}")
        return False
        
    print("\n========================================================")
    print("[SUCCESS] ALL DIAGNOSTIC TESTS PASSED SUCCESSFULLY! PIPELINE IS HEALTHY.")
    print("========================================================")
    return True

if __name__ == "__main__":
    verify_pipeline()
