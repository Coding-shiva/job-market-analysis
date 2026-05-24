import os
import csv
import random
from datetime import datetime, timedelta

def generate_job_market_data(num_records=55000, output_path="data/raw/job_postings_raw.csv"):
    """
    Generates a realistic but messy synthetic dataset in pure Python (no pandas or numpy).
    """
    print(f"Starting synthetic job postings generation ({num_records} records)...")
    
    # Setup directories
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Set seed for reproducibility
    random.seed(42)
    
    # 1. Base Tech Categories and Titles
    categories = {
        "AI/ML": {
            "titles": [
                "Machine Learning Engineer", "AI Research Scientist", "Computer Vision Engineer", 
                "NLP Engineer", "Deep Learning Engineer", "LLM Engineer", "AI Engineer",
                "MLOps Engineer", "Data Scientist - AI Specialization"
            ],
            "skills": ["Python", "PyTorch", "TensorFlow", "scikit-learn", "Keras", "Transformers", "SQL", "Git", "Docker", "AWS", "MLflow", "Kubernetes", "C++", "Hugging Face"],
            "base_salary": (130000, 220000),
            "experience_range": (2, 10)
        },
        "Data Science": {
            "titles": [
                "Data Scientist", "Lead Data Scientist", "Senior Data Analyst", "Data Analyst", 
                "Quantitative Analyst", "Data Engineer", "Senior Data Engineer", "Analytics Engineer",
                "Business Intelligence Developer"
            ],
            "skills": ["Python", "SQL", "Pandas", "NumPy", "R", "Tableau", "Power BI", "Spark", "Hadoop", "AWS", "Snowflake", "dbt", "Airflow", "Scala", "Excel"],
            "base_salary": (90000, 170000),
            "experience_range": (0, 8)
        },
        "Software Engineering": {
            "titles": [
                "Software Engineer", "Senior Software Engineer", "Backend Engineer", 
                "Systems Engineer", "Embedded Systems Developer", "C++ Developer", 
                "Java Software Engineer", "Go Software Developer", "Staff Engineer"
            ],
            "skills": ["Java", "C++", "Go", "Python", "Rust", "SQL", "Docker", "Kubernetes", "AWS", "Git", "Spring Boot", "Microservices", "Linux", "gRPC"],
            "base_salary": (100000, 190000),
            "experience_range": (1, 12)
        },
        "Full-Stack": {
            "titles": [
                "Full Stack Developer", "Senior Full Stack Engineer", "Frontend Engineer", 
                "React Developer", "UI/UX Developer", "Web Applications Developer", 
                "JavaScript Engineer", "TypeScript Developer", "Node.js Developer"
            ],
            "skills": ["JavaScript", "TypeScript", "React", "Node.js", "HTML5", "CSS3", "Next.js", "Vue.js", "Angular", "Express.js", "PostgreSQL", "MongoDB", "Tailwind CSS", "Git"],
            "base_salary": (85000, 160000),
            "experience_range": (0, 8)
        },
        "DevOps/Cloud": {
            "titles": [
                "DevOps Engineer", "Cloud Solutions Architect", "Site Reliability Engineer", 
                "Platform Engineer", "Cloud Security Engineer", "Infrastructure Engineer"
            ],
            "skills": ["AWS", "Azure", "GCP", "Terraform", "Docker", "Kubernetes", "Ansible", "Jenkins", "CI/CD", "Linux", "Python", "Bash", "Prometheus", "Grafana"],
            "base_salary": (110000, 185000),
            "experience_range": (2, 10)
        }
    }
    
    companies = [
        "Google", "Microsoft", "Meta", "Amazon", "Apple", "Netflix", "Salesforce", "Stripe", "Uber", "Lyft", 
        "Airbnb", "Snowflake", "Databricks", "OpenAI", "Anthropic", "Adobe", "Oracle", "IBM", "Intel", "NVIDIA",
        "Palantir", "Tesla", "SpaceX", "Coinbase", "Shopify", "Spotify", "Pinterest", "Twitter", "Slack", "Zoom",
        "JPMorgan Chase", "Goldman Sachs", "Morgan Stanley", "Fidelity", "Capital One", "Bloomberg", "Stripe",
        "Lockheed Martin", "Boeing", "Raytheon", "Pfizer", "Moderna", "Johnson & Johnson", "UnitedHealth",
        "Walmart", "Target", "Nike", "Ford", "General Motors", "Toyota", "Chevron", "ExxonMobil", "General Electric",
        "Siemens", "ASML", "Accenture", "Deloitte", "McKinsey & Company", "Boston Consulting Group", "Infosys",
        "TCS", "Wipro", "Cognizant", "Capgemini", "Epic Systems", "Cerner", "Athenahealth", "Stripe", "Plaid",
        "Scale AI", "Hugging Face", "Midjourney", "Pinecone", "LangChain", "Vercel", "Supabase", "Prisma", "Sentry",
        "Datadog", "Dynatrace", "New Relic", "Splunk", "Elastic", "Confluent", "MongoDB Inc.", "HashiCorp", "GitLab"
    ]
    
    locations = [
        {"city": "San Francisco", "state": "CA", "country": "USA", "remote_weight": 0.3},
        {"city": "New York", "state": "NY", "country": "USA", "remote_weight": 0.25},
        {"city": "Seattle", "state": "WA", "country": "USA", "remote_weight": 0.2},
        {"city": "Austin", "state": "TX", "country": "USA", "remote_weight": 0.35},
        {"city": "Boston", "state": "MA", "country": "USA", "remote_weight": 0.2},
        {"city": "Chicago", "state": "IL", "country": "USA", "remote_weight": 0.25},
        {"city": "Los Angeles", "state": "CA", "country": "USA", "remote_weight": 0.3},
        {"city": "Denver", "state": "CO", "country": "USA", "remote_weight": 0.4},
        {"city": "Atlanta", "state": "GA", "country": "USA", "remote_weight": 0.3},
        {"city": "London", "state": "ENG", "country": "UK", "remote_weight": 0.25},
        {"city": "Toronto", "state": "ON", "country": "Canada", "remote_weight": 0.3},
        {"city": "Vancouver", "state": "BC", "country": "Canada", "remote_weight": 0.35},
        {"city": "Bangalore", "state": "KA", "country": "India", "remote_weight": 0.2},
        {"city": "Hyderabad", "state": "TG", "country": "India", "remote_weight": 0.2},
        {"city": "Berlin", "state": "BE", "country": "Germany", "remote_weight": 0.3},
        {"city": "Paris", "state": "IDF", "country": "France", "remote_weight": 0.25},
        {"city": "Sydney", "state": "NSW", "country": "Australia", "remote_weight": 0.3}
    ]
    
    industries = ["Technology", "Finance", "Healthcare", "E-commerce", "Auto & Aerospace", "Consulting", "Defense", "Entertainment"]
    job_types = ["Full-Time", "Contract", "Part-Time", "Internship"]
    
    # Date ranges
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    headers = [
        "Job Title", "Company", "Location", "Salary", "Experience Required", 
        "Skills Required", "Job Type", "Industry", "Posting Date"
    ]
    
    records = []
    
    # Select categories randomly by weighted choices (using random.choices is a standard python library feature!)
    cat_keys = list(categories.keys())
    cat_weights = [0.22, 0.22, 0.22, 0.22, 0.12]
    
    for i in range(num_records):
        # Weighted selection of category
        cat_name = random.choices(cat_keys, weights=cat_weights, k=1)[0]
        cat_info = categories[cat_name]
        
        job_title = random.choice(cat_info["titles"])
        company = random.choice(companies)
        
        loc = random.choice(locations)
        setup_choices = ["Remote", "Onsite", "Hybrid"]
        setup_weights = [loc["remote_weight"], 0.45, 0.55 - loc["remote_weight"]]
        job_setup = random.choices(setup_choices, weights=setup_weights, k=1)[0]
        
        if job_setup == "Remote" and random.random() < 0.8:
            location_str = "Remote"
        else:
            if loc["country"] == "USA":
                location_str = f"{loc['city']}, {loc['state']}"
            else:
                location_str = f"{loc['city']}, {loc['country']}"
                
        industry = random.choice(industries)
        job_type = random.choices(job_types, weights=[0.85, 0.10, 0.03, 0.02], k=1)[0]
        
        # Select skills
        num_skills = random.randint(3, 8)
        selected_skills = random.sample(cat_info["skills"], min(num_skills, len(cat_info["skills"])))
        
        if random.random() < 0.3:
            other_cat = random.choice([k for k in categories.keys() if k != cat_name])
            selected_skills.append(random.choice(categories[other_cat]["skills"]))
            
        skills_str = ", ".join(list(set(selected_skills)))
        
        # Experience Setup
        min_exp, max_exp = cat_info["experience_range"]
        if "Senior" in job_title or "Lead" in job_title:
            exp_years = random.randint(max(5, min_exp + 3), max_exp + 4)
        elif "Staff" in job_title or "Principal" in job_title or "Architect" in job_title:
            exp_years = random.randint(max(8, min_exp + 5), max_exp + 7)
        elif "Junior" in job_title or "Analyst" in job_title or "Intern" in job_title:
            exp_years = random.randint(0, min(2, min_exp))
        else:
            exp_years = random.randint(min_exp, max_exp)
            
        exp_style = random.random()
        if exp_style < 0.4:
            experience_str = f"{exp_years} - {exp_years + random.randint(2, 4)} years"
        elif exp_style < 0.7:
            experience_str = f"{exp_years}+ years"
        elif exp_style < 0.85:
            experience_str = f"{exp_years} yrs"
        elif exp_style < 0.92:
            experience_str = "Senior Level" if exp_years >= 6 else "Entry Level" if exp_years <= 1 else "Mid Level"
        else:
            experience_str = ""  # Missing value
            
        # Base Salary
        base_min, base_max = cat_info["base_salary"]
        base_min += exp_years * 8000
        base_max += exp_years * 11000
        
        col_multiplier = 1.0
        if loc["city"] in ["San Francisco", "New York", "Seattle", "London"]:
            col_multiplier = 1.25
        elif loc["city"] in ["Austin", "Boston", "Los Angeles", "Toronto", "Sydney"]:
            col_multiplier = 1.1
        elif loc["city"] in ["Bangalore", "Hyderabad"]:
            col_multiplier = 0.55
            
        final_min = int(base_min * col_multiplier)
        final_max = int(base_max * col_multiplier)
        
        salary_style = random.random()
        curr = "$"
        if loc["country"] == "UK":
            curr = "£"
            final_min = int(final_min * 0.8)
            final_max = int(final_max * 0.8)
        elif loc["country"] in ["Germany", "France"]:
            curr = "€"
            final_min = int(final_min * 0.9)
            final_max = int(final_max * 0.9)
        elif loc["country"] == "India":
            curr = "₹"
            final_min = int(final_min * 83)
            final_max = int(final_max * 83)
            
        if salary_style < 0.45:
            salary_str = f"{curr}{final_min:,} - {curr}{final_max:,}"
        elif salary_style < 0.65:
            salary_str = f"{final_min // 1000}k - {final_max // 1000}k"
        elif salary_style < 0.75:
            avg_salary = (final_min + final_max) // 2
            salary_str = f"{curr}{avg_salary:,} per year"
        elif salary_style < 0.85:
            hourly_min = int(final_min / 2000)
            hourly_max = int(final_max / 2000)
            salary_str = f"{curr}{hourly_min}/hr - {curr}{hourly_max}/hr"
        elif salary_style < 0.93:
            salary_str = random.choice(["Competitive", "Competitive Salary", "DOE", "Not Disclosed", "Confidential"])
        else:
            salary_str = ""
            
        posting_delta = random.randint(0, 180)
        if random.random() < 0.6:
            posting_delta = int(posting_delta * 0.5)
        posting_date = start_date + timedelta(days=posting_delta)
        posting_date_str = posting_date.strftime("%Y-%m-%d")
        
        records.append([
            job_title,
            company,
            location_str,
            salary_str,
            experience_str,
            skills_str,
            job_setup,
            industry,
            posting_date_str
        ])
        
    # Introduce duplicates (around 1.5%)
    num_dupes = int(num_records * 0.015)
    for _ in range(num_dupes):
        records.append(random.choice(records))
        
    # Shuffle to mix duplicates
    random.shuffle(records)
    
    # Save raw CSV in pure Python
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(records)
        
    print(f"Dataset generated successfully! Saved to '{output_path}'. Total rows (with duplicates): {len(records)}")
    return True

if __name__ == "__main__":
    generate_job_market_data()
