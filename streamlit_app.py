```python

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="SDR Goal Automation Dashboard",
    page_icon="🎯",
    layout="wide"
)

# Custom CSS for Amazon orange branding
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF9900;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stButton>button {
        background-color: #FF9900;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        padding: 0.5rem 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">🎯 SDR Goal Automation Dashboard</h1>', unsafe_allow_html=True)

# Generate sample SDR data
def generate_sample_data():
    """Generate sample SDR data for demonstration"""
    np.random.seed(42)
    
    marketplaces = ['FR', 'DE', 'UK', 'JP', 'IN']
    business_lines = ['Grocery', 'AMZL', 'SSD', 'AMZL Special Handling']
    
    data = []
    for marketplace in marketplaces:
        for business_line in business_lines:
            # Generate sample metrics
            resolved_contacts = np.random.randint(800, 1500)
            sdr_denominator = int(resolved_contacts * np.random.uniform(0.7, 0.9))
            sdr_numerator = int(sdr_denominator * np.random.uniform(0.15, 0.25))
            
            data.append({
                'marketplace_code': marketplace,
                'business_line': business_line,
                'resolved_contacts': resolved_contacts,
                'sdr_denominator': sdr_denominator,
                'sdr_numerator': sdr_numerator
            })
    
    return pd.DataFrame(data)

# Calculate goals function
def calculate_goals(sdr_data, forecast_data):
    """Calculate 2026 goals using baseline data and forecasts"""
    
    try:
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
        
        # Check if required columns exist in forecast_data
        required_cols = ['marketplace_code', 'business_line', 'forecasted_contacts']
        missing_cols = [col for col in required_cols if col not in forecast_data.columns]
        
        if missing_cols:
            st.error(f"❌ Missing required columns in forecast file: {', '.join(missing_cols)}")
            return None
        
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
        
    except Exception as e:
        st.error(f"❌ Error calculating goals: {str(e)}")
        return None

# Main function
def main():
    # Sidebar configuration
    st.sidebar.header("Configuration")
    
    # Baseline period selection
    st.sidebar.subheader("Baseline Period")
    baseline_period = st.sidebar.selectbox(
        "Select Baseline",
        ["Q4 2025 (Oct-Dec)", "Full Year 2025", "Q1 2026 (Jan-Mar)", "Custom Date Range"]
    )
    
    if baseline_period == "Q4 2025 (Oct-Dec)":
        baseline_start = "2025-10-01"
        baseline_end = "2025-12-31"
    elif baseline_period == "Full Year 2025":
        baseline_start = "2025-01-01"
        baseline_end = "2025-12-31"
    elif baseline_period == "Q1 2026 (Jan-Mar)":
        baseline_start = "2026-01-01"
        baseline_end = "2026-03-31"
    else:
        baseline_start = st.sidebar.date_input("Start Date").strftime("%Y-%m-%d")
        baseline_end = st.sidebar.date_input("End Date").strftime("%Y-%m-%d")
    
    st.sidebar.info(f"Baseline: {baseline_start} to {baseline_end}")
    
    # Forecast data upload
    st.sidebar.subheader("Forecast Data")
    forecast_file = st.sidebar.file_uploader(
        "Upload 2026 Forecast File (Optional)",
        type=['xlsx', 'csv'],
        help="Limit 200MB per file - XLSX, CSV"
    )
    
    # Calculate goals button
    if st.sidebar.button("🚀 Calculate Goals", use_container_width=True):
        with st.spinner("Calculating goals..."):
            # Generate sample baseline data
            sdr_data = generate_sample_data()
            
            # Load forecast data or generate sample
            if forecast_file is not None:
                try:
                    if forecast_file.name.endswith('.csv'):
                        forecast_data = pd.read_csv(forecast_file)
                    else:
                        forecast_data = pd.read_excel(forecast_file)
                except Exception as e:
                    st.error(f"❌ Error reading forecast file: {str(e)}")
                    st.info("💡 Please convert your Excel file to CSV format and try again.")
                    return
            else:
                # Generate sample forecast data
                forecast_data = pd.DataFrame({
                    'week': ['2026-01'] * 20,
                    'marketplace_code': ['FR', 'DE', 'UK', 'JP', 'IN'] * 4,
                    'business_line': ['Grocery', 'AMZL', 'SSD', 'AMZL Special Handling', 'Grocery'] * 4,
                    'forecasted_contacts': np.random.randint(500, 1500, 20)
                })
            
            # Calculate goals
            goals_df = calculate_goals(sdr_data, forecast_data)
            
            if goals_df is not None:
                st.session_state['goals_df'] = goals_df
                st.session_state['baseline_period'] = baseline_period
                st.success("✅ Goals calculated successfully!")
    
    # Display results if available
    if 'goals_df' in st.session_state:
        goals_df = st.session_state['goals_df']
        
        # Key metrics overview
        st.subheader("Key Metrics Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_baseline = goals_df['baseline_sdr'].mean() * 100
            st.metric("Avg Baseline SDR", f"{avg_baseline:.2f}%")
        
        with col2:
            avg_forecasted = goals_df['forecasted_sdr'].mean() * 100
            st.metric("Avg Forecasted SDR", f"{avg_forecasted:.2f}%")
        
        with col3:
            total_contacts = goals_df['forecasted_contacts'].sum()
            st.metric("Total Forecast Contacts", f"{total_contacts:,.0f}")
        
        with col4:
            avg_variance = goals_df['variance_pct'].mean()
            st.metric("Avg Variance", f"{avg_variance:+.2f}%")
        
        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Charts", "🔍 Comparisons", "📋 Data Table", "💾 Export"])
        
        with tab1:
            st.subheader("SDR Goals Visualization")
            
            # Bar chart: Baseline vs Forecasted by Marketplace
            chart_data = goals_df.groupby('marketplace_code').agg({
                'baseline_sdr': 'mean',
                'forecasted_sdr': 'mean'
            }).reset_index()
            
            chart_data['baseline_sdr'] = chart_data['baseline_sdr'] * 100
            chart_data['forecasted_sdr'] = chart_data['forecasted_sdr'] * 100
            
            st.bar_chart(chart_data.set_index('marketplace_code')[['baseline_sdr', 'forecasted_sdr']])
            
            # Contacts by business line
            st.subheader("Forecasted Contacts by Business Line")
            contacts_by_bl = goals_df.groupby('business_line')['forecasted_contacts'].sum().reset_index()
            st.bar_chart(contacts_by_bl.set_index('business_line'))
        
        with tab2:
            st.subheader("Detailed Comparisons")
            
            comparison_type = st.radio("Compare by:", ["By Marketplace", "By Business Line"])
            
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
                
                st.dataframe(comparison_df, use_container_width=True)
                
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
                
                st.dataframe(comparison_df, use_container_width=True)
        
        with tab3:
            st.subheader("Complete Data Table")
            
            # Format display columns
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

if __name__ == "__main__":
    main()

```
