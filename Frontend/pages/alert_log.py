"""
Alert Log Page - Display real-time anomaly alerts with webhook integration.
"""
import streamlit as st
import pandas as pd
import time


@st.cache_data(ttl=30)
def fetch_alert_log(_api_client):
    """
    Fetch alert log data from API.
    
    Args:
        _api_client: API client instance (prefixed with _ to prevent hashing)
        
    Returns:
        DataFrame with alert log data
    """
    return _api_client.get_alert_log()


@st.cache_data(ttl=30)
def fetch_new_alerts_count(_api_client):
    """
    Fetch new alerts count from API.
    
    Args:
        _api_client: API client instance
        
    Returns:
        Dictionary with count and run_id
    """
    return _api_client.get_new_alerts_count()


def get_anomaly_color(anomaly_type: str) -> str:
    """
    Get background color for anomaly type.
    
    Args:
        anomaly_type: Anomaly type string
        
    Returns:
        Color code
    """
    colors = {
        "High Heart Rate": "#EF4444",      # red
        "Low Oxygen": "#3B82F6",           # blue
        "High Blood Pressure": "#F97316",  # orange
    }
    return colors.get(anomaly_type, "#6B7280")


def display_content(data: pd.DataFrame, new_alerts_info: dict):
    """
    Render alert log data with summary cards and webhook integration.
    
    Args:
        data: DataFrame with alert log data
        new_alerts_info: Dictionary with new alerts count and run_id
    """
    # Live alert banner at top
    new_count = new_alerts_info.get("count", 0)
    
    if new_count > 0:
        st.error(f"⚠️ **{new_count} new anomalies detected in the last pipeline run.** Immediate review recommended.")
    else:
        st.markdown(
            '<div style="background-color: #064e3b; color: #34d399; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">'
            '✓ No new anomalies detected in the last pipeline run.'
            '</div>', 
            unsafe_allow_html=True
        )
    
    st.divider()
    
    # Summary cards
    col1, col2, col3, col4 = st.columns(4)
    
    total_alerts = len(data)
    col1.metric("Total Alerts Ever Logged", f"{total_alerts:,}")
    col2.metric("New Alerts This Run", f"{new_count:,}")
    
    if not data.empty:
        # Most affected patient
        patient_counts = data['patient_id'].value_counts()
        most_affected = patient_counts.index[0] if len(patient_counts) > 0 else "N/A"
        col3.metric("Most Affected Patient", most_affected)
        
        # Most common anomaly type
        anomaly_counts = data['anomaly_type'].value_counts()
        most_common = anomaly_counts.index[0] if len(anomaly_counts) > 0 else "N/A"
        col4.metric("Most Common Anomaly", most_common)
    else:
        col3.metric("Most Affected Patient", "N/A")
        col4.metric("Most Common Anomaly", "N/A")
    
    st.divider()
    
    if data.empty:
        st.info("No alerts logged yet. Run the pipeline to generate alerts.")
        return
    
    # Alert Log Table
    st.subheader("Alert Log")
    
    # Display dataframe with custom styling
    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "alert_id": st.column_config.TextColumn(
                "Alert ID",
                help="Unique identifier for this alert",
                width="medium"
            ),
            "patient_id": st.column_config.TextColumn(
                "Patient ID",
                help="Patient identifier"
            ),
            "anomaly_type": st.column_config.TextColumn(
                "Anomaly Type",
                help="Type of anomaly detected"
            ),
            "value": st.column_config.TextColumn(
                "Value",
                help="Measured value"
            ),
            "timestamp": st.column_config.TextColumn(
                "Timestamp",
                help="When the anomaly occurred"
            ),
            "detected_at": st.column_config.TextColumn(
                "Detected At",
                help="When the alert was logged"
            ),
            "run_id": st.column_config.TextColumn(
                "Run ID",
                help="Pipeline run that detected this alert",
                width="medium"
            ),
        }
    )
    
    # Webhook Section
    st.divider()
    st.subheader("Webhook Integration")
    st.markdown(
        "Subscribe an external URL to receive POST notifications whenever new anomalies are detected."
    )
    
    webhook_url = st.text_input(
        "Webhook URL",
        placeholder="https://your-service.com/webhook",
        help="Enter the URL that should receive alert notifications"
    )
    
    if st.button("Subscribe", type="primary"):
        if webhook_url:
            try:
                api_client = st.session_state.api_client
                result = api_client.subscribe_webhook(webhook_url)
                st.success(f"✓ Subscribed successfully: {result.get('url')}")
            except Exception as e:
                st.error(f"Subscription failed: {str(e)}")
        else:
            st.warning("Please enter a webhook URL")
    
    # Export option
    st.divider()
    st.download_button(
        label="Download as CSV",
        data=data.to_csv(index=False).encode('utf-8'),
        file_name="alert_log.csv",
        mime="text/csv"
    )


def render():
    """Main render function for Alert Log page."""
    st.title("Alert Log")
    st.markdown(
        "Real-time anomaly alert system with webhook notifications. "
        "**Auto-refreshing every 30 seconds**"
    )
    
    st.divider()
    
    api_client = st.session_state.api_client
    
    try:
        # Fetch data with loading indicator
        with st.spinner("Loading alert log..."):
            data = fetch_alert_log(api_client)
            new_alerts_info = fetch_new_alerts_count(api_client)
        
        # Display content
        display_content(data, new_alerts_info)
        
        # Auto-refresh every 30 seconds
        time.sleep(30)
        st.rerun()
    
    except ConnectionError as e:
        st.error(f"Connection Error: {str(e)}")
        st.info("Please check if the backend API is running.")
    
    except Exception as e:
        st.error(f"Error loading alert log: {str(e)}")
        st.info("Please try again or contact support if the issue persists.")
