import os
import re
import csv
import math

def clean_salary(val, location_str):
    """
    Parses messy salary strings and standardizes them to INR (Indian Rupee) annual salaries.
    Pure Python implementation.
    """
    if not val or not isinstance(val, str) or val.strip() == "":
        return None, None, None
        
    val_clean = val.lower().strip()
    
    # Check for confidential/competitive statements
    if any(term in val_clean for term in ["competitive", "doe", "disclosed", "confidential", "negotiable"]):
        return None, None, None

    # Identify currency multiplier to convert to INR (₹)
    multiplier = 83.0  # Default assumption is USD ($) if no symbol, so multiply by 83 to get INR
    if "₹" in val_clean or "inr" in val_clean or "rs" in val_clean:
        multiplier = 1.0   # Already in INR
    elif "£" in val_clean:
        multiplier = 105.0 # Convert GBP to INR
    elif "€" in val_clean:
        multiplier = 90.0  # Convert EUR to INR
    elif "$" in val_clean:
        multiplier = 83.0  # Convert USD to INR
        
    # Check if hourly rate
    is_hourly = False
    if "/hr" in val_clean or "hr" in val_clean or "hour" in val_clean:
        is_hourly = True

    # Standardize 'k' suffixes
    val_clean = val_clean.replace(",", "")
    val_clean = re.sub(r'(\d+)\s*k', lambda m: str(int(m.group(1)) * 1000), val_clean)
    
    # Find all numbers
    numbers = re.findall(r'\d+(?:\.\d+)?', val_clean)
    numbers = [float(n) for n in numbers]
    
    if len(numbers) == 0:
        return None, None, None
        
    if len(numbers) >= 2:
        sal_min = numbers[0]
        sal_max = numbers[1]
    else:
        sal_min = numbers[0] * 0.9
        sal_max = numbers[0] * 1.1
        
    if is_hourly:
        sal_min = sal_min * 2000
        sal_max = sal_max * 2000
        
    sal_min = sal_min * multiplier
    sal_max = sal_max * multiplier
    
    # Sanity checks in INR (e.g. min 1 Lakh per year, max 10 Crores per year)
    if sal_min < 100000 or sal_min > 100000000:
        if is_hourly and (sal_min / 2000) > 100000:
            sal_min /= 2000
            sal_max /= 2000
        else:
            return None, None, None

    sal_avg = (sal_min + sal_max) / 2
    return round(sal_min, 2), round(sal_max, 2), round(sal_avg, 2)


def clean_experience(val):
    """
    Parses messy experience strings and extracts numeric experience years.
    Pure Python.
    """
    if not val or not isinstance(val, str) or val.strip() == "":
        return 2.0  # Default
        
    val_clean = val.lower().strip()
    
    numbers = re.findall(r'\d+', val_clean)
    if len(numbers) > 0:
        return float(numbers[0])
        
    if "senior" in val_clean or "staff" in val_clean or "principal" in val_clean or "lead" in val_clean:
        return 6.0
    elif "mid" in val_clean:
        return 3.0
    elif "entry" in val_clean or "junior" in val_clean or "intern" in val_clean:
        return 0.0
        
    return 2.0


def categorize_title(title):
    """
    Maps job titles to a broader technical category.
    """
    if not title:
        return "Software Engineering"
    title_clean = title.lower()
    
    if any(term in title_clean for term in ["machine learning", "ml", "ai", "artificial intelligence", "computer vision", "nlp", "deep learning", "llm", "neural"]):
        return "AI/ML"
    elif any(term in title_clean for term in ["data scientist", "data science", "analyst", "analytics", "bi ", "business intelligence", "quantitative", "data engineer"]):
        return "Data Science"
    elif any(term in title_clean for term in ["full stack", "fullstack", "frontend", "front-end", "web dev", "react", "ui", "ux", "javascript", "typescript", "node"]):
        return "Full-Stack"
    elif any(term in title_clean for term in ["devops", "cloud", "sre", "reliability", "infrastructure", "platform engineer", "systems engineer"]):
        return "DevOps/Cloud"
    else:
        return "Software Engineering"


def parse_location(location):
    """
    Normalizes location strings to City, State, Country.
    """
    if not location or not isinstance(location, str) or location.strip() == "":
        return "Unknown", "Unknown", "Unknown"
        
    parts = [p.strip() for p in location.split(",")]
    
    if len(parts) == 1:
        loc_val = parts[0]
        if loc_val.lower() == "remote":
            return "Remote", "Remote", "Remote"
        return loc_val, "Unknown", "Unknown"
        
    elif len(parts) == 2:
        city, region = parts[0], parts[1]
        if len(region) == 2 and region.isupper():
            return city, region, "USA"
        else:
            return city, "Unknown", region
            
    return parts[0], "Unknown", parts[-1]


