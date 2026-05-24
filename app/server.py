import os
import re
import csv
import json
import sqlite3
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

DB_PATH = "data/job_market.db"
ML_ASSETS_PATH = "models/pure_ml_assets.json"

class JobMarketAPIHandler(BaseHTTPRequestHandler):
    """
    Standard HTTP Request Handler representing the Web Server & Rest API Layer.
    Uses pure-Python built-ins, zero external dependencies.
    """
    def log_message(self, format, *args):
        # Override to suppress noisy server logging in the terminal
        return
        
    def _set_headers(self, content_type="application/json", status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        
    def do_OPTIONS(self):
        # Handle pre-flight CORS requests
        self._set_headers(status=204)
        
    def get_query_params(self):
        parsed_url = urllib.parse.urlparse(self.path)
        return urllib.parse.parse_qs(parsed_url.query)
        
    def serve_static(self, file_path):
        # Map file extensions to MIME types
        mime_types = {
            ".html": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".ico": "image/x-icon"
        }
        ext = os.path.splitext(file_path)[1]
        content_type = mime_types.get(ext, "text/plain")
        
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self._set_headers(content_type, status=200)
            self.wfile.write(content)
        except Exception:
            self.send_error(404, "File Not Found")

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        # 1. Serve Static Frontend Web Files
        if path == "/" or path == "/index.html":
            self.serve_static("app/static/index.html")
            return
        elif path == "/style.css":
            self.serve_static("app/static/style.css")
            return
        elif path == "/app.js":
            self.serve_static("app/static/app.js")
            return
            
        # 2. REST API Endpoints
        # Retrieve parsed filtering query parameters
        params = self.get_query_params()
        
        # Extract filters with default options
        categories = params.get("categories", [])
        cities = params.get("cities", [])
        types = params.get("types", [])
        
        # Create SQL filter condition string dynamically
        where_clauses = []
        sql_params = []
        
        if categories:
            # e.g. "job_category IN (?, ?, ?)"
            placeholders = ",".join(["?"] * len(categories))
            where_clauses.append(f"job_category IN ({placeholders})")
            sql_params.extend(categories)
            
        if cities:
            placeholders = ",".join(["?"] * len(cities))
            where_clauses.append(f"location_city IN ({placeholders})")
            sql_params.extend(cities)
            
        if types:
            placeholders = ",".join(["?"] * len(types))
            where_clauses.append(f"job_type IN ({placeholders})")
            sql_params.extend(types)
            
        filter_sql = ""
        if where_clauses:
            filter_sql = "WHERE " + " AND ".join(where_clauses)
            
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            # Endpoint: /api/kpis
            if path == "/api/kpis":
                q = f"""
                    SELECT 
                        COUNT(*) as total_jobs,
                        COUNT(DISTINCT company) as total_companies,
                        AVG(salary_avg) as avg_salary,
                        SUM(CASE WHEN job_type = 'Remote' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as remote_pct
                    FROM jobs
                    {filter_sql}
                """
                cursor.execute(q, sql_params)
                kpi_row = dict(cursor.fetchone())
                
                # Fetch distinct options for filters
                cursor.execute("SELECT DISTINCT job_category FROM jobs ORDER BY job_category")
                cats_opt = [r[0] for r in cursor.fetchall()]
                
                cursor.execute("SELECT DISTINCT location_city FROM jobs WHERE location_city != 'Remote' ORDER BY location_city")
                cities_opt = [r[0] for r in cursor.fetchall()]
                
                cursor.execute("SELECT DISTINCT job_type FROM jobs ORDER BY job_type")
                types_opt = [r[0] for r in cursor.fetchall()]
                
                response_data = {
                    "kpis": {
                        "total_jobs": kpi_row["total_jobs"] or 0,
                        "total_companies": kpi_row["total_companies"] or 0,
                        "avg_salary": round(kpi_row["avg_salary"] or 0.0, 2),
                        "remote_pct": round(kpi_row["remote_pct"] or 0.0, 2)
                    },
                    "options": {
                        "categories": cats_opt,
                        "cities": cities_opt,
                        "types": types_opt
                    }
                }
                self._set_headers()
                self.wfile.write(json.dumps(response_data).encode("utf-8"))
                
            # Endpoint: /api/charts
            elif path == "/api/charts":
                # A: Skills demand bar chart data (Top 12)
                # Filter is applied to jobs table
                skills_q = f"""
                    SELECT s.skill, COUNT(s.id) as count
                    FROM job_skills s
                    JOIN jobs j ON s.job_id = j.id
                    {filter_sql}
                    GROUP BY s.skill
                    ORDER BY count DESC
                    LIMIT 12
                """
                cursor.execute(skills_q, sql_params)
                skills_data = [{"skill": r[0], "count": r[1]} for r in cursor.fetchall()]
                
                # B: Work arrangement donut breakdown
                donut_q = f"""
                    SELECT job_type, COUNT(*) as count
                    FROM jobs
                    {filter_sql}
                    GROUP BY job_type
                """
                cursor.execute(donut_q, sql_params)
                donut_data = [{"job_type": r[0], "count": r[1]} for r in cursor.fetchall()]
                
                # C: Salary distribution histogram data (Standard bins of $15,000)
                # Min salary range to max range
                sal_q = f"""
                    SELECT CAST(salary_avg / 15000 AS INTEGER) * 15000 as bin_floor, COUNT(*) as count
                    FROM jobs
                    {filter_sql}
                    GROUP BY bin_floor
                    ORDER BY bin_floor
                """
                cursor.execute(sal_q, sql_params)
                sal_data = [{"bin": f"${r[0]:,} - ${r[0]+15000:,}", "count": r[1], "floor": r[0]} for r in cursor.fetchall()]
                
                # D: Monthly hiring velocity trends data
                trend_q = f"""
                    SELECT SUBSTR(posting_date, 1, 7) as month, job_category, COUNT(*) as count
                    FROM jobs
                    {filter_sql}
                    GROUP BY month, job_category
                    ORDER BY month
                """
                cursor.execute(trend_q, sql_params)
                trend_data = [{"month": r[0], "category": r[1], "count": r[2]} for r in cursor.fetchall()]
                
                # E: Experience vs Salary scatter correlation points (Sampled top 300 to prevent heavy JSON sizes)
                scatter_q = f"""
                    SELECT experience_years, salary_avg, job_category, job_title, company
                    FROM jobs
                    {filter_sql}
                    ORDER BY id
                    LIMIT 300
                """
                cursor.execute(scatter_q, sql_params)
                scatter_data = [{
                    "experience_years": r[0],
                    "salary_avg": r[1],
                    "job_category": r[2],
                    "job_title": r[3],
                    "company": r[4]
                } for r in cursor.fetchall()]
                
                # F: Technology co-occurrence heatmap (using Top 8 skills)
                # First fetch top 8 skills
                cursor.execute(f"SELECT s.skill, COUNT(s.id) as cnt FROM job_skills s JOIN jobs j ON s.job_id = j.id {filter_sql} GROUP BY s.skill ORDER BY cnt DESC LIMIT 8", sql_params)
                top_8_skills = [r[0] for r in cursor.fetchall()]
                
                # Calculate co-occurrences of these top 8 skills in the filtered jobs
                # job_id -> set of skills
                co_q = f"""
                    SELECT s.job_id, s.skill
                    FROM job_skills s
                    JOIN jobs j ON s.job_id = j.id
                    {filter_sql}
                """
                cursor.execute(co_q, sql_params)
                job_skills_map = {}
                for j_id, sk in cursor.fetchall():
                    if j_id not in job_skills_map:
                        job_skills_map[j_id] = set()
                    job_skills_map[j_id].add(sk)
                    
                # Build co-occurrence matrix
                matrix_data = []
                for s1 in top_8_skills:
                    row_cells = []
                    for s2 in top_8_skills:
                        if s1 == s2:
                            row_cells.append(100.0) # baseline self percentage
                        else:
                            # Count overlap percentage: intersection / union
                            intersection_cnt = sum(1 for j_id, sks in job_skills_map.items() if s1 in sks and s2 in sks)
                            union_cnt = sum(1 for j_id, sks in job_skills_map.items() if s1 in sks or s2 in sks)
                            overlap_pct = (intersection_cnt / union_cnt * 100) if union_cnt > 0 else 0
                            row_cells.append(round(overlap_pct, 1))
                    matrix_data.append({"skill": s1, "cooccurrences": row_cells})
                    
                response_data = {
                    "skills_bar": skills_data,
                    "donut": donut_data,
                    "salary_histogram": sal_data,
                    "trends_line": trend_data,
                    "scatter": scatter_data,
                    "heatmap": {
                        "skills": top_8_skills,
                        "matrix": matrix_data
                    }
                }
                
                self._set_headers()
                self.wfile.write(json.dumps(response_data).encode("utf-8"))
                
            # Endpoint: /api/insights
            elif path == "/api/insights":
                # Emerging skills (regressions)
                # Total postings month, id, and skills
                cursor.execute("SELECT s.skill, j.id, SUBSTR(j.posting_date, 1, 7) as posting_month FROM job_skills s JOIN jobs j ON s.job_id = j.id")
                rows_all = cursor.fetchall()
                
                emerging_list = []
                if rows_all:
                    jobs_per_month = {}
                    skill_monthly_counts = {}
                    skill_totals = {}
                    unique_jobs_by_month = {}
                    
                    for skill, job_id, month in rows_all:
                        if month not in unique_jobs_by_month:
                            unique_jobs_by_month[month] = set()
                        unique_jobs_by_month[month].add(job_id)
                        
                        if skill not in skill_monthly_counts:
                            skill_monthly_counts[skill] = {}
                        skill_monthly_counts[skill][month] = skill_monthly_counts[skill].get(month, 0) + 1
                        skill_totals[skill] = skill_totals.get(skill, 0) + 1
                        
                    for month, j_ids in unique_jobs_by_month.items():
                        jobs_per_month[month] = len(j_ids)
                        
                    all_months = sorted(list(jobs_per_month.keys()))
                    
                    if len(all_months) >= 3:
                        slopes = []
                        for skill, month_counts in skill_monthly_counts.items():
                            total_vol = skill_totals[skill]
                            if total_vol < 150: # volume threshold
                                continue
                            shares = []
                            for m in all_months:
                                m_tot = jobs_per_month.get(m, 0)
                                m_sk = month_counts.get(m, 0)
                                shares.append((m_sk / m_tot * 100) if m_tot > 0 else 0)
                                
                            x = list(range(len(all_months)))
                            mean_x = sum(x) / len(x)
                            mean_y = sum(shares) / len(shares)
                            num = sum((x[i] - mean_x) * (shares[i] - mean_y) for i in range(len(x)))
                            den = sum((x[i] - mean_x) ** 2 for i in range(len(x)))
                            slope = (num / den) if den > 0 else 0
                            
                            slopes.append({
                                "skill": skill,
                                "trend_slope": slope,
                                "total_listings": total_vol,
                                "recent_month_share": round(shares[-1], 2)
                            })
                            
                        # Sort by slope descending
                        emerging_list = sorted(slopes, key=lambda x: x["trend_slope"], reverse=True)[:5]
                        
                # Industry high paying averages
                cursor.execute("""
                    SELECT industry, COUNT(*), AVG(salary_avg), AVG(experience_years)
                    FROM jobs
                    GROUP BY industry
                    ORDER BY AVG(salary_avg) DESC
                """)
                industries_data = [{
                    "industry": r[0],
                    "job_count": r[1],
                    "average_salary": round(r[2], 2),
                    "average_experience": round(r[3], 2)
                } for r in cursor.fetchall()]
                
                # Fetch high salary premiums
                cursor.execute("""
                    SELECT s.skill, COUNT(s.id), AVG(j.salary_avg)
                    FROM job_skills s
                    JOIN jobs j ON s.job_id = j.id
                    GROUP BY s.skill
                    HAVING COUNT(s.id) >= 120
                    ORDER BY AVG(j.salary_avg) DESC
                    LIMIT 8
                """)
                premiums_data = [{
                    "skill": r[0],
                    "job_count": r[1],
                    "average_salary": round(r[2], 2)
                } for r in cursor.fetchall()]
                
                response_data = {
                    "emerging": emerging_list,
                    "industries": industries_data,
                    "premiums": premiums_data
                }
                
                self._set_headers()
                self.wfile.write(json.dumps(response_data).encode("utf-8"))
                
            # Endpoint: /api/download (CSV Export file download attachment)
            elif path == "/api/download":
                csv_q = f"""
                    SELECT job_title, company, location_raw, salary_raw, experience_raw,
                           skills_raw, job_type, industry, posting_date, job_category,
                           experience_years, salary_min, salary_max, salary_avg, location_city
                    FROM jobs
                    {filter_sql}
                """
                cursor.execute(csv_q, sql_params)
                export_rows = cursor.fetchall()
                
                # Build raw CSV content
                csv_headers = [
                    "job_title", "company", "location_raw", "salary_raw", "experience_raw",
                    "skills_raw", "job_type", "industry", "posting_date", "job_category",
                    "experience_years", "salary_min", "salary_max", "salary_avg", "location_city"
                ]
                
                self.send_response(200)
                self.send_header("Content-Type", "text/csv")
                self.send_header("Content-Disposition", "attachment; filename=filtered_market_postings.csv")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                
                # Write CSV header row
                self.wfile.write((",".join(csv_headers) + "\n").encode("utf-8"))
                for row in export_rows:
                    csv_cells = []
                    for val in row:
                        cell_str = str(val or "").replace('"', '""')
                        csv_cells.append(f'"{cell_str}"')
                    self.wfile.write((",".join(csv_cells) + "\n").encode("utf-8"))
                    
            else:
                self.send_error(404, "Endpoint Not Found")
                
        except Exception as e:
            self.send_error(500, f"Database query failed: {e}")
        finally:
            conn.close()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        # Read payload size
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)
        
        try:
            payload = json.loads(post_data.decode("utf-8"))
        except Exception:
            self.send_error(400, "Invalid JSON payload")
            return
            
        # Endpoint: /api/predict
        if path == "/api/predict":
            category = payload.get("category", "Software Engineering")
            jtype = payload.get("job_type", "Remote")
            city = payload.get("city", "San Francisco")
            experience = float(payload.get("experience", 3.0))
            skills = payload.get("skills", [])
            
            # Load ML parameters
            try:
                with open(ML_ASSETS_PATH, "r", encoding="utf-8") as f:
                    ml_assets = json.load(f)
                salary_predictor = ml_assets["salary_predictor"]
                
                # Inference calculation offset
                predicted_avg = salary_predictor["global_average"]
                predicted_avg += salary_predictor["category_offsets"].get(category, 0)
                predicted_avg += salary_predictor["city_offsets"].get(city, 0)
                predicted_avg += salary_predictor["type_offsets"].get(jtype, 0)
                predicted_avg += experience * salary_predictor["experience_slope"]
                
                for sk in skills:
                    predicted_avg += salary_predictor["skill_offsets"].get(sk, 0)
                    
                response_data = {
                    "predicted_avg": round(predicted_avg, 2),
                    "predicted_min": round(predicted_avg * 0.90, 2),
                    "predicted_max": round(predicted_avg * 1.10, 2)
                }
                self._set_headers()
                self.wfile.write(json.dumps(response_data).encode("utf-8"))
            except Exception as e:
                self.send_error(500, f"Model inference failed: {e}")
                
        # Endpoint: /api/recommend
        elif path == "/api/recommend":
            cand_skills = payload.get("skills", [])
            
            try:
                with open(ML_ASSETS_PATH, "r", encoding="utf-8") as f:
                    ml_assets = json.load(f)
                recommender = ml_assets["recommender"]
                
                # Fetch matches
                recs = set()
                for skill in cand_skills:
                    for r_skill in recommender["cooccurrences"].get(skill, []):
                        if r_skill not in cand_skills:
                            recs.add(r_skill)
                            
                # Get the Jaccard-similar or highly demanded recommendations
                response_data = {
                    "recommended_skills": list(recs)[:6],
                    "all_skills_list": recommender["all_skills_list"]
                }
                self._set_headers()
                self.wfile.write(json.dumps(response_data).encode("utf-8"))
            except Exception as e:
                self.send_error(500, f"Skill recommender failed: {e}")
                
        # Endpoint: /api/recommend_advisor
        elif path == "/api/recommend_advisor":
            cand_cat = payload.get("current_category")
            target_cat = payload.get("target_category")
            cand_skills = payload.get("skills", [])
            
            # Use SQLite to match premiums dynamically
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            try:
                # Fetch target category top skills
                cursor.execute("""
                    SELECT s.skill, COUNT(s.id), AVG(j.salary_avg)
                    FROM job_skills s
                    JOIN jobs j ON s.job_id = j.id
                    WHERE j.job_category = ?
                    GROUP BY s.skill
                    ORDER BY COUNT(s.id) DESC
                    LIMIT 25
                """, (target_cat,))
                
                rows = cursor.fetchall()
                missing_skills = []
                cand_skills_lower = [s.strip().lower() for s in cand_skills]
                
                for sk_name, sk_count, sk_avg_sal in rows:
                    if sk_name.lower() not in cand_skills_lower:
                        missing_skills.append({
                            "skill": sk_name,
                            "market_demand": sk_count,
                            "skill_avg_salary": round(sk_avg_sal, 2)
                        })
                        
                missing_skills = sorted(missing_skills, key=lambda x: x["market_demand"], reverse=True)
                
                # Calculate benchmarks
                cursor.execute("""
                    SELECT AVG(salary_avg), MAX(salary_max)
                    FROM jobs
                    WHERE job_category = ?
                """, (target_cat,))
                r = cursor.fetchone()
                baseline = r[0] if r and r[0] else 110000.0
                ceiling = r[1] if r and r[1] else 200000.0
                
                top_missing = [m["skill"] for m in missing_skills[:4]]
                recommendation_text = f"As a practitioner in **{cand_cat}** seeking to excel or pivot towards **{target_cat}**, "
                if len(top_missing) > 0:
                    recommendation_text += f"your highest leverage career move is to acquire: **{', '.join(top_missing)}**. "
                else:
                    recommendation_text += "you possess an outstanding, highly competitive skillset for this market! "
                    
                recommendation_text += f"The current average market salary for **{target_cat}** is **${baseline:,.2f} USD**, with top percentiles commanding up to **${ceiling:,.2f} USD**."
                
                response_data = {
                    "recommendation_text": recommendation_text,
                    "missing_skills": missing_skills[:6]
                }
                
                self._set_headers()
                self.wfile.write(json.dumps(response_data).encode("utf-8"))
            finally:
                conn.close()
                
        else:
            self.send_error(404, "Endpoint Not Found")

def start_server(port=8501):
    print(f"========================================================")
    print(f"[START] JOB MARKET ANALYTICS SERVER RUNNING")
    print(f"Local Server Address: http://localhost:{port}")
    print(f"Access raw REST APIs and interactive premium visual Web App!")
    print(f"========================================================")
    
    server_address = ("", port)
    httpd = HTTPServer(server_address, JobMarketAPIHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping analytics server...")
        httpd.server_close()

if __name__ == "__main__":
    start_server()
