"""
Vitals Page - Display cleaned vitals data.
"""
import streamlit as st
import pandas as pd


@st.cache_data(ttl=300)
def fetch_data(_api_client):
    """
    Fetch vitals data from API.
    
    Args:
        _api_client: API client instance
        
    Returns:
        DataFrame with vitals data
    """
    return _api_client.get_vitals()


def display_content(data: pd.DataFrame):
    """
    Render vitals data table.
    
    Args:
        data: DataFrame with vitals data
    """
    if data.empty:
        st.warning("No vitals data available")
        return
    
    # KPI Row
    col1, col2 = st.columns(2)
    col1.metric("Total Vitals Records", f"{len(data):,}")
    
    if len(data) > 0 and 'timestamp' in data.columns:
        col2.metric("Last Recorded", str(data['timestamp'].max()))
    else:
        col2.metric("Last Recorded", "N/A")
        
    st.divider()
    
    # Display dataframe
    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "patient_id": st.column_config.TextColumn(
                "Patient ID",
                help="Unique patient identifier"
            ),
            "timestamp": st.column_config.TextColumn(
                "Timestamp",
                help="When the vitals were recorded"
            ),
            "heart_rate": st.column_config.NumberColumn(
                "Heart Rate (bpm)",
                help="Heart rate in beats per minute",
                format="%.1f"
            ),
            "hr": st.column_config.NumberColumn(
                "Heart Rate (bpm)",
                help="Heart rate in beats per minute",
                format="%.1f"
            ),
            "oxygen_level": st.column_config.NumberColumn(
                "Oxygen (%)",
                help="Blood oxygen saturation level",
                format="%.1f"
            ),
            "ox": st.column_config.NumberColumn(
                "Oxygen (%)",
                help="Blood oxygen saturation level",
                format="%.1f"
            ),
            "sys": st.column_config.NumberColumn(
                "Systolic BP",
                help="Systolic blood pressure",
                format="%.0f"
            ),
            "dia": st.column_config.NumberColumn(
                "Diastolic BP",
                help="Diastolic blood pressure",
                format="%.0f"
            ),
        }
    )
    
    # Export option
    st.download_button(
        label="Download as CSV",
        data=data.to_csv(index=False).encode('utf-8'),
        file_name="vitals.csv",
        mime="text/csv"
    )


def render():
    """Main render function for Vitals page."""
    st.title("Vitals")
    st.markdown(
        "Cleaned patient vital signs including heart rate, oxygen levels, and blood pressure."
    )
    
    api_client = st.session_state.api_client
    
    try:
        # Fetch data with loading indicator
        with st.spinner("Loading vitals data..."):
            data = fetch_data(api_client)
        
        # Display content
        display_content(data)
    
    except ConnectionError as e:
        st.error(f"Connection Error: {str(e)}")
        st.info("Please check if the backend API is running.")
    
    except Exception as e:
        st.error(f"Error loading vitals data: {str(e)}")
        st.info("Please try again or contact support if the issue persists.")
