/**
 * Job Market Intelligence - Asynchronous Controller Application Layer
 * Pure Vanilla JavaScript implementing Chart.js mappings and REST API queries.
 */

// Global Chart Instances to prevent overlap redraws
let chartTrends = null;
let chartSalaryDist = null;
let chartJobSetup = null;
let chartScatter = null;
let chartSkillsBar = null;

// DOM Selectors
const kpiJobs = document.getElementById("kpi-jobs");
const kpiCompanies = document.getElementById("kpi-companies");
const kpiSalary = document.getElementById("kpi-salary");
const kpiRemote = document.getElementById("kpi-remote");

const spinner = document.getElementById("loading-spinner");

const heatmapTable = document.getElementById("heatmap-table");
const skillsPremiumTable = document.getElementById("skills-premium-table");

// Initialization
document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    initFilters();
    initEstimator();
    initAdvisor();
});

// ----------------------------------------------------
// 1. Tab Navigation Controller
// ----------------------------------------------------
function initTabs() {
    const navItems = document.querySelectorAll(".nav-item");
    const tabContents = document.querySelectorAll(".tab-content");

    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const targetTab = item.getAttribute("data-tab");
            
            navItems.forEach(i => i.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));
            
            item.classList.add("active");
            const targetEl = document.getElementById(`tab-${targetTab}`);
            if (targetEl) targetEl.classList.add("active");
            
            // Re-fetch advisor details if switching to advisor tab
            if (targetTab === "advisor") {
                loadAdvisorTrends();
            }
        });
    });
}

// ----------------------------------------------------
// 2. Global Filter Controller
// ----------------------------------------------------
let activeFilters = {
    categories: [],
    cities: [],
    types: []
};

async function initFilters() {
    // Initial fetch to load filters from DB
    showSpinner(true);
    try {
        const res = await fetch("/api/kpis");
        const data = await res.json();
        
        // Populated dynamically
        populateCheckboxGroup("filter-categories", data.options.categories, "categories");
        populateCheckboxGroup("filter-cities", data.options.cities.slice(0, 10), "cities"); // Top 10 cities to prevent long grids
        populateCheckboxGroup("filter-types", data.options.types, "types");
        
        // Load initial analytics
        updateDashboard();
        
        // Setup Reset Button
        document.getElementById("btn-reset-filters").addEventListener("click", () => {
            document.querySelectorAll(".checkbox-group input").forEach(cb => cb.checked = true);
            updateFilterSelection();
        });
        
        // Setup Download CSV
        document.getElementById("btn-download-csv").addEventListener("click", () => {
            const queryStr = getFilterQueryString();
            window.location.href = `/api/download?${queryStr}`;
        });
        
    } catch (e) {
        console.error("Filter initialization failed:", e);
    } finally {
        showSpinner(false);
    }
}

function populateCheckboxGroup(elementId, options, key) {
    const container = document.getElementById(elementId);
    if (!container) return;
    container.innerHTML = "";
    
    options.forEach(opt => {
        const item = document.createElement("label");
        item.className = "checkbox-item";
        
        const cb = document.createElement("input");
        cb.type = "checkbox";
        cb.value = opt;
        cb.checked = true; // default checked
        
        cb.addEventListener("change", () => {
            updateFilterSelection();
        });
        
        item.appendChild(cb);
        item.appendChild(document.createTextNode(opt));
        container.appendChild(item);
    });
}

function updateFilterSelection() {
    activeFilters.categories = getCheckedValues("filter-categories");
    activeFilters.cities = getCheckedValues("filter-cities");
    activeFilters.types = getCheckedValues("filter-types");
    
    updateDashboard();
}

function getCheckedValues(elementId) {
    const container = document.getElementById(elementId);
    if (!container) return [];
    const inputs = container.querySelectorAll("input:checked");
    return Array.from(inputs).map(i => i.value);
}

function getFilterQueryString() {
    const parts = [];
    activeFilters.categories.forEach(c => parts.push(`categories=${encodeURIComponent(c)}`));
    activeFilters.cities.forEach(c => parts.push(`cities=${encodeURIComponent(c)}`));
    activeFilters.types.forEach(t => parts.push(`types=${encodeURIComponent(t)}`));
    return parts.join("&");
}

