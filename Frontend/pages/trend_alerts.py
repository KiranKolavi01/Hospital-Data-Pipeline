"""
Trend Alerts Page - Display deterioration alerts for patients with consistently worsening vitals.
"""
import streamlit as st
import pandas as pd


@st.cache_data(ttl=300)
def fetch_data(_api_client):
    """
    Fetch trend alerts data from API.
    
    Args:
        _api_client: API client instance (prefixed with _ to prevent hashing)
        
    Returns:
        DataFrame with trend alerts data
    """
    return _api_client.get_trend_alerts()


def get_vital_color(vital: str) -> str:
    """
    Get color for vital sign.
    
    Args:
        vital: Vital sign name (hr, ox, sys, dia)
        
    Returns:
        Color code
    """
    colors = {
        "hr": "#EF4444",      # red
        "ox": "#3B82F6",      # blue
        "sys": "#F97316",     # orange
        "dia": "#F97316",     # orange
    }
    return colors.get(vital, "#6B7280")


def display_content(data: pd.DataFrame):
    """
    Render trend alerts data table with color coding.
    
    Args:
        data: DataFrame with trend alerts data
    """
    if data.empty:
        st.success("No deterioration trends detected!")
        st.info("All patients' vitals are stable or improving.")
        return
    
    st.divider()
    
    # KPI Row - Summary cards
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Total Trends Detected", f"{len(data):,}")
    
    if 'vital' in data.columns:
        hr_count = len(data[data['vital'] == 'hr'])
        ox_count = len(data[data['vital'] == 'ox'])
        bp_count = len(data[data['vital'].isin(['sys', 'dia'])])
        
        col2.metric("HR Trends", f"{hr_count:,}")
        col3.metric("OX Trends", f"{ox_count:,}")
        col4.metric("BP Trends", f"{bp_count:,}")
    else:
        col2.metric("HR Trends", "0")
        col3.metric("OX Trends", "0")
        col4.metric("BP Trends", "0")
    
    st.divider()
    
    # Warning banner
    st.markdown(
        """
        <div style='padding: 14px 18px; background-color: #FEF3C7; border: 1px solid #F59E0B; border-radius: 6px; margin-bottom: 8px;'>
            <p style='color: #92400E; font-size: 14px; font-weight: 600; margin: 0;'>
                ⚠️ <strong>Early Warning System</strong> — These patients are not yet critical but their vitals are consistently worsening. Early intervention recommended.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.divider()
    
    # Filter options
    if 'vital' in data.columns:
        vital_types = ['All'] + sorted(data['vital'].unique().tolist())
        selected_vital = st.selectbox(
            "Filter by vital sign:",
            vital_types
        )
        
        if selected_vital != 'All':
            data = data[data['vital'] == selected_vital]
    
    # Display dataframe with custom styling
    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "patient_id": st.column_config.TextColumn(
                "Patient ID",
                help="Unique patient identifier"
            ),
            "vital": st.column_config.TextColumn(
                "Vital Sign",
                help="Which vital is trending"
            ),
            "reading_1": st.column_config.NumberColumn(
                "Reading 1",
                help="Oldest of the 3 readings",
                format="%.1f"
            ),
            "reading_2": st.column_config.NumberColumn(
                "Reading 2",
                help="Middle reading",
                format="%.1f"
            ),
            "reading_3": st.column_config.NumberColumn(
                "Reading 3",
                help="Most recent reading",
                format="%.1f"
            ),
            "direction": st.column_config.TextColumn(
                "Direction",
                help="Trend direction (RISING or FALLING)"
            ),
            "trend_label": st.column_config.TextColumn(
                "Trend Description",
                help="Human-readable trend description",
                width="large"
            ),
            "already_critical": st.column_config.CheckboxColumn(
                "Already Critical",
                help="Whether the most recent value already crosses anomaly threshold"
            ),
        }
    )
    
    # Info section at bottom
    st.divider()
    st.markdown("### How Trend Detection Works")
    st.info(
        "A deterioration alert is raised when a patient's last 3 consecutive vitals readings "
        "show a consistent worsening direction — even if the values are still within safe limits. "
        "This allows early clinical intervention before a critical threshold is crossed.\n\n"
        "**Worsening Patterns:**\n"
        "- **HR, SYS, DIA**: Each reading is strictly higher than the previous (↑↑↑)\n"
        "- **OX**: Each reading is strictly lower than the previous (↓↓↓)\n\n"
        "**Already Critical**: Indicates if the most recent reading has crossed the anomaly threshold "
        "(HR > 120, OX < 92, SYS > 160, DIA > 100)."
    )
    
    # Export option
    st.divider()
    st.download_button(
        label="Download as CSV",
        data=data.to_csv(index=False).encode('utf-8'),
        file_name="trend_alerts.csv",
        mime="text/csv"
    )


def render():
    """Main render function for Trend Alerts page."""
    st.title("Trend Alerts")
    st.markdown(
        "Early warning system for patients with consistently worsening vital signs."
    )
    
    st.divider()
    
    api_client = st.session_state.api_client
    
    try:
        # Fetch data with loading indicator
        with st.spinner("Loading trend alerts..."):
            data = fetch_data(api_client)
        
        # Display content
        display_content(data)
    
    except ConnectionError as e:
        st.error(f"Connection Error: {str(e)}")
        st.info("Please check if the backend API is running.")
    
    except Exception as e:
        st.error(f"Error loading trend alerts: {str(e)}")
        st.info("Please try again or contact support if the issue persists.")
