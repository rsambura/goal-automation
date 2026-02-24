```python

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import re

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
    .adjustment-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #FF9900;
        margin: 0.5rem 0;
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

# Initialize session state
if 'adjustments' not in st.session_state:
    st.session_state['adjustments'] = []
if 'goals_df' not in st.session_state:
    st.session_state['goals_df'] = None
if 'baseline_df' not in st.session_state:
    st.session_state['baseline_df'] = None

# Generate sample SDR data
def generate_sample_data():
    """Generate sample SDR data for demonstration"""
    np.random.seed(42)
    
    marketplaces = ['FR', 'DE', 'UK', 'JP', 'IN', 'US']
    business_lines = ['Grocery', 'AMXL', 'SSD', 'AMZL Special Handling']
    
    data = []
    for marketplace in marketplaces:
        for business_line in business_lines:
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

# AI Parser - Natural Language Command Parser
def parse_adjustment_command(command):
    """
    Parse natural language adjustment commands
    
    Examples:
    - "Add 10% for Prime Day in US AMXL"
    - "Increase June goals by 5% for all EU"
    - "Apply 15% uplift for holiday season"
    """
    
    adjustment = {
        'action': None,
        'percentage': None,
        'date': None,
        'marketplace': None,
        'business_line': None,
        'original_command': command
    }
    
    cmd = command.lower()
    
    # 1. Extract Action
    if any(word in cmd for word in ['add', 'increase', 'apply', 'uplift', 'boost']):
        adjustment['action'] = 'increase'
    elif any(word in cmd for word in ['reduce', 'decrease', 'lower', 'cut']):
        adjustment['action'] = 'decrease'
    
    # 2. Extract Percentage
    pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%', cmd)
    if pct_match:
        adjustment['percentage'] = float(pct_match.group(1))
    
    # 3. Extract Date/Event
    if 'prime day' in cmd:
        adjustment['date'] = '2026-23'
        adjustment['date_label'] = 'Prime Day (Week 2026-23)'
    elif 'holiday' in cmd or 'christmas' in cmd:
        adjustment['date'] = '2026-48'
        adjustment['date_label'] = 'Holiday Season (Week 2026-48)'
    elif 'june' in cmd:
        adjustment['date'] = '2026-06'
        adjustment['date_label'] = 'June 2026'
    elif 'q2' in cmd:
        adjustment['date'] = 'Q2'
        adjustment['date_label'] = 'Q2 2026 (Apr-Jun)'
    elif 'q3' in cmd:
        adjustment['date'] = 'Q3'
        adjustment['date_label'] = 'Q3 2026 (Jul-Sep)'
    elif 'q4' in cmd:
        adjustment['date'] = 'Q4'
        adjustment['date_label'] = 'Q4 2026 (Oct-Dec)'
    
    # 4. Extract Marketplace
    if 'us' in cmd and 'amxl' not in cmd:
        adjustment['marketplace'] = ['US']
    elif 'fr' in cmd:
        adjustment['marketplace'] = ['FR']
    elif 'de' in cmd:
        adjustment['marketplace'] = ['DE']
    elif 'uk' in cmd:
        adjustment['marketplace'] = ['UK']
    elif 'jp' in cmd:
        adjustment['marketplace'] = ['JP']
    elif 'in' in cmd and 'increase' not in cmd:
        adjustment['marketplace'] = ['IN']
    elif 'all eu' in cmd or 'eu' in cmd:
        adjustment['marketplace'] = ['FR', 'DE', 'UK']
    elif 'all marketplace' in cmd or 'all markets' in cmd:
        adjustment['marketplace'] = 'ALL'
    
    # 5. Extract Business Line
    if 'amxl' in cmd or 'amzl' in cmd:
        adjustment['business_line'] = 'AMXL'
    elif 'grocery' in cmd:
        adjustment['business_line'] = 'Grocery'
    elif 'ssd' in cmd:
        adjustment['business_line'] = 'SSD'
    elif 'special handling' in cmd:
        adjustment['business_line'] = 'AMZL Special Handling'
    elif 'all business' in cmd:
        adjustment['business_line'] = 'ALL'
    
    return adjustment

# Apply adjustment to goals
def apply_adjustment(goals_df, adjustment):
    """Apply parsed adjustment to baseline goals"""
    
    if goals_df is None:
        return None
    
    # Create a copy to avoid modifying original
    adjusted_df = goals_df.copy()
    
    # Create filter mask
    mask = pd.Series([True] * len(adjusted_df))
    
    # Filter by marketplace
    if adjustment['marketplace'] and adjustment['marketplace'] != 'ALL':
        mask &= adjusted_df['marketplace_code'].isin(adjustment['marketplace'])
    
    # Filter by business line
    if adjustment['business_line'] and adjustment['business_line'] != 'ALL':
        mask &= adjusted_df['business_line'] == adjustment['business_line']
    
    # Apply percentage adjustment
    if adjustment['action'] == 'increase':
        multiplier = 1 + (adjustment['percentage'] / 100)
    else:
        multiplier = 1 - (adjustment['percentage'] / 100)
    
    # Update forecasted SDR
    adjusted_df.loc[mask, 'forecasted_sdr'] *= multiplier
    
    # Recalculate variance
    adjusted_df['variance_pct'] = (
        (adjusted_df['forecasted_sdr'] - adjusted_df['baseline_sdr']) /
        adjusted_df['baseline_sdr'] * 100
    )
    
    return adjusted_df

# Calculate goals function
def calculate_goals(sdr_data, forecast_data=None):
    """Calculate 2026 goals using baseline data and forecasts"""
    
    try:
        # Calculate baseline rates
        baseline_rates = sdr_data.groupby(['marketplace_code', 'business_line']).agg({
            'sdr_numerator': 'sum',
            'sdr_denominator': 'sum',
            'resolved_contacts': 'sum'
        }).reset_index()
        
        baseline_rates['response_rate'] = (
            baseline_rates['sdr_denominator'] / baseline_rates['resolved_contacts']
        )
        
        baseline_rates['conversion_rate'] = (
            baseline_rates['sdr_numerator'] / baseline_rates['sdr_denominator']
        )
        
        baseline_rates['baseline_sdr'] = baseline_rates['conversion_rate']
        
        # Generate or use forecast data
        if forecast_data is None:
            forecast_data = pd.DataFrame({
                'week': ['2026-01'] * 24,
                'marketplace_code': ['FR', 'DE', 'UK', 'JP', 'IN', 'US'] * 4,
                'business_line': ['Grocery', 'AMXL', 'SSD', 'AMZL Special Handling'] * 6,
                'forecasted_contacts': np.random.randint(500, 1500, 24)
            })
        
        # Check required columns
        required_cols = ['marketplace_code', 'business_line', 'forecasted_contacts']
        missing_cols = [col for col in required_cols if col not in forecast_data.columns]
        
        if missing_cols:
            st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
            return None
        
        # Merge with forecast data
        goals = forecast_data.merge(
            baseline_rates[['marketplace_code', 'business_line', 'response_rate', 'conversion_rate', 'baseline_sdr']],
            on=['marketplace_code', 'business_line'],
            how='left'
        )
        
        goals['forecasted_denominator'] = (
            goals['response_rate'] * goals['forecasted_contacts']
        )
        
        goals['forecasted_numerator'] = (
            goals['conversion_rate'] * goals['forecasted_denominator']
        )
        
        goals['forecasted_sdr'] = (
            goals['forecasted_numerator'] / goals['forecasted_denominator']
        )
        
        goals['variance_pct'] = (
            (goals['forecasted_sdr'] - goals['baseline_sdr']) / goals['baseline_sdr'] * 100
        )
        
        return goals
        
    except Exception as e:
        st.error(f"❌ Error calculating goals: {str(e)}")
        return None

# Main function
def main():
    # Title
    st.markdown('<h1 class="main-header">🎯 SDR Goal Automation Dashboard</h1>', unsafe_allow_html=True)
    
    # Step 1: Baseline Selection
    st.subheader("📊 Step 1: Select Baseline Period")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        baseline_period = st.selectbox(
            "Choose baseline period:",
            ["Q4 2025 (Oct-Dec)", "Full Year 2025", "Q1 2026 (Jan-Mar)", "Custom Date Range"],
            help="Select the historical period to use as baseline for 2026 goals"
        )
    
    with col2:
        if st.button("🔄 Calculate Baseline", use_container_width=True):
            with st.spinner("Calculating baseline..."):
                sdr_data = generate_sample_data()
                goals_df = calculate_goals(sdr_data)
                
                if goals_df is not None:
                    st.session_state['baseline_df'] = goals_df.copy()
                    st.session_state['goals_df'] = goals_df.copy()
                    st.session_state['baseline_period'] = baseline_period
                    st.session_state['adjustments'] = []
                    st.success("✅ Baseline calculated successfully!")
    
    # Display baseline info
    if st.session_state['baseline_df'] is not None:
        st.info(f"📅 **Current Baseline:** {st.session_state.get('baseline_period', 'N/A')}")
    
    st.divider()
    
    # Step 2: AI-Powered Adjustments
    st.subheader("🤖 Step 2: AI-Powered Adjustments (Optional)")
    
    st.markdown("""
    **Type your adjustment in natural language!** Examples:
    - *"Add 10% for Prime Day in US AMXL"*
    - *"Increase all EU marketplaces by 5% for Q2"*
    - *"Apply 15% uplift for holiday season"*
    """)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        adjustment_command = st.text_input(
            "Enter adjustment command:",
            placeholder="e.g., Add 10% for Prime Day in US AMXL",
            label_visibility="collapsed"
        )
    
    with col2:
        apply_button = st.button("✨ Apply Adjustment", use_container_width=True)
    
    # Process adjustment
    if apply_button and adjustment_command:
        if st.session_state['goals_df'] is None:
            st.warning("⚠️ Please calculate baseline first!")
        else:
            # Parse the command
            adjustment = parse_adjustment_command(adjustment_command)
            
            # Validate
            if not adjustment['action'] or not adjustment['percentage']:
                st.error("❌ Could not understand the command. Please include an action (add/increase) and percentage (e.g., 10%).")
            else:
                # Show what was understood
                st.markdown("### 🔍 Confirmation")
                
                marketplace_str = ', '.join(adjustment['marketplace']) if isinstance(adjustment['marketplace'], list) else adjustment['marketplace'] or 'ALL'
                business_line_str = adjustment['business_line'] or 'ALL'
                date_str = adjustment.get('date_label', 'All periods')
                
                st.markdown(f"""
                <div class="adjustment-box">
                <strong>I understand you want to:</strong><br>
                • <strong>Action:</strong> {adjustment['action'].title()} by {adjustment['percentage']}%<br>
                • <strong>Period:</strong> {date_str}<br>
                • <strong>Marketplace(s):</strong> {marketplace_str}<br>
                • <strong>Business Line(s):</strong> {business_line_str}
                </div>
                """, unsafe_allow_html=True)
                
                # Apply adjustment
                adjusted_df = apply_adjustment(st.session_state['goals_df'], adjustment)
                
                if adjusted_df is not None:
                    st.session_state['goals_df'] = adjusted_df
                    st.session_state['adjustments'].append({
                        'command': adjustment_command,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'details': adjustment
                    })
                    st.success("✅ Adjustment applied successfully!")
    
    # Show adjustment history
    if st.session_state['adjustments']:
        st.markdown("### 📝 Adjustment History")
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            for i, adj in enumerate(st.session_state['adjustments'], 1):
                st.markdown(f"**{i}.** {adj['command']} *({adj['timestamp']})*")
        
        with col2:
            if st.button("🗑️ Clear All", use_container_width=True):
                st.session_state['goals_df'] = st.session_state['baseline_df'].copy()
                st.session_state['adjustments'] = []
                st.rerun()
    
    st.divider()
    
    # Step 3: Results and Export
    if st.session_state['goals_df'] is not None:
        goals_df = st.session_state['goals_df']
        baseline_df = st.session_state['baseline_df']
        
        st.subheader("📈 Step 3: Results & Export")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            baseline_avg = baseline_df['baseline_sdr'].mean() * 100
            st.metric("Baseline SDR", f"{baseline_avg:.2f}%")
        
        with col2:
            current_avg = goals_df['forecasted_sdr'].mean() * 100
            delta = current_avg - baseline_avg
            st.metric("Current SDR", f"{current_avg:.2f}%", f"{delta:+.2f}%")
        
        with col3:
            total_contacts = goals_df['forecasted_contacts'].sum()
            st.metric("Total Contacts", f"{total_contacts:,.0f}")
        
        with col4:
            avg_variance = goals_df['variance_pct'].mean()
            st.metric("Avg Variance", f"{avg_variance:+.2f}%")
        
        # Tabs for visualization
        tab1, tab2, tab3 = st.tabs(["📊 Charts", "📋 Data Table", "💾 Export"])
        
        with tab1:
            st.subheader("Baseline vs Current Goals")
            
            chart_data = goals_df.groupby('marketplace_code').agg({
                'baseline_sdr': 'mean',
                'forecasted_sdr': 'mean'
            }).reset_index()
            
            chart_data['baseline_sdr'] = chart_data['baseline_sdr'] * 100
            chart_data['forecasted_sdr'] = chart_data['forecasted_sdr'] * 100
            
            st.bar_chart(chart_data.set_index('marketplace_code')[['baseline_sdr', 'forecasted_sdr']])
            
            st.subheader("Contacts by Business Line")
            contacts_by_bl = goals_df.groupby('business_line')['forecasted_contacts'].sum().reset_index()
            st.bar_chart(contacts_by_bl.set_index('business_line'))
        
        with tab2:
            st.subheader("Complete Data Table")
            
            display_df = goals_df.copy()
            display_df['baseline_sdr'] = (display_df['baseline_sdr'] * 100).round(2)
            display_df['forecasted_sdr'] = (display_df['forecasted_sdr'] * 100).round(2)
            display_df['variance_pct'] = display_df['variance_pct'].round(2)
            
            st.dataframe(display_df, use_container_width=True)
        
        with tab3:
            st.subheader("Export Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Generate filename
                adjustment_suffix = f"_adjusted_v{len(st.session_state['adjustments'])}" if st.session_state['adjustments'] else "_baseline"
                filename = f"sdr_goals_2026{adjustment_suffix}_{datetime.now().strftime('%Y%m%d')}.csv"
                
                csv = goals_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=filename,
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                summary = f"""
                **Export Summary**
                - Baseline Period: {st.session_state.get('baseline_period', 'N/A')}
                - Adjustments Applied: {len(st.session_state['adjustments'])}
                - Total Records: {len(goals_df)}
                - Marketplaces: {goals_df['marketplace_code'].nunique()}
                - Business Lines: {goals_df['business_line'].nunique()}
                - Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """
                st.info(summary)
                
                if st.session_state['adjustments']:
                    st.markdown("**Applied Adjustments:**")
                    for i, adj in enumerate(st.session_state['adjustments'], 1):
                        st.markdown(f"{i}. {adj['command']}")

if __name__ == "__main__":
    main()

```