function showSpinner(show) {
    spinner.style.display = show ? "flex" : "none";
}

// ----------------------------------------------------
// 3. Asynchronous Data Aggregation Update
// ----------------------------------------------------
async function updateDashboard() {
    showSpinner(true);
    const queryStr = getFilterQueryString();
    
    try {
        // 1. Fetch KPIs
        const kpiRes = await fetch(`/api/kpis?${queryStr}`);
        const kpiData = await kpiRes.json();
        
        // Update KPI displays
        kpiJobs.textContent = kpiData.kpis.total_jobs.toLocaleString();
        kpiCompanies.textContent = kpiData.kpis.total_companies.toLocaleString();
        kpiSalary.textContent = `$${Math.round(kpiData.kpis.avg_salary).toLocaleString()}`;
        kpiRemote.textContent = `${kpiData.kpis.remote_pct.toFixed(1)}%`;
        
        // 2. Fetch Charts Data
        const chartRes = await fetch(`/api/charts?${queryStr}`);
        const chartData = await chartRes.json();
        
        // Load Charts
        renderTrendsChart(chartData.trends_line);
        renderSalaryDistChart(chartData.salary_histogram);
        renderJobSetupChart(chartData.donut);
        renderScatterChart(chartData.scatter);
        renderSkillsBarChart(chartData.skills_bar);
        renderHeatmapTable(chartData.heatmap);
        
    } catch (e) {
        console.error("Dashboard update failed:", e);
    } finally {
        showSpinner(false);
    }
}

// ----------------------------------------------------
// 4. Chart.js & Relational Visualizations Mappings
// ----------------------------------------------------
function renderTrendsChart(data) {
    if (chartTrends) chartTrends.destroy();
    
    // Group monthly counts by month and category
    // Months x Category dataset compile
    const categories = [...new Set(data.map(d => d.category))];
    const months = [...new Set(data.map(d => d.month))].sort();
    
    const datasets = categories.map((cat, i) => {
        const catData = months.map(m => {
            const record = data.find(d => d.month === m && d.category === cat);
            return record ? record.count : 0;
        });
        
        // Stylized color lines matching theme
        const colors = ["#00f2fe", "#f35588", "#a78bfa", "#34d399", "#fbbf24"];
        const color = colors[i % colors.length];
        
        return {
            label: cat,
            data: catData,
            borderColor: color,
            backgroundColor: "transparent",
            borderWidth: 3,
            tension: 0.3,
            pointRadius: 4
        };
    });
    
    const ctx = document.getElementById("chart-trends").getContext("2d");
    chartTrends = new Chart(ctx, {
        type: "line",
        data: { labels: months, datasets: datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: "#e2e8f0" } }
            },
            scales: {
                x: { grid: { color: "#1f2937" }, ticks: { color: "#9ca3af" } },
                y: { grid: { color: "#1f2937" }, ticks: { color: "#9ca3af" } }
            }
        }
    });
}

function renderSalaryDistChart(data) {
    if (chartSalaryDist) chartSalaryDist.destroy();
    
    // Sort data by floor size
    data.sort((a, b) => a.floor - b.floor);
    
    const labels = data.map(d => d.bin);
    const counts = data.map(d => d.count);
    
    const ctx = document.getElementById("chart-salary-dist").getContext("2d");
    chartSalaryDist = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Hiring Listings Count",
                data: counts,
                backgroundColor: "#00f2fe",
                borderRadius: 4,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: "#9ca3af", font: { size: 9 } } },
                y: { grid: { color: "#1f2937" }, ticks: { color: "#9ca3af" } }
            }
        }
    });
}

function renderJobSetupChart(data) {
    if (chartJobSetup) chartJobSetup.destroy();
    
    const labels = data.map(d => d.job_type);
    const counts = data.map(d => d.count);
    
    const ctx = document.getElementById("chart-job-setup").getContext("2d");
    chartJobSetup = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: counts,
                backgroundColor: ["#00f2fe", "#a78bfa", "#f35588"],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "bottom", labels: { color: "#e2e8f0" } }
            },
            cutout: "55%"
        }
    });
}

