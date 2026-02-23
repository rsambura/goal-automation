
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import json

# Page configuration
st.set_page_config(
    page_title="SDR Goal Automation Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF9900;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 3px solid #FF9900;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

# Sample data generator (replace with actual database connection later)
def generate_sample_sdr_data(start_date, end_date):
    """Generate sample SDR data for demo"""
    np.random.seed(42)
    
    marketplaces = ['FR', 'DE', 'UK', 'JP', 'IN']
    business_lines = ['Grocery', 'AMZL', 'SSD', 'AMZL Special Handling']
    weeks = pd.date_range(start=start_date, end=end_date, freq='W')
    
    data = []
    for week in weeks:
        for marketplace in marketplaces:
            for business in business_lines:
                data.append({
                    'week': week.strftime('%Y-%W'),
                    'marketplace_code': marketplace,
                    'business_line': business,
                    'sdr_numerator': np.random.randint(5, 100),
                    'sdr_denominator': np.random.randint(50, 500),
                    'resolved_contacts': np.random.randint(400, 2000)
                })
    
    return pd.DataFrame(data)

def generate_sample_forecast(start_date, end_date):
    """Generate sample forecast data"""
    np.random.seed(43)
    
    marketplaces = ['FR', 'DE', 'UK', 'JP', 'IN']
    business_lines = ['Grocery', 'AMZL', 'SSD', 'AMZL Special Handling']
    weeks = pd.date_range(start=start_date, end=end_date, freq='W')
    
    data = []
    for week in weeks:
        for marketplace in marketplaces:
            for business in business_lines:
                data.append({
                    'week': week.strftime('%Y-%W'),
                    'marketplace_code': marketplace,
                    'business_line': business,
                    'forecasted_contacts': np.random.randint(500, 2200)
                })
    
    return pd.DataFrame(data)

def calculate_goals(sdr_data, forecast_data):
    """Calculate 2026 goals using baseline data and forecasts"""
    
    # Calculate baseline rates
    baseline_rates = sdr_data.groupby(['marketplace_code', 'business_line']).agg({
        'sdr_numerator': 'sum',
        'sdr_denominator': 'sum',
        'resolved_contacts': 'sum'
    }).reset_index()
    
    # Response rate: denominator / resolved contacts
    baseline_rates['response_rate'] = (
        baseline_rates['sdr_denominator'] / baseline_rates['resolved_contacts']
    )
    
    # Conversion rate: numerator / denominator
    baseline_rates['conversion_rate'] = (
        baseline_rates['sdr_numerator'] / baseline_rates['sdr_denominator']
    )
    
    # Baseline SDR
    baseline_rates['baseline_sdr'] = baseline_rates['conversion_rate']
    
    # Merge with forecast data
    goals = forecast_data.merge(
        baseline_rates[['marketplace_code', 'business_line', 'response_rate', 'conversion_rate', 'baseline_sdr']],
        on=['marketplace_code', 'business_line'],
        how='left'
    )
    
    # Calculate forecasted denominator
    goals['forecasted_denominator'] = (
        goals['response_rate'] * goals['forecasted_contacts']
    )
    
    # Calculate forecasted numerator
    goals['forecasted_numerator'] = (
        goals['conversion_rate'] * goals['forecasted_denominator']
    )
    
    # Calculate forecasted SDR goal
    goals['forecasted_sdr'] = (
        goals['forecasted_numerator'] / goals['forecasted_denominator']
    )
    
    # Calculate variance
    goals['variance_pct'] = (
        (goals['forecasted_sdr'] - goals['baseline_sdr']) / goals['baseline_sdr'] * 100
    )
    
    return goals

# Main application
def main():
    # Header
    st.markdown('<div class="main-header">🎯 SDR Goal Automation Dashboard</div>', unsafe_allow_html=True)
    
    # Sidebar configuration
    st.sidebar.title("⚙️ Configuration")
    st.sidebar.markdown("---")
    
    # Baseline period selection
    st.sidebar.subheader("📅 Baseline Period")
    baseline_preset = st.sidebar.selectbox(
        "Select Baseline",
        ["Q4 2025 (Oct-Dec)", "Full Year 2025", "Q1 2026 (Jan-Mar)", "Custom Date Range"],
        index=0
    )
    
    # Map preset to dates
    baseline_mapping = {
        "Q4 2025 (Oct-Dec)": ("2025-10-01", "2025-12-31"),
        "Full Year 2025": ("2025-01-01", "2025-12-31"),
        "Q1 2026 (Jan-Mar)": ("2026-01-01", "2026-03-31"),
    }
    
    if baseline_preset == "Custom Date Range":
        col1, col2 = st.sidebar.columns(2)
        baseline_start = col1.date_input("Start Date", datetime(2025, 10, 1))
        baseline_end = col2.date_input("End Date", datetime(2025, 12, 31))
        baseline_start = baseline_start.strftime("%Y-%m-%d")
        baseline_end = baseline_end.strftime("%Y-%m-%d")
    else:
        baseline_start, baseline_end = baseline_mapping[baseline_preset]
    
    st.sidebar.info(f"**Baseline:** {baseline_start} to {baseline_end}")
    
    # File upload for forecast
    st.sidebar.markdown("---")
    st.sidebar.subheader("📁 Forecast Data")
    forecast_file = st.sidebar.file_uploader(
        "Upload 2026 Forecast File (Optional)",
        type=['xlsx', 'csv'],
        help="Upload Excel or CSV file with forecasted contacts. Sample data will be used if not provided."
    )
    
    # Calculate button
    st.sidebar.markdown("---")
    calculate_button = st.sidebar.button("🚀 Calculate Goals", type="primary", use_container_width=True)
    
    # Main content area
    if calculate_button:
        with st.spinner("🔄 Loading data and calculating goals..."):
            # Generate sample data (replace with actual database queries later)
            sdr_data = generate_sample_sdr_data(baseline_start, baseline_end)
            
            # Load or create forecast data
            if forecast_file is not None:
                if forecast_file.name.endswith('.csv'):
                    forecast_data = pd.read_csv(forecast_file)
                else:
                    forecast_data = pd.read_excel(forecast_file)
            else:
                forecast_data = generate_sample_forecast('2026-01-01', '2026-12-31')
            
            # Calculate goals
            goals_df = calculate_goals(sdr_data, forecast_data)
            
            # Store in session state
            st.session_state['goals_df'] = goals_df
            st.session_state['baseline_period'] = baseline_preset
            
        st.success("✅ Goals calculated successfully!")
    
    # Display results if available
    if 'goals_df' in st.session_state:
        goals_df = st.session_state['goals_df']
        
        # Key metrics cards
        st.subheader("📈 Key Metrics Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_baseline_sdr = goals_df['baseline_sdr'].mean() * 100
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Avg Baseline SDR</div>
                <div class="metric-value">{avg_baseline_sdr:.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            avg_forecast_sdr = goals_df['forecasted_sdr'].mean() * 100
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Avg Forecasted SDR</div>
                <div class="metric-value">{avg_forecast_sdr:.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            total_forecast_contacts = goals_df['forecasted_contacts'].sum()
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Forecast Contacts</div>
                <div class="metric-value">{total_forecast_contacts:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            avg_variance = goals_df['variance_pct'].mean()
            variance_color = "#10b981" if avg_variance >= 0 else "#ef4444"
            st.markdown(f"""
            <div class="metric-card" style="background: {variance_color};">
                <div class="metric-label">Avg Variance</div>
                <div class="metric-value">{avg_variance:+.2f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Charts", "📈 Comparisons", "📋 Data Table", "💾 Export"
        ])
        
        with tab1:
            st.subheader("Visualization Dashboard")
            
            # Prepare chart data
            chart_data = goals_df.groupby('marketplace_code').agg({
                'baseline_sdr': 'mean',
                'forecasted_sdr': 'mean'
            }).reset_index()
            
            # SDR Comparison Chart
            st.markdown("#### SDR: Baseline vs Forecast by Marketplace")
            chart_config = {
                'chart': {'type': 'column'},
                'title': {'text': 'SDR Comparison by Marketplace'},
                'xAxis': {
                    'categories': chart_data['marketplace_code'].tolist(),
                    'title': {'text': 'Marketplace'}
                },
                'yAxis': {
                    'title': {'text': 'SDR Rate (%)'}
                },
                'series': [
                    {
                        'name': 'Baseline SDR',
                        'data': (chart_data['baseline_sdr'] * 100).round(2).tolist()
                    },
                    {
                        'name': 'Forecasted SDR',
                        'data': (chart_data['forecasted_sdr'] * 100).round(2).tolist()
                    }
                ]
            }
            
            st.json(chart_config)
            
            # Business Line Distribution
            st.markdown("#### Forecasted Contacts by Business Line")
            business_data = goals_df.groupby('business_line').agg({
                'forecasted_contacts': 'sum'
            }).reset_index()
            
            pie_config = {
                'chart': {'type': 'pie'},
                'title': {'text': 'Forecasted Contacts Distribution'},
                'series': [{
                    'name': 'Contacts',
                    'data': [
                        {'name': row['business_line'], 'y': int(row['forecasted_contacts'])}
                        for _, row in business_data.iterrows()
                    ]
                }]
            }
            
            st.json(pie_config)
            
            # Variance Analysis
            st.markdown("#### Variance Analysis: 2026 Goals vs 2025 Baseline")
            variance_data = goals_df.groupby('marketplace_code').agg({
                'variance_pct': 'mean'
            }).reset_index().sort_values('variance_pct', ascending=False)
            
            variance_config = {
                'chart': {'type': 'bar'},
                'title': {'text': 'Variance by Marketplace'},
                'xAxis': {
                    'categories': variance_data['marketplace_code'].tolist(),
                    'title': {'text': 'Marketplace'}
                },
                'yAxis': {
                    'title': {'text': 'Variance (%)'}
                },
                'series': [{
                    'name': 'Variance %',
                    'data': variance_data['variance_pct'].round(2).tolist()
                }]
            }
            
            st.json(variance_config)
        
        with tab2:
            st.subheader("Detailed Comparisons")
            
            comparison_type = st.selectbox(
                "Select Comparison View",
                ["By Marketplace", "By Business Line"]
            )
            
            if comparison_type == "By Marketplace":
                comparison_df = goals_df.groupby('marketplace_code').agg({
                    'baseline_sdr': 'mean',
                    'forecasted_sdr': 'mean',
                    'forecasted_contacts': 'sum',
                    'variance_pct': 'mean'
                }).reset_index()
                
                comparison_df['baseline_sdr'] = (comparison_df['baseline_sdr'] * 100).round(2)
                comparison_df['forecasted_sdr'] = (comparison_df['forecasted_sdr'] * 100).round(2)
                comparison_df['variance_pct'] = comparison_df['variance_pct'].round(2)
                
                st.dataframe(
                    comparison_df.style.background_gradient(subset=['variance_pct'], cmap='RdYlGn'),
                    use_container_width=True
                )
            
            else:
                comparison_df = goals_df.groupby('business_line').agg({
                    'baseline_sdr': 'mean',
                    'forecasted_sdr': 'mean',
                    'forecasted_contacts': 'sum',
                    'variance_pct': 'mean'
                }).reset_index()
                
                comparison_df['baseline_sdr'] = (comparison_df['baseline_sdr'] * 100).round(2)
                comparison_df['forecasted_sdr'] = (comparison_df['forecasted_sdr'] * 100).round(2)
                comparison_df['variance_pct'] = comparison_df['variance_pct'].round(2)
                
                st.dataframe(
                    comparison_df.style.background_gradient(subset=['variance_pct'], cmap='RdYlGn'),
                    use_container_width=True
                )
        
        with tab3:
            st.subheader("Complete Data Table")
            
            display_df = goals_df.copy()
            display_df['baseline_sdr'] = (display_df['baseline_sdr'] * 100).round(2)
            display_df['forecasted_sdr'] = (display_df['forecasted_sdr'] * 100).round(2)
            display_df['variance_pct'] = display_df['variance_pct'].round(2)
            
            st.dataframe(display_df, use_container_width=True)
        
        with tab4:
            st.subheader("Export Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                csv = goals_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"sdr_goals_2026_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                # Summary stats
                summary = f"""
                **Export Summary**
                - Baseline Period: {st.session_state.get('baseline_period', 'N/A')}
                - Total Records: {len(goals_df)}
                - Marketplaces: {goals_df['marketplace_code'].nunique()}
                - Business Lines: {goals_df['business_line'].nunique()}
                - Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """
                st.info(summary)
    
    else:
        # Welcome screen
        st.info("""
        ### 👋 Welcome to the SDR Goal Automation Dashboard!
        
        **Get Started:**
        1. Select your baseline period from the sidebar (Q4 2025, Full Year 2025, etc.)
        2. Optionally upload your 2026 forecast file (Excel or CSV)
        3. Click "🚀 Calculate Goals" to generate your 2026 SDR goals
        
        **Features:**
        - 📊 Interactive charts and visualizations
        - 📈 Baseline vs forecast comparisons
        - 🗺️ Marketplace and business line breakdowns
        - 💾 Export to CSV
        
        **Note:** Currently using sample data for demonstration. Connect to your Andes database for production use.
        
        **Need Help?** Contact the SDS BI team for support.
        """)
        
        # Show sample data structure
        with st.expander("📖 Expected Data Format"):
            st.markdown("""
            **Forecast File Format (Excel/CSV):**
            
            | week | marketplace_code | business_line | forecasted_contacts |
            |------|------------------|---------------|---------------------|
            | 2026-01 | FR | Grocery | 550 |
            | 2026-01 | DE | AMZL | 1300 |
            
            **Required Columns:**
            - `week`: Week identifier (YYYY-WW format)
            - `marketplace_code`: Marketplace code (FR, DE, UK, etc.)
            - `business_line`: Business line (Grocery, AMZL, SSD, etc.)
            - `forecasted_contacts`: Number of forecasted contacts
            """)

if __name__ == "__main__":
    main()

