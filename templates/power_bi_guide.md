# Power BI Executive Dashboard Integration Guide

This guide details instructions and design patterns for loading the **SQLite Database (`data/job_market.db`)** into **Microsoft Power BI** to create a stunning, executive-ready Business Intelligence dashboard.

---

## 1. Connecting Power BI to the SQLite Database

To connect Power BI Desktop to our SQLite database:

### Option A: Using ODBC Driver (Recommended for native SQLite)
1. Download and install the **SQLite ODBC Driver** (e.g., from [Christian Werner's ODBC Page](http://www.chwerner.de/sqliteodbc/) or standard sources).
2. Open the **ODBC Data Source Administrator** on Windows (64-bit).
3. Under the **User DSN** tab, click **Add...** and select **SQLite3 ODBC Driver**.
4. Configure the DSN:
   - **Data Source Name (DSN)**: `JobMarketDSN`
   - **Database Name**: Click *Browse* and select the path to your SQLite database file: `C:\Users\<Your_User>\Desktop\data-analytics\data\job_market.db`.
5. Open Power BI Desktop, click **Get Data** -> **ODBC**.
6. Select `JobMarketDSN` from the DSN dropdown, click **Connect**.
7. In the Navigator window, select the **`jobs`** and **`job_skills`** tables, and click **Load** or **Transform Data**.

### Option B: Python Script Loader (Quick & Portable)
1. Open Power BI Desktop.
2. Click **Get Data** -> **Python script**.
3. Paste the following script:
   ```python
   import sqlite3
   import pandas as pd

   db_path = r"C:\Users\shivanand sharma\Desktop\data-analytics\data\job_market.db"
   conn = sqlite3.connect(db_path)
   
   jobs = pd.read_sql("SELECT * FROM jobs", conn)
   job_skills = pd.read_sql("SELECT * FROM job_skills", conn)
   
   conn.close()
   ```
4. Click **OK**, then select `jobs` and `job_skills` in the Navigator and click **Load**.

---

## 2. Relational Schema / Data Model

Ensure Power BI creates the following relation in the **Model View**:
* **Table**: `jobs` (Primary Table)
* **Table**: `job_skills` (Normalized Skill Table)
* **Relation**: **One-to-Many (`1:*`)** from `jobs(id)` to `job_skills(job_id)`.
* **Cross filter direction**: **Both** (This allows filtering the `jobs` metrics, like average salary, when selecting a skill in the `job_skills` table).

---

## 3. Key Measures (DAX Formulae)

Create a dedicated table or add these measures to your model to compute executive KPIs:

### Total Active Postings
```dax
Total Postings = COUNT(jobs[id])
```

### Market Average Annual Salary (USD)
```dax
Average Salary = AVERAGE(jobs[salary_avg])
```

### Remote Share Ratio (%)
```dax
Remote Share % = 
DIVIDE(
    CALCULATE(COUNT(jobs[id]), jobs[job_type] = "Remote"),
    COUNT(jobs[id]),
    0
) * 100
```

### Experience Multiplier Premium (DAX Measure)
```dax
Salary Per Exp Year = 
DIVIDE(
    SUM(jobs[salary_avg]),
    SUM(jobs[experience_years]),
    0
)
```

---

## 4. Visual Layout Recommendations

### Visual 1: Executive KPI Panel (Cards)
* Place 4 card visuals at the top of the canvas:
  1. `[Total Postings]` (Format: Decimal, no decimals)
  2. `[Average Salary]` (Format: Currency, `$` English, no decimals)
  3. `[Remote Share %]` (Format: Percentage, 1 decimal)
  4. **Hiring Companies Count**: `DISTINCTCOUNT(jobs[company])`

### Visual 2: In-Demand Tech Stack (Horizontal Bar Chart)
* **Y-Axis**: `job_skills[skill]`
* **X-Axis**: `Total Postings`
* **Filter**: Top N (e.g., Top 15) skills.
* **Formatting**: Sleek Teal color bar representation.

### Visual 3: Compensation Distribution (Clustered Column Chart)
* **Axis**: Standardized bins of `salary_avg`.
* **Value**: Count of job IDs.
* **Filter**: Filter out anomalous zeroes.

### Visual 4: Salary vs Experience Scatter Plot
* **X-Axis**: `jobs[experience_years]`
* **Y-Axis**: `jobs[salary_avg]`
* **Legend**: `jobs[job_category]`
* Add a trendline to showcase the linear expansion of salary premiums per year of experience.

### Visual 5: Geographical Tech Hub Hotspots (Map / Bubble Map)
* **Location**: `jobs[location_city]`
* **Bubble Size**: `Total Postings`
* **Tooltips**: `Average Salary`

---

## 5. UI Style Sheet & Harmonious Color Palette

To align the Power BI canvas with our Streamlit application's premium glassmorphic dark aesthetic, configure these color hexes:

* **Canvas Background**: `#0b0f19` (Dark Navy Blue)
* **Card & Visual Backgrounds**: `#111827` with 10% transparency (Dark Slate)
* **Primary Metric Highlights (Glow/Teal)**: `#00f2fe`
* **Secondary Indicators (Slate Blue)**: `#4facfe`
* **Accent highlights (Rose/Coral)**: `#f35588`
* **Text / Labels**: `#9ca3af` (Secondary labels) and `#f1f5f9` (Primary titles)
* **Font Family**: **Segoe UI** or **Segoe UI Semibold** (matches Streamlit's sleek headers in Power BI)