function renderScatterChart(data) {
    if (chartScatter) chartScatter.destroy();
    
    // Group scatter points by category
    const categories = [...new Set(data.map(d => d.job_category))];
    const colors = ["#00f2fe", "#f35588", "#a78bfa", "#34d399", "#fbbf24"];
    
    const datasets = categories.map((cat, i) => {
        const catPoints = data.filter(d => d.job_category === cat).map(d => ({
            x: d.experience_years,
            y: d.salary_avg,
            title: d.job_title,
            company: d.company
        }));
        
        return {
            label: cat,
            data: catPoints,
            backgroundColor: colors[i % colors.length],
            pointRadius: 5,
            pointHoverRadius: 7
        };
    });
    
    const ctx = document.getElementById("chart-scatter").getContext("2d");
    chartScatter = new Chart(ctx, {
        type: "scatter",
        data: { datasets: datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "right", labels: { color: "#e2e8f0" } },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const point = context.raw;
                            return `${point.title} (${point.company}): Exp: ${point.x} yrs, Salary: $${Math.round(point.y).toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: "Experience Required (Years)", color: "#e2e8f0" },
                    grid: { color: "#1f2937" },
                    ticks: { color: "#9ca3af" }
                },
                y: {
                    title: { display: true, text: "Compensation (USD)", color: "#e2e8f0" },
                    grid: { color: "#1f2937" },
                    ticks: {
                        color: "#9ca3af",
                        callback: (val) => `$${val.toLocaleString()}`
                    }
                }
            }
        }
    });
}

function renderSkillsBarChart(data) {
    if (chartSkillsBar) chartSkillsBar.destroy();
    
    const labels = data.map(d => d.skill);
    const counts = data.map(d => d.count);
    
    const ctx = document.getElementById("chart-skills-bar").getContext("2d");
    chartSkillsBar = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                data: counts,
                backgroundColor: "#4facfe",
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: "y",
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { color: "#1f2937" }, ticks: { color: "#9ca3af" } },
                y: { grid: { display: false }, ticks: { color: "#e2e8f0" } }
            }
        }
    });
}

function renderHeatmapTable(data) {
    if (!heatmapTable) return;
    heatmapTable.innerHTML = "";
    
    // Create matrix header row
    const headRow = document.createElement("tr");
    headRow.appendChild(document.createElement("th")); // top-left empty cell
    
    data.skills.forEach(s => {
        const th = document.createElement("th");
        th.textContent = s;
        headRow.appendChild(th);
    });
    heatmapTable.appendChild(headRow);
    
    // Create cells
    data.matrix.forEach(row => {
        const tr = document.createElement("tr");
        
        // Skill name header
        const th = document.createElement("th");
        th.textContent = row.skill;
        tr.appendChild(th);
        
        row.cooccurrences.forEach(val => {
            const td = document.createElement("td");
            td.textContent = `${val}%`;
            td.className = "heatmap-cell";
            
            // Synthesize background visual intensity color based on percentage overlap (teal gradient scale)
            const alpha = (val / 100).toFixed(2);
            td.style.backgroundColor = `rgba(0, 242, 254, ${alpha})`;
            td.style.color = val > 45 ? "#000000" : "#ffffff";
            
            tr.appendChild(td);
        });
        
        heatmapTable.appendChild(tr);
    });
}

// Populate skills average table
function renderSkillsPremiumTable(premiums) {
    if (!skillsPremiumTable) return;
    skillsPremiumTable.innerHTML = "";
    
    premiums.forEach(p => {
        const tr = document.createElement("tr");
        
        const tdSkill = document.createElement("td");
        tdSkill.innerHTML = `<strong>${p.skill}</strong>`;
        
        const tdCount = document.createElement("td");
        tdCount.textContent = p.job_count.toLocaleString();
        
        const tdSalary = document.createElement("td");
        tdSalary.textContent = `$${Math.round(p.average_salary).toLocaleString()}`;
        tdSalary.style.color = "#00f2fe";
        tdSalary.style.fontWeight = "600";
        
        tr.appendChild(tdSkill);
        tr.appendChild(tdCount);
        tr.appendChild(tdSalary);
        
        skillsPremiumTable.appendChild(tr);
    });
}

// ----------------------------------------------------
// 5. ML Salary Prediction Calculator Forms
// ----------------------------------------------------
async function initEstimator() {
    const categorySel = document.getElementById("pred-category");
    const citySel = document.getElementById("pred-city");
    const typeSel = document.getElementById("pred-type");
    const expRange = document.getElementById("pred-experience");
    const expVal = document.getElementById("exp-val");
    const skillsGrid = document.getElementById("pred-skills-grid");
    const btnPredict = document.getElementById("btn-predict");
    
    const resultsPanel = document.getElementById("predict-results");
    const resAvg = document.getElementById("res-avg");
    const resRange = document.getElementById("res-range");
    const resTips = document.getElementById("res-tips");

    // Live experience counter slider value update
    expRange.addEventListener("input", () => {
        expVal.textContent = expRange.value;
    });
    
    // Fetch unique options to populate selects
    try {
        const res = await fetch("/api/kpis");
        const data = await res.json();
        
        // Populate options
        populateSelect(categorySel, data.options.categories);
        populateSelect(citySel, data.options.cities);
        populateSelect(typeSel, data.options.types);
        
        // Load skills list from recommendation endpoints to fill checkboxes
        const recRes = await fetch("/api/recommend", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({skills: []})
        });
        const recData = await recRes.json();
        
        // Select Top 25 general skills for ML calculator checklist
        recData.all_skills_list.slice(0, 25).forEach(skill => {
            const lbl = document.createElement("label");
            lbl.className = "checkbox-item";
            
            const cb = document.createElement("input");
            cb.type = "checkbox";
            cb.value = skill;
            
            lbl.appendChild(cb);
            lbl.appendChild(document.createTextNode(skill));
            skillsGrid.appendChild(lbl);
        });
        
    } catch (e) {
        console.error("Estimator setups failed:", e);
    }
    
    // Prediction Action Trigger
    btnPredict.addEventListener("click", async () => {
        const checkedSkills = Array.from(skillsGrid.querySelectorAll("input:checked")).map(cb => cb.value);
        
        const payload = {
            category: categorySel.value,
            city: citySel.value,
            job_type: typeSel.value,
            experience: parseFloat(expRange.value),
            skills: checkedSkills
        };
        
        btnPredict.disabled = true;
        btnPredict.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Estimating...';
        
        try {
            const predRes = await fetch("/api/predict", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(payload)
            });
            const pred = await predRes.json();
            
            // Format metrics
            resAvg.textContent = `$${pred.predicted_avg.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            resRange.textContent = `$${Math.round(pred.predicted_min).toLocaleString()} - $${Math.round(pred.predicted_max).toLocaleString()}`;
            
            // Update custom tips
            resTips.innerHTML = `<strong>Dynamic Insights:</strong> The average salary premium in <strong>${payload.city}</strong> for a candidate with <strong>${payload.experience} years</strong> of experience in <strong>${payload.category}</strong> is highly competitive. Adding hot technologies like ${payload.skills.slice(0,3).join(", ") || 'cloud platforms'} generally increases market value by 8% to 15% in similar roles.`;
            
            resultsPanel.style.display = "flex";
            resultsPanel.scrollIntoView({behavior: "smooth"});
            
        } catch (e) {
            console.error("Prediction failed:", e);
        } finally {
            btnPredict.disabled = false;
            btnPredict.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Calculate Estimated Annual Salary Range';
        }
    });
}

