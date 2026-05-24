import os
import re
import csv
import json
import math

def calculate_medians_and_means(rows):
    """
    Helper to calculate general averages and metrics in pure Python.
    """
    salaries = [float(r["salary_avg"]) for r in rows if r["salary_avg"]]
    if not salaries:
        return 110000.0
    return sum(salaries) / len(salaries)

def train_pure_ml_pipeline(cleaned_csv_path="data/processed/job_postings_cleaned.csv", output_dir="models"):
    """
    Trains pure-Python statistical ML models and exports parameters in JSON format.
    Ensures zero reliance on Numpy, Pandas, or Scikit-learn DLLs.
    """
    print("\n--- Training Pure-Python ML Model Pipeline ---")
    
    if not os.path.exists(cleaned_csv_path):
        raise FileNotFoundError(f"Cleaned CSV not found at {cleaned_csv_path}.")
        
    # Load dataset
    rows = []
    with open(cleaned_csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "job_title": r["job_title"],
                "company": r["company"],
                "job_category": r["job_category"],
                "job_type": r["job_type"],
                "experience_years": float(r["experience_years"]),
                "salary_avg": float(r["salary_avg"]),
                "location_city": r["location_city"],
                "skills_cleaned": r["skills_cleaned"]
            })
            
    num_records = len(rows)
    print(f"Loaded {num_records:,} records for training.")
    
    # ----------------------------------------------------
    # Model 1: Additive Salary Regressor Training
    # ----------------------------------------------------
    # We want to fit: salary = Base + Cat_premium + City_premium + Type_premium + Exp * Exp_slope + Skill_premiums
    
    # 1. Base Global Average
    global_avg = sum(r["salary_avg"] for r in rows) / num_records
    print(f"  Global Baseline Salary: ${global_avg:,.2f} USD")
    
    # 2. Fit Experience slope
    # Simple linear correlation estimate: delta_salary / delta_exp
    exp_salaries = {} # exp -> list of salaries
    for r in rows:
        exp = int(r["experience_years"])
        if exp not in exp_salaries:
            exp_salaries[exp] = []
        exp_salaries[exp].append(r["salary_avg"])
        
    # Get mean per experience year
    exp_means = {exp: sum(sals)/len(sals) for exp, sals in exp_salaries.items()}
    # Compute average slope between consecutive years
    slopes = []
    for exp in sorted(exp_means.keys()):
        if exp + 1 in exp_means:
            slopes.append(exp_means[exp+1] - exp_means[exp])
            
    experience_slope = sum(slopes)/len(slopes) if slopes else 9500.0
    print(f"  Fitted Experience Slope: +${experience_slope:,.2f} / year")
    
    # Subtract experience effect to isolate other variables
    # Residual = salary - (experience * slope)
    for r in rows:
        r["residual"] = r["salary_avg"] - (r["experience_years"] * experience_slope)
        
    # 3. Fit Job Category offsets
    cat_residuals = {}
    for r in rows:
        cat = r["job_category"]
        if cat not in cat_residuals:
            cat_residuals[cat] = []
        cat_residuals[cat].append(r["residual"])
    category_offsets = {cat: (sum(resids)/len(resids)) - global_avg for cat, resids in cat_residuals.items()}
    
    # 4. Fit City offsets
    city_residuals = {}
    for r in rows:
        city = r["location_city"]
        if city not in city_residuals:
            city_residuals[city] = []
        city_residuals[city].append(r["residual"])
    city_offsets = {city: (sum(resids)/len(resids)) - global_avg for city, resids in city_residuals.items()}
    
    # 5. Fit Job Type offsets
    type_residuals = {}
    for r in rows:
        jtype = r["job_type"]
        if jtype not in type_residuals:
            type_residuals[jtype] = []
        type_residuals[jtype].append(r["residual"])
    type_offsets = {jtype: (sum(resids)/len(resids)) - global_avg for jtype, resids in type_residuals.items()}
    
    # 6. Top Skills and Skill offsets
    all_skills = []
    for r in rows:
        skills = [s.strip() for s in r["skills_cleaned"].split(",") if s.strip() != ""]
        all_skills.extend(skills)
        
    # Count frequencies
    skill_freq = {}
    for s in all_skills:
        skill_freq[s] = skill_freq.get(s, 0) + 1
        
    # Select top 50 skills
    top_50_skills = sorted(skill_freq.keys(), key=lambda x: skill_freq[x], reverse=True)[:50]
    
    # Fit offset for each skill
    # Compare average residual of jobs with skill vs average residual of jobs without skill
    skill_offsets = {}
    for skill in top_50_skills:
        with_skill = []
        without_skill = []
        for r in rows:
            if skill in r["skills_cleaned"]:
                with_skill.append(r["residual"])
            else:
                without_skill.append(r["residual"])
                
        mean_with = sum(with_skill)/len(with_skill) if with_skill else global_avg
        mean_without = sum(without_skill)/len(without_skill) if without_skill else global_avg
        # Offset premium is the difference
        skill_offsets[skill] = (mean_with - mean_without) * 0.45 # slightly scaled to prevent multi-skill inflation
        
    print(f"  Fitted Skill Premiums (Top 5): {sorted(skill_offsets.items(), key=lambda x: x[1], reverse=True)[:5]}")
    
    # Assemble Salary Predictor Assets
    salary_predictor = {
        "global_average": global_avg,
        "experience_slope": experience_slope,
        "category_offsets": category_offsets,
        "city_offsets": city_offsets,
        "type_offsets": type_offsets,
        "skill_offsets": skill_offsets,
        "top_50_skills": top_50_skills
    }
    
    # ----------------------------------------------------
    # Model 2: Job Category Keyword Text Classifier
    # ----------------------------------------------------
    # Analyze words in title & skills to associate with categories
    category_vocab = {} # category -> {word -> count}
    
    for r in rows:
        cat = r["job_category"]
        if cat not in category_vocab:
            category_vocab[cat] = {}
            
        # Combine title and skills into words
        text = (r["job_title"] + " " + r["skills_cleaned"]).lower()
        words = re.findall(r'\b\w+\b', text)
        for w in words:
            if len(w) > 2: # filter out tiny words
                category_vocab[cat][w] = category_vocab[cat].get(w, 0) + 1
                
    # Normalize frequencies to probabilities/scores to avoid volume bias
    vocab_scores = {}
    for cat, words_freq in category_vocab.items():
        total_words = sum(words_freq.values())
        vocab_scores[cat] = {w: (cnt / total_words) * 1000 for w, cnt in words_freq.items()}
        
    classifier = {
        "vocab_scores": vocab_scores,
        "categories": ["AI/ML", "Data Science", "Software Engineering", "Full-Stack", "DevOps/Cloud"]
    }
    
    # ----------------------------------------------------
    # Model 3: Co-occurrence Skill Recommender
    # ----------------------------------------------------
    # Compute skill-to-skill links
    skill_relations = {} # skill -> {other_skill -> frequency}
    
    for r in rows:
        skills = [s.strip() for s in r["skills_cleaned"].split(",") if s.strip() != ""]
        for s1 in skills:
            if s1 not in skill_relations:
                skill_relations[s1] = {}
            for s2 in skills:
                if s1 != s2:
                    skill_relations[s1][s2] = skill_relations[s1].get(s2, 0) + 1
                    
    # Select top 5 recommended skills for each skill
    recommendations = {}
    for skill, relations in skill_relations.items():
        top_recs = sorted(relations.keys(), key=lambda x: relations[x], reverse=True)[:5]
        recommendations[skill] = top_recs
        
    recommender = {
        "cooccurrences": recommendations,
        "all_skills_list": sorted(list(skill_relations.keys()))
    }
    
    # ----------------------------------------------------
    # Save Compiled Models as JSON
    # ----------------------------------------------------
    os.makedirs(output_dir, exist_ok=True)
    model_filepath = os.path.join(output_dir, "pure_ml_assets.json")
    
    ml_assets = {
        "salary_predictor": salary_predictor,
        "classifier": classifier,
        "recommender": recommender
    }
    
    with open(model_filepath, "w", encoding="utf-8") as f:
        json.dump(ml_assets, f, indent=4)
        
    print(f"All pure-Python ML assets compiled successfully! Saved to '{model_filepath}'. Size: {os.path.getsize(model_filepath)/1024:.2f} KB")
    return True

if __name__ == "__main__":
    train_pure_ml_pipeline()
