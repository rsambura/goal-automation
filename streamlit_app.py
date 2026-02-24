import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px

# ==============================
# PAGE CONFIG
# ==============================

st.set_page_config(
    page_title="SDR Goal Automation Dashboard",
    page_icon="🎯",
    layout="wide"
)

st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #FF9900;
    text-align: center;
    margin-bottom: 2rem;
}
.section-card {
    background: white;
    padding: 1.5rem;
    border-radius: 18px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.08);
    margin-bottom: 1.5rem;
}
.metric-box {
    background: linear-gradient(135deg, #FF9900 0%, #FF6600 100%);
    padding: 1.2rem;
    border-radius: 14px;
    color: white;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header">🎯 SDR Goal Automation Dashboard</h1>', unsafe_allow_html=True)

# ==============================
# BASELINE GENERATION
# ==============================

def generate_baseline():
    np.random.seed(42)
    marketplaces = ['FR', 'DE', 'UK', 'JP', 'IN', 'US']
    business_lines = ['Grocery', 'AMXL', 'SSD', 'AMZL Special Handling']
    contact_types = ['Email', 'Phone', 'Chat']

    data = []
    for m in marketplaces:
        for b in business_lines:
            for c in contact_types:
                rate = np.random.uniform(0.15, 0.25)
                data.append({
                    "marketplace_code": m,
                    "business_line": b,
                    "contact_type": c,
                    "baseline_sdr": rate
                })
    return pd.DataFrame(data)

baseline_df = generate_baseline()

# ==============================
# FILE UPLOAD
# ==============================

st.sidebar.header("📂 Upload Forecast File")
forecast_file = st.sidebar.file_uploader(
    "Upload CSV or Excel",
    type=["csv", "xlsx"]
)

if forecast_file is None:
    st.warning("Upload forecast file to continue.")
    st.stop()

if forecast_file.name.endswith(".csv"):
    forecast_df = pd.read_csv(forecast_file)
else:
    forecast_df = pd.read_excel(forecast_file)

# ==============================
# DETECT TIME LEVEL
# ==============================

time_column = None

if "date" in forecast_df.columns:
    time_column = "date"
elif "week" in forecast_df.columns:
    time_column = "week"
elif "month" in forecast_df.columns:
    time_column = "month"
else:
    st.error("Forecast must contain date, week, or month column.")
    st.stop()

# ==============================
# REQUIRED STRUCTURE
# ==============================

required_cols = [
    "marketplace_code",
    "business_line",
    "forecasted_contacts"
]

missing = [c for c in required_cols if c not in forecast_df.columns]
if missing:
    st.error(f"Missing columns: {missing}")
    st.stop()

# ==============================
# MERGE BASELINE
# ==============================

merge_cols = ["marketplace_code", "business_line"]

if "contact_type" in forecast_df.columns:
    merge_cols.append("contact_type")
else:
    baseline_df = baseline_df.groupby(
        ["marketplace_code", "business_line"]
    )["baseline_sdr"].mean().reset_index()

goals_df = forecast_df.merge(
    baseline_df,
    on=merge_cols,
    how="left"
)

# ==============================
# CALCULATIONS
# ==============================

goals_df["forecasted_denominator"] = goals_df["forecasted_contacts"]
goals_df["forecasted_numerator"] = (
    goals_df["forecasted_contacts"] * goals_df["baseline_sdr"]
)

goals_df["forecasted_sdr"] = goals_df["baseline_sdr"]

# ==============================
# KPI
# ==============================

st.markdown('<div class="section-card">', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

avg_sdr = goals_df["forecasted_sdr"].mean() * 100
total_contacts = goals_df["forecasted_contacts"].sum()
records = len(goals_df)

col1.markdown(f'<div class="metric-box"><h3>Avg SDR</h3><h2>{avg_sdr:.2f}%</h2></div>', unsafe_allow_html=True)
col2.markdown(f'<div class="metric-box"><h3>Total Contacts</h3><h2>{total_contacts:,.0f}</h2></div>', unsafe_allow_html=True)
col3.markdown(f'<div class="metric-box"><h3>Rows</h3><h2>{records}</h2></div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# FILTERS
# ==============================

st.markdown('<div class="section-card">', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    mp_filter = st.multiselect(
        "Marketplace",
        goals_df["marketplace_code"].unique(),
        default=goals_df["marketplace_code"].unique()
    )

with col2:
    bl_filter = st.multiselect(
        "Business Line",
        goals_df["business_line"].unique(),
        default=goals_df["business_line"].unique()
    )

if "contact_type" in goals_df.columns:
    with col3:
        ct_filter = st.multiselect(
            "Contact Type",
            goals_df["contact_type"].unique(),
            default=goals_df["contact_type"].unique()
        )
else:
    ct_filter = None

filtered = goals_df[
    goals_df["marketplace_code"].isin(mp_filter) &
    goals_df["business_line"].isin(bl_filter)
]

if ct_filter:
    filtered = filtered[filtered["contact_type"].isin(ct_filter)]

# ==============================
# AGGREGATION (AUTO LEVEL)
# ==============================

group_cols = [time_column]

trend_df = filtered.groupby(group_cols).agg({
    "forecasted_sdr": "mean",
    "forecasted_contacts": "sum"
}).reset_index()

trend_df["forecasted_sdr"] *= 100

# ==============================
# SDR CHART
# ==============================

st.subheader("📈 SDR Trend")

fig1 = px.line(
    trend_df,
    x=time_column,
    y="forecasted_sdr",
    markers=True,
    template="plotly_white"
)

fig1.update_layout(hovermode="x unified")
st.plotly_chart(fig1, use_container_width=True)

# ==============================
# CONTACT TREND
# ==============================

st.subheader("📞 Contact Trend")

fig2 = px.line(
    trend_df,
    x=time_column,
    y="forecasted_contacts",
    markers=True,
    template="plotly_white"
)

fig2.update_layout(hovermode="x unified")
st.plotly_chart(fig2, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# EXPORT
# ==============================

st.subheader("💾 Export")

csv = filtered.to_csv(index=False)

st.download_button(
    "Download Filtered Data",
    csv,
    f"sdr_goals_{datetime.now().strftime('%Y%m%d')}.csv",
    "text/csv"
)