function populateSelect(selectEl, options) {
    if (!selectEl) return;
    selectEl.innerHTML = "";
    options.forEach(opt => {
        const el = document.createElement("option");
        el.value = opt;
        el.textContent = opt;
        selectEl.appendChild(el);
    });
}

// ----------------------------------------------------
// 6. AI Insights & Advisor Controller
// ----------------------------------------------------
async function initAdvisor() {
    const advCategory = document.getElementById("adv-category");
    const advTarget = document.getElementById("adv-target");
    const advSkills = document.getElementById("adv-skills");
    const btnAdvisor = document.getElementById("btn-advisor");
    
    const advResults = document.getElementById("advisor-results");
    const advSummaryTxt = document.getElementById("adv-summary-txt");
    const advisorTableBody = document.getElementById("advisor-table-body");
    
    // Populate dropdown options
    try {
        const res = await fetch("/api/kpis");
        const data = await res.json();
        populateSelect(advCategory, data.options.categories);
        populateSelect(advTarget, data.options.categories);
    } catch(e) {
        console.error("Advisor options load failed:", e);
    }
    
    btnAdvisor.addEventListener("click", async () => {
        const candSkills = advSkills.value.split(",").map(s => s.strip ? s.strip() : s.trim()).filter(s => s !== "");
        
        const payload = {
            current_category: advCategory.value,
            target_category: advTarget.value,
            skills: candSkills
        };
        
        btnAdvisor.disabled = true;
        btnAdvisor.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing Profile Gaps...';
        
        try {
            const advRes = await fetch("/api/recommend_advisor", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(payload)
            });
            const adv = await advRes.json();
            
            // Format advice
            advSummaryTxt.innerHTML = adv.recommendation_text;
            
            // Populate skills table
            advisorTableBody.innerHTML = "";
            if (adv.missing_skills && adv.missing_skills.length > 0) {
                adv.missing_skills.forEach(s => {
                    const tr = document.createElement("tr");
                    
                    const tdName = document.createElement("td");
                    tdName.innerHTML = `<strong>${s.skill}</strong>`;
                    
                    const tdCount = document.createElement("td");
                    tdCount.textContent = s.market_demand.toLocaleString();
                    
                    const tdSalary = document.createElement("td");
                    tdSalary.textContent = `$${Math.round(s.skill_avg_salary).toLocaleString()}`;
                    tdSalary.style.color = "#00f2fe";
                    
                    tr.appendChild(tdName);
                    tr.appendChild(tdCount);
                    tr.appendChild(tdSalary);
                    advisorTableBody.appendChild(tr);
                });
            } else {
                advisorTableBody.innerHTML = '<tr><td colspan="3" style="text-align:center;">Outstanding! You possess all high-demand technologies for this track.</td></tr>';
            }
            
            advResults.style.display = "block";
            advResults.scrollIntoView({behavior: "smooth"});
            
        } catch (e) {
            console.error("Advisor evaluation failed:", e);
        } finally {
            btnAdvisor.disabled = false;
            btnAdvisor.innerHTML = '<i class="fa-solid fa-rocket"></i> Analyze Skill Gap & Target Premium';
        }
    });
}

