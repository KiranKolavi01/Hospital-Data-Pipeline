"""
Pipeline History Page - Display audit log of all pipeline runs with metrics and comparisons.
"""
import streamlit as st
import pandas as pd


@st.cache_data(ttl=300)
def fetch_data(_api_client):
    """
    Fetch pipeline history data from API.
    
    Args:
        _api_client: API client instance (prefixed with _ to prevent hashing)
        
    Returns:
        DataFrame with pipeline history data
    """
    return _api_client.get_pipeline_history()


def get_status_color(status: str) -> str:
    """
    Get background color for status.
    
    Args:
        status: Status string (SUCCESS, RUNNING, FAILED)
        
    Returns:
        Color code
    """
    colors = {
        "SUCCESS": "#10B981",    # green
        "RUNNING": "#F59E0B",    # amber
        "FAILED": "#EF4444",     # red
    }
    return colors.get(status, "#6B7280")


def display_content(data: pd.DataFrame):
    """
    Render pipeline history data table with summary cards and comparison.
    
    Args:
        data: DataFrame with pipeline history data
    """
    if data.empty:
        st.info("No pipeline runs recorded yet. Run the pipeline to see history.")
        return
    
    st.divider()
    
    # Summary cards at top
    col1, col2, col3, col4 = st.columns(4)
    
    total_runs = len(data)
    col1.metric("Total Pipeline Runs", f"{total_runs:,}")
    
    if total_runs > 0:
        # Most recent run is first row (already sorted by started_at DESC)
        latest_run = data.iloc[0]
        
        # Last Run Duration
        duration = latest_run.get('duration_seconds', 0)
        if pd.notna(duration) and duration != "":
            col2.metric("Last Run Duration", f"{float(duration):.1f}s")
        else:
            col2.metric("Last Run Duration", "N/A")
        
        # Last Run Anomalies
        anomalies = latest_run.get('gold_anomalies_count', 0)
        if pd.notna(anomalies) and anomalies != "":
            col3.metric("Last Run Anomalies", f"{int(anomalies):,}")
        else:
            col3.metric("Last Run Anomalies", "0")
        
        # Last Run Trends
        trends = latest_run.get('silver_trends_count', 0)
        if pd.notna(trends) and trends != "":
            col4.metric("Last Run Trends", f"{int(trends):,}")
        else:
            col4.metric("Last Run Trends", "0")
    else:
        col2.metric("Last Run Duration", "N/A")
        col3.metric("Last Run Anomalies", "N/A")
        col4.metric("Last Run Trends", "N/A")
    
    st.divider()
    
    # Run History Table
    st.subheader("Run History")
    
    # Display dataframe with custom styling
    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "run_id": st.column_config.TextColumn(
                "Run ID",
                help="Unique identifier for this pipeline run",
                width="medium"
            ),
            "started_at": st.column_config.TextColumn(
                "Started At",
                help="When the pipeline run started",
                width="medium"
            ),
            "finished_at": st.column_config.TextColumn(
                "Finished At",
                help="When the pipeline run finished",
                width="medium"
            ),
            "duration_seconds": st.column_config.NumberColumn(
                "Duration (s)",
                help="How long the pipeline took to run",
                format="%.2f"
            ),
            "bronze_ehr_count": st.column_config.NumberColumn(
                "EHR",
                help="Number of EHR records ingested",
                format="%d"
            ),
            "bronze_vitals_count": st.column_config.NumberColumn(
                "Vitals",
                help="Number of vitals records ingested",
                format="%d"
            ),
            "bronze_labs_count": st.column_config.NumberColumn(
                "Labs",
                help="Number of labs records ingested",
                format="%d"
            ),
            "silver_vitals_count": st.column_config.NumberColumn(
                "Clean Vitals",
                help="Number of cleaned vitals records",
                format="%d"
            ),
            "silver_labs_count": st.column_config.NumberColumn(
                "Clean Labs",
                help="Number of cleaned labs records",
                format="%d"
            ),
            "silver_patient_master_count": st.column_config.NumberColumn(
                "Patients",
                help="Number of patients in master table",
                format="%d"
            ),
            "silver_trends_count": st.column_config.NumberColumn(
                "Trends",
                help="Number of trend alerts detected",
                format="%d"
            ),
            "gold_anomalies_count": st.column_config.NumberColumn(
                "Anomalies",
                help="Number of anomalies detected",
                format="%d"
            ),
            "gold_risk_scores_count": st.column_config.NumberColumn(
                "Risk Scores",
                help="Number of risk scores calculated",
                format="%d"
            ),
            "status": st.column_config.TextColumn(
                "Status",
                help="Pipeline run status"
            ),
        }
    )
    
    # Run Comparison Section
    st.divider()
    st.subheader("Run Comparison")
    
    if total_runs >= 2:
        # Compare most recent run (index 0) with previous run (index 1)
        current_run = data.iloc[0]
        previous_run = data.iloc[1]
        
        # Anomaly count change
        current_anomalies = int(current_run.get('gold_anomalies_count', 0)) if pd.notna(current_run.get('gold_anomalies_count')) and current_run.get('gold_anomalies_count') != "" else 0
        prev_anomalies = int(previous_run.get('gold_anomalies_count', 0)) if pd.notna(previous_run.get('gold_anomalies_count')) and previous_run.get('gold_anomalies_count') != "" else 0
        
        # Trends count change
        current_trends = int(current_run.get('silver_trends_count', 0)) if pd.notna(current_run.get('silver_trends_count')) and current_run.get('silver_trends_count') != "" else 0
        prev_trends = int(previous_run.get('silver_trends_count', 0)) if pd.notna(previous_run.get('silver_trends_count')) and previous_run.get('silver_trends_count') != "" else 0
        
        # Duration change
        current_duration = float(current_run.get('duration_seconds', 0)) if pd.notna(current_run.get('duration_seconds')) and current_run.get('duration_seconds') != "" else 0
        prev_duration = float(previous_run.get('duration_seconds', 0)) if pd.notna(previous_run.get('duration_seconds')) and previous_run.get('duration_seconds') != "" else 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Anomalies**")
            anomaly_change = current_anomalies - prev_anomalies
            if anomaly_change < 0:
                st.markdown(f"<span style='color: #10B981;'>{prev_anomalies} → {current_anomalies} (↓ {abs(anomaly_change)})</span>", unsafe_allow_html=True)
            elif anomaly_change > 0:
                st.markdown(f"<span style='color: #EF4444;'>{prev_anomalies} → {current_anomalies} (↑ {anomaly_change})</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color: #6B7280;'>{prev_anomalies} → {current_anomalies} (no change)</span>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("**Trends**")
            trend_change = current_trends - prev_trends
            if trend_change < 0:
                st.markdown(f"<span style='color: #10B981;'>{prev_trends} → {current_trends} (↓ {abs(trend_change)})</span>", unsafe_allow_html=True)
            elif trend_change > 0:
                st.markdown(f"<span style='color: #EF4444;'>{prev_trends} → {current_trends} (↑ {trend_change})</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color: #6B7280;'>{prev_trends} → {current_trends} (no change)</span>", unsafe_allow_html=True)
        
        with col3:
            st.markdown("**Duration**")
            st.markdown(f"{prev_duration:.1f}s → {current_duration:.1f}s")
    else:
        st.info("Run at least 2 pipelines to see comparison")
    
    # Export option
    st.divider()
    st.download_button(
        label="Download as CSV",
        data=data.to_csv(index=False).encode('utf-8'),
        file_name="pipeline_history.csv",
        mime="text/csv"
    )


def render():
    """Main render function for Pipeline History page."""
    st.title("Pipeline History")
    st.markdown(
        "Audit log of all pipeline runs with detailed metrics and performance tracking."
    )
    
    st.divider()
    
    api_client = st.session_state.api_client
    
    try:
        # Fetch data with loading indicator
        with st.spinner("Loading pipeline history..."):
            data = fetch_data(api_client)
        
        # Display content
        display_content(data)
    
    except ConnectionError as e:
        st.error(f"Connection Error: {str(e)}")
        st.info("Please check if the backend API is running.")
    
    except Exception as e:
        st.error(f"Error loading pipeline history: {str(e)}")
        st.info("Please try again or contact support if the issue persists.")