def run_data_cleaning_pipeline(input_path="data/raw/job_postings_raw.csv", output_path="data/processed/job_postings_cleaned.csv"):
    """
    Cleans raw CSV data and implements imputation without pandas/numpy.
    """
    print(f"Loading raw data from '{input_path}'...")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Raw data file not found at {input_path}.")
        
    # Read rows
    raw_rows = []
    with open(input_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_rows.append(row)
            
    initial_len = len(raw_rows)
    print(f"Loaded {initial_len:,} raw rows.")
    
    # 1. Deduplicate by converting rows to tuples (excluding date if slight difference, or complete row deduplication)
    seen = set()
    deduped_rows = []
    for row in raw_rows:
        # Deduplicate based on Title, Company, Location, Salary, Experience, Skills, Type, Industry
        key = (
            row["Job Title"], row["Company"], row["Location"], row["Salary"],
            row["Experience Required"], row["Skills Required"], row["Job Type"], row["Industry"]
        )
        if key not in seen:
            seen.add(key)
            deduped_rows.append(row)
            
    print(f"Dropped {initial_len - len(deduped_rows)} duplicates. Remaining: {len(deduped_rows):,}")
    
    # 2. First Pass: Compute categorization, basic cleaning, and gather salaries for median computation
    processed_rows = []
    salaries_by_cat_exp = {} # (category, experience_years) -> list of salaries
    salaries_by_cat = {}     # category -> list of salaries
    all_salaries = []
    
    for row in deduped_rows:
        job_title = row["Job Title"]
        company = row["Company"]
        location_raw = row["Location"]
        salary_raw = row["Salary"]
        experience_raw = row["Experience Required"]
        skills_raw = row["Skills Required"]
        job_type = row["Job Type"]
        industry = row["Industry"]
        posting_date = row["Posting Date"]
        
        job_category = categorize_title(job_title)
        experience_years = clean_experience(experience_raw)
        sal_min, sal_max, sal_avg = clean_salary(salary_raw, location_raw)
        
        city, state, country = parse_location(location_raw)
        
        # Skills clean
        skills = [s.strip() for s in skills_raw.split(",") if s.strip() != ""] if skills_raw else []
        if not skills:
            skills = ["Python", "SQL"]
        skills_cleaned = ", ".join(skills)
        
        processed_row = {
            "job_title": job_title,
            "company": company,
            "location_raw": location_raw,
            "salary_raw": salary_raw,
            "experience_raw": experience_raw,
            "skills_raw": skills_raw,
            "job_type": job_type,
            "industry": industry,
            "posting_date": posting_date,
            "job_category": job_category,
            "experience_years": experience_years,
            "salary_min": sal_min,
            "salary_max": sal_max,
            "salary_avg": sal_avg,
            "location_city": city,
            "location_state": state,
            "location_country": country,
            "skills_cleaned": skills_cleaned
        }
        
        processed_rows.append(processed_row)
        
        # Gather non-null average salaries for imputation
        if sal_avg is not None:
            # Store by category & experience
            key = (job_category, experience_years)
            if key not in salaries_by_cat_exp:
                salaries_by_cat_exp[key] = []
            salaries_by_cat_exp[key].append(sal_avg)
            
            # Store by category
            if job_category not in salaries_by_cat:
                salaries_by_cat[job_category] = []
            salaries_by_cat[job_category].append(sal_avg)
            
            all_salaries.append(sal_avg)
            
    # Calculate medians in pure Python
    def get_median(lst):
        if not lst:
            return 9130000.0
        sorted_lst = sorted(lst)
        n = len(sorted_lst)
        if n % 2 == 1:
            return sorted_lst[n // 2]
        else:
            return (sorted_lst[(n // 2) - 1] + sorted_lst[n // 2]) / 2.0
            
    medians_by_cat_exp = {key: get_median(val) for key, val in salaries_by_cat_exp.items()}
    medians_by_cat = {key: get_median(val) for key, val in salaries_by_cat.items()}
    global_median = get_median(all_salaries)
    
    # 3. Second Pass: Impute missing salaries and compile final clean list
    final_rows = []
    for row in processed_rows:
        if row["salary_avg"] is None:
            cat = row["job_category"]
            exp = row["experience_years"]
            
            # Try to get median for category + exp
            imputed_avg = medians_by_cat_exp.get((cat, exp))
            if imputed_avg is None:
                imputed_avg = medians_by_cat.get(cat, global_median)
                
            row["salary_avg"] = round(imputed_avg, 2)
            row["salary_min"] = round(imputed_avg * 0.9, 2)
            row["salary_max"] = round(imputed_avg * 1.1, 2)
            
        final_rows.append(row)
        
    # Sort final records by posting_date
    final_rows = sorted(final_rows, key=lambda x: x["posting_date"])
    
    # Save cleaned data to CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    headers = [
        "job_title", "company", "location_raw", "salary_raw", "experience_raw", 
        "skills_raw", "job_type", "industry", "posting_date", "job_category", 
        "experience_years", "salary_min", "salary_max", "salary_avg", 
        "location_city", "location_state", "location_country", "skills_cleaned"
    ]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in final_rows:
            writer.writerow(row)
            
    print(f"Data cleaning and feature engineering complete! Saved to '{output_path}'. Total rows: {len(final_rows):,}")
    return True

if __name__ == "__main__":
    run_data_cleaning_pipeline()
