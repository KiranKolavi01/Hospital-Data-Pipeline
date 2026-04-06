"""
Labs Page - Display cleaned laboratory test data.
"""
import streamlit as st
import pandas as pd


@st.cache_data(ttl=300)
def fetch_data(_api_client):
    """
    Fetch labs data from API.
    
    Args:
        _api_client: API client instance
        
    Returns:
        DataFrame with labs data
    """
    return _api_client.get_labs()


def display_content(data: pd.DataFrame):
    """
    Render labs data table.
    
    Args:
        data: DataFrame with labs data
    """
    if data.empty:
        st.warning("No lab data available")
        return
    
    st.divider()
    
    # KPI Row
    col1, col2 = st.columns(2)
    col1.metric("Total Lab Records", f"{len(data):,}")
    
    if len(data) > 0 and 'lab_test' in data.columns:
        col2.metric("Unique Test Types", str(data['lab_test'].nunique()))
    else:
        col2.metric("Unique Test Types", "0")
        
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
                help="When the lab test was performed"
            ),
            "lab_test": st.column_config.TextColumn(
                "Lab Test",
                help="Name of the laboratory test"
            ),
            "test_name": st.column_config.TextColumn(
                "Test Name",
                help="Name of the laboratory test"
            ),
            "lab_value": st.column_config.NumberColumn(
                "Lab Value",
                help="Test result value",
                format="%.2f"
            ),
            "test_value": st.column_config.NumberColumn(
                "Test Value",
                help="Test result value",
                format="%.2f"
            ),
            "value": st.column_config.NumberColumn(
                "Value",
                help="Test result value",
                format="%.2f"
            ),
            "unit": st.column_config.TextColumn(
                "Unit",
                help="Unit of measurement"
            ),
        }
    )
    
    # Export option
    st.divider()
    st.download_button(
        label="Download as CSV",
        data=data.to_csv(index=False).encode('utf-8'),
        file_name="labs.csv",
        mime="text/csv"
    )


def render():
    """Main render function for Labs page."""
    st.title("Labs")
    st.markdown(
        "Cleaned laboratory test results for all patients."
    )
    
    st.divider()
    
    api_client = st.session_state.api_client
    
    try:
        # Fetch data with loading indicator
        with st.spinner("Loading lab data..."):
            data = fetch_data(api_client)
        
        # Display content
        display_content(data)
    
    except ConnectionError as e:
        st.error(f"Connection Error: {str(e)}")
        st.info("Please check if the backend API is running.")
    
    except Exception as e:
        st.error(f"Error loading lab data: {str(e)}")
        st.info("Please try again or contact support if the issue persists.")
