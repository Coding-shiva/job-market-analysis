import os
import sqlite3

class AIInsightsEngine:
    """
    Automated Analytical Insights Engine that extracts market trends, emerging technology slopes, 
    salary benchmarks, and personalized career pathways from SQLite in pure Python.
    """
    def __init__(self, db_path="data/job_market.db"):
        self.db_path = db_path
        
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
        
    def get_most_valuable_skills(self, limit=15, min_occurrences=100):
        """
        Identifies high-paying skills based on the average salary of jobs requiring them.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        query = f"""
            SELECT 
                s.skill,
                COUNT(s.id) as job_count,
                AVG(j.salary_avg) as average_salary,
                AVG(j.experience_years) as average_experience
            FROM job_skills s
            JOIN jobs j ON s.job_id = j.id
            GROUP BY s.skill
            HAVING job_count >= ?
            ORDER BY average_salary DESC
            LIMIT ?
        """
        try:
            cursor.execute(query, (min_occurrences, limit))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                results.append({
                    "skill": r[0],
                    "job_count": r[1],
                    "average_salary": round(r[2], 2),
                    "average_experience": round(r[3], 2)
                })
            return results
        finally:
            conn.close()
            
    def get_emerging_technologies(self, limit=8, min_total_jobs=300):
        """
        Determines emerging skills by calculating the monthly job percentage trend slope in pure Python.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 1. Fetch postings month, id, and skills
        query = """
            SELECT s.skill, j.id, SUBSTR(j.posting_date, 1, 7) as posting_month
            FROM job_skills s
            JOIN jobs j ON s.job_id = j.id
        """
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            if not rows:
                return []
                
            # Organize counts in pure Python
            # jobs_per_month: month -> total unique job count
            # skill_monthly_counts: skill -> month -> count
            jobs_per_month = {}
            skill_monthly_counts = {}
            skill_totals = {}
            
            unique_jobs_by_month = {} # month -> set of job_ids
            
            for skill, job_id, month in rows:
                if month not in unique_jobs_by_month:
                    unique_jobs_by_month[month] = set()
                unique_jobs_by_month[month].add(job_id)
                
                if skill not in skill_monthly_counts:
                    skill_monthly_counts[skill] = {}
                skill_monthly_counts[skill][month] = skill_monthly_counts[skill].get(month, 0) + 1
                skill_totals[skill] = skill_totals.get(skill, 0) + 1
                
            for month, job_ids in unique_jobs_by_month.items():
                jobs_per_month[month] = len(job_ids)
                
            # List of sorted months
            all_months = sorted(list(jobs_per_month.keys()))
            if len(all_months) < 3:
                return [] # Not enough timeline details
                
            slopes = []
            for skill, month_counts in skill_monthly_counts.items():
                total_volume = skill_totals[skill]
                if total_volume < min_total_jobs:
                    continue
                    
                # Compile share percentages for consecutive months
                shares = []
                for m in all_months:
                    m_total_jobs = jobs_per_month.get(m, 0)
                    m_skill_jobs = month_counts.get(m, 0)
                    share_pct = (m_skill_jobs / m_total_jobs * 100) if m_total_jobs > 0 else 0
                    shares.append(share_pct)
                    
                # Fit simple linear slope: cov(x,y) / var(x) in pure Python
                x = list(range(len(all_months)))
                mean_x = sum(x) / len(x)
                mean_y = sum(shares) / len(shares)
                
                numerator = sum((x[i] - mean_x) * (shares[i] - mean_y) for i in range(len(x)))
                denominator = sum((x[i] - mean_x) ** 2 for i in range(len(x)))
                
                slope = (numerator / denominator) if denominator > 0 else 0
                
                slopes.append({
                    "skill": skill,
                    "trend_slope": slope,
                    "total_listings": total_volume,
                    "recent_month_share": round(shares[-1], 2),
                    "starting_month_share": round(shares[0], 2)
                })
                
            # Sort by slope descending
            sorted_slopes = sorted(slopes, key=lambda x: x["trend_slope"], reverse=True)[:limit]
            return sorted_slopes
        finally:
            conn.close()
            
    def get_high_paying_domains(self):
        """
        Compares salaries and volumes across industries.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        query = """
            SELECT 
                industry,
                COUNT(*) as job_count,
                AVG(salary_avg) as average_salary,
                AVG(experience_years) as average_experience
            FROM jobs
            GROUP BY industry
            ORDER BY average_salary DESC
        """
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            results = []
            for r in rows:
                results.append({
                    "industry": r[0],
                    "job_count": r[1],
                    "average_salary": round(r[2], 2),
                    "average_experience": round(r[3], 2)
                })
            return results
        finally:
            conn.close()
            
    def get_career_recommendation(self, current_category, current_skills, target_category=None):
        """
        Provides custom, actionable career advisor recommendations and missing skills in pure Python.
        """
        if not target_category:
            target_category = current_category
            
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # 1. Fetch top skills for the target category
            query = """
                SELECT s.skill, COUNT(s.id) as count, AVG(j.salary_avg) as skill_avg_salary
                FROM job_skills s
                JOIN jobs j ON s.job_id = j.id
                WHERE j.job_category = ?
                GROUP BY s.skill
                ORDER BY count DESC
                LIMIT 25
            """
            cursor.execute(query, (target_category,))
            rows = cursor.fetchall()
            
            target_skills_dict = {}
            for r in rows:
                target_skills_dict[r[0]] = {
                    "count": r[1],
                    "skill_avg_salary": r[2]
                }
                
            # Identify missing skills
            candidate_skills = [s.strip().lower() for s in current_skills]
            missing_skills = []
            
            for skill_name, info in target_skills_dict.items():
                if skill_name.lower() not in candidate_skills:
                    missing_skills.append({
                        "skill": skill_name,
                        "market_demand": info["count"],
                        "skill_avg_salary": info["skill_avg_salary"]
                    })
                    
            # Sort missing skills by market demand
            missing_skills = sorted(missing_skills, key=lambda x: x["market_demand"], reverse=True)
            
            # Calculate salary benchmarks
            bench_query = """
                SELECT 
                    AVG(salary_avg) as baseline_salary,
                    MAX(salary_max) as ceiling_salary
                FROM jobs 
                WHERE job_category = ?
            """
            cursor.execute(bench_query, (target_category,))
            r = cursor.fetchone()
            baseline = r[0] if r and r[0] else 100000.0
            ceiling = r[1] if r and r[1] else 200000.0
            
            # Generate recommendation summary text
            top_missing = [m["skill"] for m in missing_skills[:4]]
            
            recommendation_text = f"As a practitioner in **{current_category}** seeking to excel or pivot towards **{target_category}**, "
            if len(top_missing) > 0:
                recommendation_text += f"your highest leverage career move is to acquire: **{', '.join(top_missing)}**. "
            else:
                recommendation_text += "you possess an outstanding, highly competitive skillset for this market! "
                
            recommendation_text += f"The current average market salary for **{target_category}** is **${baseline:,.2f} USD**, with top percentiles commanding up to **${ceiling:,.2f} USD**."
            
            return {
                "recommendation_text": recommendation_text,
                "missing_skills": missing_skills[:10],
                "market_average_salary": baseline,
                "market_ceiling_salary": ceiling
            }
        finally:
            conn.close()

if __name__ == "__main__":
    engine = AIInsightsEngine()
    print("Pure-Python AI Insights Engine initialized.")
    val_skills = engine.get_most_valuable_skills(limit=5)
    print("Sample Valuable Skills:")
    print(val_skills)
