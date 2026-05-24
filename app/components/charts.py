import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Sleek Theme Styling Variables
THEME_COLORS = {
    "primary": "#00f2fe",      # Cyan/Teal glow
    "secondary": "#4facfe",    # Slate blue
    "accent": "#f35588",       # Coral pink/rose
    "dark_bg": "#121824",      # Dark slate
    "grid_color": "#232e44",   # Border grid color
    "text_light": "#e2e8f0"    # Off-white
}

def plot_skill_demand(df_skills, title="Top In-Demand Skills"):
    """
    Creates an interactive Plotly horizontal bar chart displaying top skills.
    """
    if df_skills.empty:
        return go.Figure()
        
    df_skills = df_skills.sort_values(by="count", ascending=True)
    
    fig = px.bar(
        df_skills,
        x="count",
        y="skill",
        orientation="h",
        text="count",
        labels={"count": "Number of Job Listings", "skill": "Technology / Skill"},
        color="count",
        color_continuous_scale=["#4facfe", "#00f2fe"] # Blue to Cyan gradient
    )
    
    fig.update_layout(
        title={
            "text": title,
            "y": 0.95,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": {"size": 18, "color": THEME_COLORS["text_light"]}
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": THEME_COLORS["text_light"]},
        coloraxis_showscale=False,
        margin=dict(l=100, r=20, t=50, b=50),
        xaxis=dict(showgrid=True, gridcolor=THEME_COLORS["grid_color"]),
        yaxis=dict(showgrid=False)
    )
    
    fig.update_traces(
        textposition="inside",
        texttemplate="%{text:,}",
        hovertemplate="<b>%{y}</b><br>Listings: %{x:,}<extra></extra>"
    )
    
    return fig


def plot_salary_distribution(df, title="Market Salary Distribution (USD)"):
    """
    Plots an interactive histogram showing annual salary distribution.
    """
    fig = px.histogram(
        df,
        x="salary_avg",
        nbins=40,
        labels={"salary_avg": "Annual Salary (USD)", "count": "Job Postings"},
        color_discrete_sequence=[THEME_COLORS["primary"]],
        opacity=0.85
    )
    
    # Calculate key statistics
    avg_sal = df["salary_avg"].mean()
    med_sal = df["salary_avg"].median()
    
    fig.add_vline(x=avg_sal, line_dash="dash", line_color=THEME_COLORS["accent"], annotation_text=f"Mean: ${avg_sal:,.0f}")
    fig.add_vline(x=med_sal, line_dash="dot", line_color="#a78bfa", annotation_text=f"Median: ${med_sal:,.0f}")
    
    fig.update_layout(
        title={
            "text": title,
            "y": 0.95,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": {"size": 18, "color": THEME_COLORS["text_light"]}
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": THEME_COLORS["text_light"]},
        xaxis=dict(
            showgrid=True, 
            gridcolor=THEME_COLORS["grid_color"],
            tickformat="$,.0f"
        ),
        yaxis=dict(showgrid=True, gridcolor=THEME_COLORS["grid_color"]),
        bargap=0.08
    )
    
    fig.update_traces(
        hovertemplate="Salary Range: %{x}<br>Count: %{y}<extra></extra>"
    )
    
    return fig


def plot_experience_vs_salary(df, title="Experience vs Salary Correlation"):
    """
    Renders an interactive scatter plot showcasing the relationship 
    between experience years and average salary.
    """
    # Sample data points if too large to ensure fast rendering
    if len(df) > 2000:
        df_plot = df.sample(2000, random_state=42)
    else:
        df_plot = df
        
    fig = px.scatter(
        df_plot,
        x="experience_years",
        y="salary_avg",
        color="job_category",
        opacity=0.7,
        size_max=12,
        labels={
            "experience_years": "Years of Experience Required",
            "salary_avg": "Average Annual Salary (USD)",
            "job_category": "Category"
        },
        color_discrete_sequence=["#00f2fe", "#f35588", "#a78bfa", "#34d399", "#fbbf24"],
        hover_data=["job_title", "company", "location_city"]
    )
    
    fig.update_layout(
        title={
            "text": title,
            "y": 0.95,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": {"size": 18, "color": THEME_COLORS["text_light"]}
        },
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": THEME_COLORS["text_light"]},
        xaxis=dict(showgrid=True, gridcolor=THEME_COLORS["grid_color"]),
        yaxis=dict(showgrid=True, gridcolor=THEME_COLORS["grid_color"], tickformat="$,.0f")
    )
    
    fig.update_traces(marker=dict(size=6))
    
    return fig


def plot_job_setup_pie(df, title="Work Arrangement Distribution"):
    """
    Generates a donut chart representing Remote/Onsite/Hybrid breakdowns.
    """
    counts = df["job_type"].value_counts().reset_index()
    counts.columns = ["arrangement", "count"]
    
    fig = px.pie(
        counts,
        names="arrangement",
        values="count",
        hole=0.4,
        color_discrete_sequence=["#00f2fe", "#a78bfa", "#f35588"],
    )
    
    fig.update_layout(
        title={
            "text": title,
            "y": 0.95,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": {"size": 18, "color": THEME_COLORS["text_light"]}
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": THEME_COLORS["text_light"]},
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )
    
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Listings: %{value:,}<br>Percentage: %{percent}<extra></extra>"
    )
    
    return fig


def plot_hiring_trends(df, title="Hiring Velocity Trends Over Time"):
    """
    Generates a line plot showing job posting volume trends by month.
    """
    df_trends = df.copy()
    # Convert date to Year-Month for grouping
    df_trends["month"] = pd.to_datetime(df_trends["posting_date"]).dt.to_period("M").astype(str)
    
    trend_counts = df_trends.groupby(["month", "job_category"]).size().reset_index(name="listings")
    
    fig = px.line(
        trend_counts,
        x="month",
        y="listings",
        color="job_category",
        markers=True,
        labels={"month": "Month", "listings": "New Postings", "job_category": "Job Category"},
        color_discrete_sequence=["#00f2fe", "#f35588", "#a78bfa", "#34d399", "#fbbf24"],
    )
    
    fig.update_layout(
        title={
            "text": title,
            "y": 0.95,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": {"size": 18, "color": THEME_COLORS["text_light"]}
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": THEME_COLORS["text_light"]},
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=True, gridcolor=THEME_COLORS["grid_color"]),
        yaxis=dict(showgrid=True, gridcolor=THEME_COLORS["grid_color"])
    )
    
    fig.update_traces(line=dict(width=3))
    
    return fig


def plot_skills_cooccurrence(df, top_n_skills=15):
    """
    Generates a correlation/co-occurrence matrix heatmap for the top N skills.
    Returns a Seaborn/Matplotlib figure for embedded display.
    """
    # Parse list of skills
    all_skills_nested = df["skills_cleaned"].fillna("").apply(lambda x: [s.strip() for s in x.split(",") if s.strip() != ""])
    
    # Flatten list and find top skills
    flat_skills = [s for sublist in all_skills_nested for s in sublist]
    top_skills = list(pd.Series(flat_skills).value_counts().head(top_n_skills).index)
    
    # Create jobs x skills binary dataframe
    binary_df = pd.DataFrame(0, index=df.index, columns=top_skills)
    for idx, skills in enumerate(all_skills_nested):
        for s in skills:
            if s in top_skills:
                binary_df.loc[idx, s] = 1
                
    # Compute correlation matrix
    corr_matrix = binary_df.corr()
    
    # Plot using seaborn
    fig, ax = plt.subplots(figsize=(10, 8), facecolor=THEME_COLORS["dark_bg"])
    ax.set_facecolor(THEME_COLORS["dark_bg"])
    
    # Custom color palette for dark theme
    cmap = sns.diverging_palette(220, 20, as_cmap=True)
    
    sns.heatmap(
        corr_matrix, 
        annot=True, 
        fmt=".2f", 
        cmap=cmap, 
        center=0,
        square=True, 
        linewidths=.5, 
        cbar_kws={"shrink": .8},
        ax=ax,
        annot_kws={"size": 9}
    )
    
    # Style formatting
    ax.tick_params(colors=THEME_COLORS["text_light"], labelsize=10)
    plt.title(f"Technology Co-occurrence Matrix (Top {top_n_skills} Skills)", color=THEME_COLORS["text_light"], fontsize=14, pad=15)
    plt.tight_layout()
    
    # Set colorbar tick colors
    cbar = ax.collections[0].colorbar
    cbar.ax.yaxis.set_tick_params(color=THEME_COLORS["text_light"])
    plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color=THEME_COLORS["text_light"])
    
    return fig
