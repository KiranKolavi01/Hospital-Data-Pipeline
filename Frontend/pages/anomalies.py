"""
Anomalies Page - Display detected health anomalies with color coding.
"""
import streamlit as st
import pandas as pd
from utils.helpers import get_anomaly_color, get_anomaly_icon
from styles.custom_styles import inject_styles


def inject_page_styles():
    """Styles are now handled globally in custom_styles.py"""
    pass


@st.cache_data(ttl=300)
def fetch_data(_api_client):
    """
    Fetch anomaly data from API.
    
    Args:
        _api_client: API client instance
        
    Returns:
        DataFrame with anomaly data
    """
    return _api_client.get_anomalies()


def add_anomaly_styling(data: pd.DataFrame) -> pd.DataFrame:
    """
    Add icon column to anomaly data for visual indicators.
    
    Args:
        data: DataFrame with anomaly data
        
    Returns:
        DataFrame with added icon column
    """
    if 'anomaly_type' in data.columns:
        data['icon'] = data['anomaly_type'].apply(get_anomaly_icon)
    return data


def display_content(data: pd.DataFrame):
    """
    Render anomalies data table with color coding.
    
    Args:
        data: DataFrame with anomaly data
    """
    if data.empty:
        st.success("No anomalies detected!")
        return
    
    # Add styling
    styled_data = add_anomaly_styling(data)
    
    st.divider()
    
    # KPI Row
    col1, col2 = st.columns(2)
    col1.metric("Total Anomalies", f"{len(data):,}")
    
    if 'anomaly_type' in data.columns and not data.empty:
        critical_count = len(data[data['anomaly_type'].isin(['High Heart Rate', 'Low Oxygen', 'High Blood Pressure'])])
        col2.metric("Critical Alerts", f"{critical_count:,}", delta="Requires Immediate Attention", delta_color="inverse")
    else:
        col2.metric("Critical Alerts", "0")
        
    st.divider()
    
    # Anomaly type filter
    if 'anomaly_type' in data.columns:
        anomaly_types = ['All'] + sorted(data['anomaly_type'].unique().tolist())
        st.markdown("<p style='color: #111827; font-size: 14px; margin-bottom: 4px;'>Filter by anomaly type:</p>", unsafe_allow_html=True)
        selected_type = st.selectbox(
            "Filter by anomaly type:",
            anomaly_types,
            label_visibility="collapsed"
        )
        
        if selected_type != 'All':
            styled_data = styled_data[styled_data['anomaly_type'] == selected_type]
    
    # Display dataframe
    st.dataframe(
        styled_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "icon": st.column_config.TextColumn(
                "",
                width="small"
            ),
            "patient_id": st.column_config.TextColumn(
                "Patient ID",
                help="Unique patient identifier"
            ),
            "anomaly_type": st.column_config.TextColumn(
                "Anomaly Type",
                help="Type of detected anomaly"
            ),
            "value": st.column_config.NumberColumn(
                "Value",
                help="Measured value",
                format="%.1f"
            ),
            "threshold": st.column_config.NumberColumn(
                "Threshold",
                help="Threshold value for anomaly detection",
                format="%.1f"
            ),
            "timestamp": st.column_config.TextColumn(
                "Timestamp",
                help="When the anomaly was detected"
            ),
        }
    )
    
    # Anomaly thresholds info
    st.divider()
    st.markdown("### Anomaly Detection Thresholds")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<p class="tech-label" style="font-size: 14px !important;">Heart Rate Limit</p>', unsafe_allow_html=True)
        st.markdown('<div class="status-badge" style="font-size: 14px !important; padding: 6px 14px;">  <span class="status-dot dot-error"></span>High Heart Rate</div>', unsafe_allow_html=True)
        st.markdown("<p style='color: #6B7280; font-size: 16px; margin-top: 8px; font-weight: 600;'>HR > 120 BPM</p>", unsafe_allow_html=True)
    
    with col2:
        st.markdown('<p class="tech-label" style="font-size: 14px !important;">Oxygen Limit</p>', unsafe_allow_html=True)
        st.markdown('<div class="status-badge" style="font-size: 14px !important; padding: 6px 14px;"><span class="status-dot dot-warning"></span>Low Oxygen</div>', unsafe_allow_html=True)
        st.markdown("<p style='color: #6B7280; font-size: 16px; margin-top: 8px; font-weight: 600;'>OX < 92%</p>", unsafe_allow_html=True)
    
    with col3:
        st.markdown('<p class="tech-label" style="font-size: 14px !important;">Blood Pressure Limit</p>', unsafe_allow_html=True)
        st.markdown('<div class="status-badge" style="font-size: 14px !important; padding: 6px 14px;"><span class="status-dot dot-error"></span>High BP</div>', unsafe_allow_html=True)
        st.markdown("<p style='color: #6B7280; font-size: 16px; margin-top: 8px; font-weight: 600;'>SYS > 160 OR DIA > 100</p>", unsafe_allow_html=True)
    
    # Export option
    st.divider()
    st.download_button(
        label="Download as CSV",
        data=data.to_csv(index=False).encode('utf-8'),
        file_name="anomalies.csv",
        mime="text/csv"
    )


def render():
    """Main render function for Anomalies page."""
    inject_page_styles()
    
    st.title("Anomalies")
    st.markdown(
        "Detected health anomalies requiring immediate attention."
    )
    
    st.divider()
    
    api_client = st.session_state.api_client
    
    try:
        # Fetch data with loading indicator
        with st.spinner("Loading anomaly data..."):
            data = fetch_data(api_client)
        
        # Display content
        display_content(data)
    
    except ConnectionError as e:
        st.error(f"Connection Error: {str(e)}")
        st.info("Please check if the backend API is running.")
    
    except Exception as e:
        st.error(f"Error loading anomaly data: {str(e)}")
        st.info("Please try again or contact support if the issue persists.")
