"""
Risk Leaderboard Page - Display patient risk scores with tiered color coding.
"""
import streamlit as st
import pandas as pd

def inject_page_styles():
    """Styles are handled globally, but we can add page-specific overrides here if needed."""
    st.markdown("""
        <style>
        .risk-card {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            border: 1px solid #E5E7EB;
            margin-bottom: 1rem;
        }
        .metric-label {
            font-size: 0.8rem;
            color: #6B7280;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }
        .metric-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: #111827;
        }
        </style>
    """, unsafe_allow_html=True)

def fetch_data(_api_client):
    """Fetch risk score data from API."""
    return _api_client.get_risk_scores()

def display_summary(data: pd.DataFrame):
    """Display high-level summary metrics for risk levels."""
    if data.empty:
        return
        
    high_count = len(data[data['risk_level'] == 'HIGH'])
    med_count = len(data[data['risk_level'] == 'MEDIUM'])
    low_count = len(data[data['risk_level'] == 'LOW'])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div class="risk-card" style="border-left: 4px solid #EF4444;">
                <div class="metric-label">High Risk Patients</div>
                <div class="metric-value" style="color: #EF4444;">{high_count}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown(f"""
            <div class="risk-card" style="border-left: 4px solid #F59E0B;">
                <div class="metric-label">Medium Risk Patients</div>
                <div class="metric-value" style="color: #F59E0B;">{med_count}</div>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown(f"""
            <div class="risk-card" style="border-left: 4px solid #10B981;">
                <div class="metric-label">Low Risk Patients</div>
                <div class="metric-value" style="color: #10B981;">{low_count}</div>
            </div>
        """, unsafe_allow_html=True)

def style_risk_table(df: pd.DataFrame):
    """Apply color coding to the risk level column."""
    def color_risk(val):
        if val == 'HIGH':
            return 'background-color: #FEE2E2; color: #991B1B; font-weight: bold;'
        elif val == 'MEDIUM':
            return 'background-color: #FEF3C7; color: #92400E; font-weight: bold;'
        elif val == 'LOW':
            return 'background-color: #D1FAE5; color: #065F46; font-weight: bold;'
        return ''

    return df.style.applymap(color_risk, subset=['risk_level'])

def render():
    """Render the Risk Leaderboard page."""
    inject_page_styles()
    
    st.markdown("<h1>Risk Leaderboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6B7280; margin-bottom: 2rem;'>Composite clinical risk scoring based on anomaly frequency, severity, and recency.</p>", unsafe_allow_html=True)
    
    api_client = st.session_state.get('api_client')
    if not api_client:
        st.error("API Client not initialized.")
        return

    with st.spinner("Fetching patient risk data..."):
        try:
            data = fetch_data(api_client)
            
            if data.empty:
                st.info("No risk score data available. Please run the pipeline first.")
                return
                
            # Summary Metrics
            display_summary(data)
            
            st.markdown("<h3>Patient Risk Rankings</h3>", unsafe_allow_html=True)
            
            # Interactive Table
            # Sort by score descending is already handled by backend, but we'll ensure it here
            data = data.sort_values(by='risk_score', ascending=False)
            
            styled_df = style_risk_table(data)
            st.dataframe(
                styled_df,
                use_container_width=True,
                column_config={
                    "patient_id": "Patient ID",
                    "risk_score": st.column_config.NumberColumn("Risk Score", format="%.1f"),
                    "risk_level": "Risk Level",
                    "anomaly_count": "Total Anomalies",
                    "last_anomaly_timestamp": "Last Observed Anomaly"
                },
                hide_index=True
            )
            
        except Exception as e:
            st.error(f"Error loading risk leaderboard: {str(e)}")
