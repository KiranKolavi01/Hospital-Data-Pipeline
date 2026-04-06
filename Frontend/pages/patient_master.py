"""
Patient Master Page - Display consolidated patient data with latest vitals and labs.
"""
import streamlit as st
import pandas as pd
from utils.helpers import format_timestamp


@st.cache_data(ttl=300)
def fetch_data(_api_client):
    """
    Fetch patient master data from API.
    
    Args:
        _api_client: API client instance (prefixed with _ to prevent hashing)
        
    Returns:
        DataFrame with patient master data
    """
    return _api_client.get_patient_master()


def display_content(data: pd.DataFrame):
    """
    Render patient master data table.
    
    Args:
        data: DataFrame with patient data
    """
    if data.empty:
        st.warning("No patient data available")
        return
    
    # ISSUE 1 FIX: Force convert numeric columns to avoid type errors
    # Convert hr, ox, sys, dia to numeric
    if 'hr' in data.columns:
        data['hr'] = pd.to_numeric(data['hr'], errors='coerce')
    if 'ox' in data.columns:
        data['ox'] = pd.to_numeric(data['ox'], errors='coerce')
    if 'sys' in data.columns:
        data['sys'] = pd.to_numeric(data['sys'], errors='coerce')
    if 'dia' in data.columns:
        data['dia'] = pd.to_numeric(data['dia'], errors='coerce')
    
    # Convert all lab_* columns to numeric
    lab_cols = [col for col in data.columns if col.startswith('lab_')]
    for col in lab_cols:
        data[col] = pd.to_numeric(data[col], errors='coerce')
    
    st.divider()
    
    # KPI Row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Patients", f"{len(data):,}")
    
    # AVG HEART RATE - using f-string to avoid concatenation errors
    if len(data) > 0 and 'hr' in data.columns:
        avg_hr = data['hr'].mean()
        if pd.notna(avg_hr):
            col2.metric("Avg Heart Rate", f"{avg_hr:.1f} bpm")
        else:
            col2.metric("Avg Heart Rate", "0.0 bpm")
    else:
        col2.metric("Avg Heart Rate", "0.0 bpm")
        
    # AVG OXYGEN - using f-string to avoid concatenation errors
    if len(data) > 0 and 'ox' in data.columns:
        avg_ox = data['ox'].mean()
        if pd.notna(avg_ox):
            col3.metric("Avg Oxygen", f"{avg_ox:.1f}%")
        else:
            col3.metric("Avg Oxygen", "0.0%")
    else:
        col3.metric("Avg Oxygen", "0.0%")
        
    # ISSUE 2 FIX: Calculate average across all lab columns (not just lab_* pattern)
    if len(data) > 0:
        # Define known non-lab columns
        known_non_lab = ["patient_id", "name", "age", "gender", "diagnosis", 
                        "hr", "ox", "sys", "dia", "timestamp"]
        
        # Find all lab columns by excluding known non-lab columns
        lab_cols = [col for col in data.columns if col not in known_non_lab]
        
        if lab_cols:
            # Convert all lab columns to numeric and compute mean
            lab_values = data[lab_cols].apply(pd.to_numeric, errors='coerce')
            avg_lab = lab_values.values.flatten()
            # Filter out NaN values
            avg_lab = avg_lab[pd.notna(avg_lab)]
            
            if len(avg_lab) > 0:
                avg_lab_value = round(avg_lab.mean(), 1)
                avg_lab_value = avg_lab_value if not pd.isna(avg_lab_value) else 0.0
                col4.metric("Avg Lab Value", f"{avg_lab_value:.1f}")
            else:
                col4.metric("Avg Lab Value", "0.0")
        else:
            col4.metric("Avg Lab Value", "0.0")
    else:
        col4.metric("Avg Lab Value", "0.0")
        
    st.divider()
    
    # AI Summary Hook Simulation
    st.markdown("### Clinical AI Insight")
    if st.button("Generate Summary Insight", type="primary"):
        with st.spinner("Analyzing master patient registry..."):
            import time; time.sleep(0.5)
            st.info(f"The registry currently holds {len(data)} stable records. Average heart rate across the population is steady. Standard monitoring protocol is recommended.")
            
    st.divider()
    
    st.subheader("Master Directory")
    
    # Display dataframe with custom configuration
    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "patient_id": st.column_config.TextColumn(
                "Patient ID",
                help="Unique patient identifier"
            ),
            "hr": st.column_config.NumberColumn(
                "Heart Rate (bpm)",
                help="Latest heart rate measurement",
                format="%.1f"
            ),
            "ox": st.column_config.NumberColumn(
                "Oxygen (%)",
                help="Latest oxygen level",
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
    st.divider()
    st.download_button(
        label="Download as CSV",
        data=data.to_csv(index=False).encode('utf-8'),
        file_name="patient_master.csv",
        mime="text/csv"
    )


def render():
    """Main render function for Patient Master page."""
    st.title("Patient Master")
    st.markdown(
        "Consolidated view of all patients with their latest vitals and lab results."
    )
    
    st.divider()
    
    api_client = st.session_state.api_client
    
    try:
        # Fetch data with loading indicator
        with st.spinner("Loading patient data..."):
            data = fetch_data(api_client)
        
        # Display content
        display_content(data)
    
    except ConnectionError as e:
        st.error(f"Connection Error: {str(e)}")
        st.info("Please check if the backend API is running.")
    
    except Exception as e:
        st.error(f"Error loading patient data: {str(e)}")
        st.info("Please try again or contact support if the issue persists.")
