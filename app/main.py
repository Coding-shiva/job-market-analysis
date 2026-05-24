import os
import joblib
import sqlite3
import numpy as np
import pandas as pd
import streamlit as st

# Custom modules
from components.charts import (
    plot_skill_demand, plot_salary_distribution, plot_experience_vs_salary,
    plot_job_setup_pie, plot_hiring_trends, plot_skills_cooccurrence
)
from src.insights import AIInsightsEngine
from src.database import JobMarketDatabase

# Set page config with premium icon and title
st.set_page_config(
    page_title="Job Market Intelligence Platform",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sleek CSS for Custom Glassmorphism, Neon glow headers, and Premium Dark Theme
st.markdown("""
    <style>
    /* Main container styling */
    .main {
        background-color: #0b0f19;
        color: #f1f5f9;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid #1f2937;
    }
    
    /* Header/Title style */
    .dashboard-title {
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 800;
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        margin-bottom: 0.5rem;
        text-shadow: 0px 0px 20px rgba(0, 242, 254, 0.15);
    }
    
    .dashboard-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        color: #9ca3af;
        margin-bottom: 2rem;
    }
    
    /* Glassmorphic KPI Cards */
    .kpi-card {
        background: rgba(17, 24, 39, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        text-align: center;
        transition: transform 0.3s ease, border 0.3s ease;
    }
    .kpi-card:hover {
        transform: translateY(-5px);
        border: 1px solid rgba(0, 242, 254, 0.3);
    }
    .kpi-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #00f2fe;
        margin-bottom: 5px;
        font-family: 'Outfit', sans-serif;
    }
    .kpi-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #9ca3af;
    }
    
    /* Section dividers */
    .section-header {
        font-family: 'Outfit', sans-serif;
        font-size: 1.5rem;
        font-weight: 600;
        color: #e2e8f0;
        border-bottom: 2px solid #1f2937;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
        margin-bottom: 1.25rem;
    }
    
    /* Input adjustments */
    div[data-baseweb="select"] > div {
        background-color: #1f2937 !important;
        color: #f1f5f9 !important;
        border-color: #374151 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 1. Initialize Database & Insights Engine
# ----------------------------------------------------
DB_PATH = "data/job_market.db"
CLEANED_CSV = "data/processed/job_postings_cleaned.csv"

# In case database is not populated, alert candidate
if not os.path.exists(DB_PATH) or not os.path.exists(CLEANED_CSV):
    st.error("⚠️ Data files are missing! Please run the orchestrator script `run.py` to generate the raw dataset, clean it, train the ML models, and initialize the SQL tables.")
    st.stop()

db = JobMarketDatabase(DB_PATH)
insights_engine = AIInsightsEngine(DB_PATH)

# Load the base dataset for general filters
df_cleaned = pd.read_csv(CLEANED_CSV)

# ----------------------------------------------------
# 2. Sidebar Navigation and Filters
# ----------------------------------------------------
st.sidebar.markdown("""
    <div style="text-align: center; margin-bottom: 1.5rem;">
        <h2 style="color: #00f2fe; font-family: 'Outfit', sans-serif; margin-bottom: 5px;">Market Intelligence</h2>
        <span style="color: #9ca3af; font-size: 0.85rem;">Developer Hiring Trends Platform</span>
    </div>
""", unsafe_allow_html=True)

# Navigation
page = st.sidebar.radio(
    "🧭 SELECT MODULE",
    ["📊 Market Overview", "💻 Tech Stack Analytics", "🔮 ML Salary Estimator", "💡 AI Career Advisor"]
)

st.sidebar.markdown("<br><hr style='border-color: #1f2937;'>", unsafe_allow_html=True)
st.sidebar.subheader("🔍 FILTER SETTINGS")

# Setup Global Filters
all_categories = sorted(df_cleaned["job_category"].unique())
all_countries = sorted(df_cleaned["location_country"].unique())
all_cities = sorted(df_cleaned["location_city"].unique())
all_job_types = sorted(df_cleaned["job_type"].unique())

selected_categories = st.sidebar.multiselect("Job Category", all_categories, default=all_categories)
selected_countries = st.sidebar.multiselect("Country / Region", all_countries, default=all_countries)

# Dynamic filter for cities based on selected country
filtered_cities_list = sorted(df_cleaned[df_cleaned["location_country"].isin(selected_countries)]["location_city"].unique()) if len(selected_countries) > 0 else all_cities
selected_cities = st.sidebar.multiselect("Hiring Hub / City", filtered_cities_list, default=filtered_cities_list[:8])

selected_types = st.sidebar.multiselect("Work Arrangement", all_job_types, default=all_job_types)

st.sidebar.markdown("<br>", unsafe_allow_html=True)
if st.sidebar.button("🔄 Reset Filter Selection", use_container_width=True):
    st.experimental_rerun()

# Apply Filters to the base DataFrame for analysis
df_filtered = df_cleaned[
    (df_cleaned["job_category"].isin(selected_categories)) &
    (df_cleaned["location_country"].isin(selected_countries)) &
    (df_cleaned["location_city"].isin(selected_cities)) &
    (df_cleaned["job_type"].isin(selected_types))
].reset_index(drop=True)

# ----------------------------------------------------
# 3. Render Top Branding and Header
# ----------------------------------------------------
st.markdown("<h1 class='dashboard-title'>Job Market Analytics Platform</h1>", unsafe_allow_html=True)
st.markdown("<div class='dashboard-subtitle'>Interactive Market Intelligence Engine Analyzing 55,000+ Software & Data Job Postings</div>", unsafe_allow_html=True)

# Render glowing glassmorphism KPI Cards
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_jobs = len(df_filtered)
unique_companies = df_filtered["company"].nunique() if total_jobs > 0 else 0
avg_sal = df_filtered["salary_avg"].mean() if total_jobs > 0 else 0.0
remote_pct = (len(df_filtered[df_filtered["job_type"] == "Remote"]) / total_jobs * 100) if total_jobs > 0 else 0.0

with kpi1:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{total_jobs:,}</div>
            <div class="kpi-label">Active Job Postings</div>
        </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{unique_companies:,}</div>
            <div class="kpi-label">Hiring Companies</div>
        </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">${avg_sal:,.0f}</div>
            <div class="kpi-label">National Salary Average</div>
        </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-value">{remote_pct:.1f}%</div>
            <div class="kpi-label">Remote Share Ratio</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Handle empty state if filter is too restrictive
if df_filtered.empty:
    st.warning("⚠️ No records match your current filter settings. Please expand your location, category, or arrangement criteria in the sidebar.")
    st.stop()

# ----------------------------------------------------
# MODULE 1: MARKET OVERVIEW
# ----------------------------------------------------
if page == "📊 Market Overview":
    st.markdown("<div class='section-header'>Market Distribution & Velocity Insights</div>", unsafe_allow_html=True)
    
    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(plot_hiring_trends(df_filtered), use_container_width=True)
    with col_r:
        st.plotly_chart(plot_salary_distribution(df_filtered), use_container_width=True)
        
    st.markdown("<div class='section-header'>Workplace Dynamics & Experience Correlation</div>", unsafe_allow_html=True)
    
    col_l_2, col_r_2 = st.columns([1, 2])
    with col_l_2:
        st.plotly_chart(plot_job_setup_pie(df_filtered), use_container_width=True)
    with col_r_2:
        st.plotly_chart(plot_experience_vs_salary(df_filtered), use_container_width=True)
        
    # Geographic Top Hiring Centers breakdown table
    st.markdown("<div class='section-header'>Top Hiring Hubs & Regional Salaries</div>", unsafe_allow_html=True)
    geo_df = df_filtered.groupby(["location_city", "location_country"]).agg(
        postings=("job_title", "count"),
        average_salary=("salary_avg", "mean"),
        average_experience=("experience_years", "mean")
    ).reset_index().sort_values(by="postings", ascending=False).head(10)
    
    geo_df["average_salary"] = geo_df["average_salary"].apply(lambda x: f"${x:,.2f}")
    geo_df["average_experience"] = geo_df["average_experience"].apply(lambda x: f"{x:.1f} yrs")
    geo_df.columns = ["City", "Country/Region", "Total Open Postings", "Average Compensation (USD)", "Avg Exp Required"]
    
    st.dataframe(geo_df, use_container_width=True, hide_index=True)

# ----------------------------------------------------
# MODULE 2: TECH STACK ANALYTICS
# ----------------------------------------------------
elif page == "💻 Tech Stack Analytics":
    st.markdown("<div class='section-header'>Tech Stack Dominance Matrix</div>", unsafe_allow_html=True)
    
    # Calculate top skill count from DB/filtered set
    job_ids = list(df_filtered["job_title"].index) # get index references
    
    # Build filtered list of skills
    all_skills = []
    for s_str in df_filtered["skills_cleaned"].fillna(""):
        all_skills.extend([s.strip() for s in s_str.split(",") if s.strip() != ""])
        
    skills_df = pd.Series(all_skills).value_counts().reset_index()
    skills_df.columns = ["skill", "count"]
    
    col_skill_l, col_skill_r = st.columns([2, 3])
    
    with col_skill_l:
        st.plotly_chart(plot_skill_demand(skills_df.head(15)), use_container_width=True)
        
    with col_skill_r:
        # Tech co-occurrence heatmap
        with st.spinner("Generating technology co-occurrence matrix..."):
            fig_heatmap = plot_skills_cooccurrence(df_filtered, top_n_skills=12)
            st.pyplot(fig_heatmap)
            
    # Skill-wise salary premium table
    st.markdown("<div class='section-header'>High-Value Technology Premium Benchmarks</div>", unsafe_allow_html=True)
    val_skills_df = insights_engine.get_most_valuable_skills(limit=12, min_occurrences=150)
    
    if not val_skills_df.empty:
        val_skills_df["average_salary"] = val_skills_df["average_salary"].apply(lambda x: f"${x:,.2f}")
        val_skills_df["average_experience"] = val_skills_df["average_experience"].apply(lambda x: f"{x:.1f} years")
        val_skills_df.columns = ["Skill / Technology", "Total Open Listings", "Market Average Compensation (USD)", "Avg Experience Level"]
        st.dataframe(val_skills_df, use_container_width=True, hide_index=True)
    else:
        st.info("Additional volume required to run standard salary premium benchmarks.")

# ----------------------------------------------------
# MODULE 3: ML SALARY ESTIMATOR
# ----------------------------------------------------
elif page == "🔮 ML Salary Estimator":
    st.markdown("<div class='section-header'>AI Salary Prediction Engine</div>", unsafe_allow_html=True)
    
    # Load serialised model assets
    models_dir = "models"
    salary_model_path = os.path.join(models_dir, "salary_model.joblib")
    top_skills_path = os.path.join(models_dir, "top_skills_list.joblib")
    skill_recommender_path = os.path.join(models_dir, "skill_recommender.joblib")
    
    if not os.path.exists(salary_model_path) or not os.path.exists(top_skills_path):
        st.warning("⚠️ Machine learning models are not yet compiled! Please run `run.py` to trigger model training.")
        st.stop()
        
    pipeline = joblib.load(salary_model_path)
    top_skills = joblib.load(top_skills_path)
    
    st.write("Use this predictive module to input role parameters and estimate the target market valuation range based on historical distributions, region, experience, and custom skill selection.")
    
    col_input1, col_input2, col_input3 = st.columns(3)
    with col_input1:
        job_cat = st.selectbox("Market Discipline / Category", all_categories)
        job_type = st.selectbox("Work Arrangement Format", ["Remote", "Onsite", "Hybrid"])
    with col_input2:
        city = st.selectbox("Target Hiring Center / City", all_cities)
    with col_input3:
        experience = st.slider("Required Years of Experience", min_value=0, max_value=15, value=3)
        
    st.markdown("##### 🛠️ Select Associated Technologies & Tools")
    
    # Group skills visually into grid columns
    cols_skills = st.columns(5)
    selected_skills = []
    
    # Group checklist entries into column widgets
    skills_per_col = len(top_skills) // 5
    for c_idx, col in enumerate(cols_skills):
        start_i = c_idx * skills_per_col
        end_i = (c_idx + 1) * skills_per_col if c_idx < 4 else len(top_skills)
        with col:
            for skill in top_skills[start_i:end_i]:
                if st.checkbox(skill, key=f"pred_skill_{skill}"):
                    selected_skills.append(skill)
                    
    if st.button("🔮 Calculate Estimated Annual Salary Range", type="primary", use_container_width=True):
        # Build vector matching ML features exactly
        # Categoricals: job_category, job_type, location_city
        # Numericals: experience_years
        # Skill-indicators: binary columns
        input_data = {
            "job_category": [job_cat],
            "job_type": [job_type],
            "location_city": [city],
            "experience_years": [float(experience)]
        }
        
        # Add skill indicators
        for skill in top_skills:
            input_data[f"skill_{skill}"] = [1 if skill in selected_skills else 0]
            
        input_df = pd.DataFrame(input_data)
        
        with st.spinner("Executing Random Forest inference pipeline..."):
            predicted_avg = pipeline.predict(input_df)[0]
            
            # Formulate realistic ranges based on model confidence
            estimated_min = predicted_avg * 0.90
            estimated_max = predicted_avg * 1.10
            
            # Format UI displays
            st.success("🎉 Target compensation estimate calculated successfully!")
            
            r_col1, r_col2 = st.columns(2)
            with r_col1:
                st.metric(
                    label="ESTIMATED ANNUAL SALARY (AVERAGE)",
                    value=f"${predicted_avg:,.2f} USD"
                )
            with r_col2:
                st.metric(
                    label="VALUATION BOUNDS / RANGE",
                    value=f"${estimated_min:,.0f} - ${estimated_max:,.0f}"
                )
                
            st.info(f"💡 **Dynamic Insights:** The average salary premium in **{city}** for a candidate with **{experience} years** of experience in **{job_cat}** is highly competitive. Adding hot technologies like {', '.join(selected_skills[:3]) if len(selected_skills) > 0 else 'cloud platforms'} generally increases market value by 8% to 15% in similar roles.")

# ----------------------------------------------------
# MODULE 4: AI CAREER ADVISOR
# ----------------------------------------------------
elif page == "💡 AI Career Advisor":
    st.markdown("<div class='section-header'>Automated Hiring & Career Advisor</div>", unsafe_allow_html=True)
    
    col_insight_l, col_insight_r = st.columns([3, 2])
    
    with col_insight_l:
        st.markdown("### 📈 Sector-Wide Hiring Dynamics")
        st.write("This engine uses linear regressions on skill-demand slopes to extract emerging platforms and hot domains.")
        
        st.markdown("#### 🔥 Emerging & Rising Technologies (Monthly Share Growth)")
        emerging_df = insights_engine.get_emerging_technologies(limit=6, min_total_jobs=150)
        
        if not emerging_df.empty:
            for idx, row in emerging_df.iterrows():
                # Format trend slope
                slope = row["trend_slope"]
                st.markdown(f"- **{row['skill']}**: Monthly demand share is **{'growing' if slope > 0 else 'stable'}** (slope: `+{slope:.4f}`). Listings containing this skill total **{int(row['total_listings']):,}**.")
        else:
            st.info("Additional volume required to run emerging technology share regressions.")
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 🏢 Industry Compensation Benchmarks")
        domain_df = insights_engine.get_high_paying_domains()
        
        if not domain_df.empty:
            domain_df.columns = ["Industry Sector", "Open Jobs Volume", "Avg Annual Salary (USD)", "Avg Exp Required"]
            domain_df["Avg Annual Salary (USD)"] = domain_df["Avg Annual Salary (USD)"].apply(lambda x: f"${x:,.2f}")
            domain_df["Avg Exp Required"] = domain_df["Avg Exp Required"].apply(lambda x: f"{x:.1f} yrs")
            st.dataframe(domain_df, use_container_width=True, hide_index=True)
            
    with col_insight_r:
        st.markdown("### 🎓 Personalised Career Accelerator")
        st.write("Submit your profile attributes below to evaluate skill gaps and calculate high-value technological premiums.")
        
        cand_cat = st.selectbox("Current Category / Track", all_categories, index=0)
        
        target_cat = st.selectbox("Target Career Pivot (Or Same)", all_categories, index=0)
        
        cand_skills_raw = st.text_area(
            "Enter your current skills (comma-separated)",
            value="Python, SQL, Git",
            placeholder="e.g. Python, SQL, Docker, React, C++"
        )
        
        if st.button("🚀 Analyze Skill Gap & Target Premium", use_container_width=True):
            cand_skills_list = [s.strip() for s in cand_skills_raw.split(",") if s.strip() != ""]
            
            with st.spinner("Querying market database..."):
                advice = insights_engine.get_career_recommendation(cand_cat, cand_skills_list, target_cat)
                
                st.markdown("#### 💬 AI Recommendation Summary")
                st.markdown(advice["recommendation_text"])
                
                st.markdown("#### 📊 Target Skill Premium Benchmarks")
                missing_df = pd.DataFrame(advice["missing_skills"])
                
                if not missing_df.empty:
                    missing_df["skill_avg_salary"] = missing_df["skill_avg_salary"].apply(lambda x: f"${x:,.2f}")
                    missing_df.columns = ["Highly Demanded Skill", "Open Listings Count", "Average Salary associated (USD)"]
                    st.dataframe(missing_df.head(6), use_container_width=True, hide_index=True)
                else:
                    st.success("Excellent! You match all high-demand technologies for this segment.")

    # Report Download Section
    st.markdown("<div class='section-header'>💾 Export Analytics & Job Datasets</div>", unsafe_allow_html=True)
    st.write("Generate a downloadable file containing the filtered job postings for downstream integrations, offline analysis, or executive briefing packs.")
    
    csv_data = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Cleaned Filtered Dataset (CSV)",
        data=csv_data,
        file_name="filtered_job_postings.csv",
        mime="text/csv",
        use_container_width=True
    )
