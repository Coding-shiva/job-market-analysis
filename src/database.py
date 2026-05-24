import os
import csv
import sqlite3

class JobMarketDatabase:
    """
    Manages SQLite database storage and relational ingestion of cleaned job market data.
    Uses pure Python standard library sqlite3.
    """
    def __init__(self, db_path="data/job_market.db"):
        self.db_path = db_path
        self.db_dir = os.path.dirname(db_path)
        if self.db_dir:
            os.makedirs(self.db_dir, exist_ok=True)
        
    def create_tables(self):
        """
        Creates schema tables: jobs and job_skills (normalized relational table).
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. Create main jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_title TEXT,
                company TEXT,
                location_raw TEXT,
                salary_raw TEXT,
                experience_raw TEXT,
                skills_raw TEXT,
                job_type TEXT,
                industry TEXT,
                posting_date TEXT,
                job_category TEXT,
                experience_years REAL,
                salary_min REAL,
                salary_max REAL,
                salary_avg REAL,
                location_city TEXT,
                location_state TEXT,
                location_country TEXT,
                skills_cleaned TEXT
            )
        """)
        
        # 2. Create normalized skills table for fast joins/lookups
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                skill TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs(id)
            )
        """)
        
        # Create indexes for optimal performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_category ON jobs(job_category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_city ON jobs(location_city)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_skills_job_id ON job_skills(job_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_skills_name ON job_skills(skill)")
        
        conn.commit()
        conn.close()
        print("Database schema and indexes set up successfully.")
        
    def ingest_data(self, cleaned_csv_path="data/processed/job_postings_cleaned.csv"):
        """
        Loads the cleaned CSV data and populates SQLite tables using parameterized bulk inserts.
        """
        print(f"Ingesting cleaned data from '{cleaned_csv_path}' to database '{self.db_path}'...")
        if not os.path.exists(cleaned_csv_path):
            raise FileNotFoundError(f"Cleaned CSV not found at {cleaned_csv_path}. Run data cleaning first.")
            
        # 1. Read the cleaned CSV
        rows = []
        with open(cleaned_csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
                
        # Connect to DB and clear existing tables
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM jobs")
        cursor.execute("DELETE FROM job_skills")
        conn.commit()
        
        print(f"Loaded {len(rows):,} cleaned rows to ingest.")
        
        # 2. Bulk Insert main jobs
        # Compile parameterized queries
        job_insert_q = """
            INSERT INTO jobs (
                job_title, company, location_raw, salary_raw, experience_raw, 
                skills_raw, job_type, industry, posting_date, job_category, 
                experience_years, salary_min, salary_max, salary_avg, 
                location_city, location_state, location_country, skills_cleaned
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        job_data = []
        for r in rows:
            job_data.append((
                r["job_title"], r["company"], r["location_raw"], r["salary_raw"], r["experience_raw"],
                r["skills_raw"], r["job_type"], r["industry"], r["posting_date"], r["job_category"],
                float(r["experience_years"]), float(r["salary_min"]), float(r["salary_max"]), float(r["salary_avg"]),
                r["location_city"], r["location_state"], r["location_country"], r["skills_cleaned"]
            ))
            
        cursor.executemany(job_insert_q, job_data)
        conn.commit()
        print("Main jobs table populated successfully.")
        
        # 3. Retrieve jobs to match auto-increment IDs with their skills
        cursor.execute("SELECT id, skills_cleaned FROM jobs")
        jobs_db = cursor.fetchall()
        
        skill_data = []
        for job_id, skills_str in jobs_db:
            if not skills_str:
                continue
            skills = [s.strip() for s in skills_str.split(",") if s.strip() != ""]
            for skill in skills:
                skill_data.append((job_id, skill))
                
        # Bulk Insert skills
        skill_insert_q = "INSERT INTO job_skills (job_id, skill) VALUES (?, ?)"
        cursor.executemany(skill_insert_q, skill_data)
        conn.commit()
        conn.close()
        
        print(f"Normlised skills table populated with {len(skill_data):,} records. Data ingestion finalized!")
        
    def query(self, sql_query, params=None):
        """
        Executes a SQL query and returns results as a list of dictionaries (pure Python structure).
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row # returns dict-like Row objects
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(sql_query, params)
            else:
                cursor.execute(sql_query)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
            
    def get_summary_kpis(self):
        """
        Utility method to fetch main summary metrics.
        """
        q = """
        SELECT 
            COUNT(*) as total_jobs,
            COUNT(DISTINCT company) as total_companies,
            AVG(salary_avg) as avg_salary,
            AVG(experience_years) as avg_experience
        FROM jobs
        """
        results = self.query(q)
        if results:
            return results[0]
        return {"total_jobs": 0, "total_companies": 0, "avg_salary": 0, "avg_experience": 0}

if __name__ == "__main__":
    db = JobMarketDatabase()
    db.create_tables()
    db.ingest_data()