// Load static general AI insights tables
async function loadAdvisorTrends() {
    const emergingList = document.getElementById("emerging-list");
    const industriesTable = document.getElementById("industries-table");
    
    try {
        const res = await fetch("/api/insights");
        const data = await res.json();
        
        // 1. Emerging technologies share growth
        emergingList.innerHTML = "";
        data.emerging.forEach(e => {
            const li = document.createElement("li");
            li.innerHTML = `<i class="fa-solid fa-circle-up" style="color:#00f2fe; margin-right:8px;"></i> 
                            <strong>${e.skill}</strong>: Share of monthly postings is <strong>growing</strong> 
                            (regression trend slope: <code>+${e.trend_slope.toFixed(4)}</code>) with <strong>${e.total_listings.toLocaleString()}</strong> listings overall.`;
            emergingList.appendChild(li);
        });
        
        // 2. Industry sector averages
        industriesTable.innerHTML = "";
        data.industries.forEach(ind => {
            const tr = document.createElement("tr");
            
            const tdName = document.createElement("td");
            tdName.textContent = ind.industry;
            
            const tdCount = document.createElement("td");
            tdCount.textContent = ind.job_count.toLocaleString();
            
            const tdSalary = document.createElement("td");
            tdSalary.textContent = `$${Math.round(ind.average_salary).toLocaleString()}`;
            tdSalary.style.fontWeight = "600";
            
            const tdExp = document.createElement("td");
            tdExp.textContent = `${ind.average_experience.toFixed(1)} yrs`;
            
            tr.appendChild(tdName);
            tr.appendChild(tdCount);
            tr.appendChild(tdSalary);
            tr.appendChild(tdExp);
            
            industriesTable.appendChild(tr);
        });
        
        // 3. Populate skills average premium table inside Tech Stack tab
        renderSkillsPremiumTable(data.premiums);
        
    } catch(e) {
        console.error("Advisor metrics load failed:", e);
    }
}
