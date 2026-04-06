"""
Hospital Data Pipeline Frontend - Main Application
A Streamlit-based web application for healthcare data visualization and pipeline management.
"""
import streamlit as st
from api.client import HospitalAPIClient
from styles.custom_styles import apply_all_styles
import config

# Import page modules
from pages import run_pipeline, patient_master, anomalies, trend_alerts, alert_log, vitals, labs, visualizations, risk_leaderboard, pipeline_history


def configure_page():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="Hospital Data Pipeline",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def inject_global_styles():
    """Apply custom CSS to entire application."""
    apply_all_styles()


def initialize_session_state():
    """Initialize session state variables."""
    if 'api_client' not in st.session_state:
        st.session_state.api_client = HospitalAPIClient(
            base_url=config.API_BASE_URL,
            timeout=config.REQUEST_TIMEOUT
        )
    
    # Step 1 — Read page from query params first, then fallback to default
    params = st.query_params
    if "page" in params:
        st.session_state.current_page = params["page"]
    elif 'current_page' not in st.session_state:
        st.session_state.current_page = config.PAGE_NAMES[0]
    
    if 'pipeline_running' not in st.session_state:
        st.session_state.pipeline_running = False
    
    if 'pipeline_logs' not in st.session_state:
        st.session_state.pipeline_logs = []


@st.cache_data(ttl=60)
def _check_api_connection():
    """Cached API connection check."""
    return st.session_state.api_client.check_connection()


def validate_api_connection():
    """Validate API connection on startup."""
    if not _check_api_connection():
        st.error(
            f"Unable to connect to Backend API at `{config.API_BASE_URL}`. "
            "Please ensure the backend server is running."
        )
        st.info(
            "Tip: You can configure the API URL by setting the "
            "`API_BASE_URL` environment variable."
        )
        return False
    return True


def navigate_to(page_name):
    """
    Navigate to a page and persist in URL query params.
    
    Args:
        page_name: Name of the page to navigate to
    """
    st.session_state.current_page = page_name
    st.query_params["page"] = page_name


def on_nav_change():
    """Callback for navigation menu changes."""
    navigate_to(st.session_state.nav_radio)


def render_navigation():
    """Display navigation menu in sidebar."""
    # Live alert banner at top of sidebar
    try:
        api_client = st.session_state.api_client
        new_alerts_info = api_client.get_new_alerts_count()
        new_count = new_alerts_info.get("count", 0)
        
        if new_count > 0:
            st.sidebar.markdown(
                f"""
                <div style='padding: 10px; background-color: #FEE2E2; border: 2px solid #EF4444; border-radius: 5px; margin-bottom: 15px;'>
                    <p style='color: #991B1B; font-weight: bold; margin: 0; font-size: 14px;'>
                        ⚠️ {new_count} NEW CRITICAL ALERTS
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.sidebar.markdown(
                """
                <div style='padding: 10px; background-color: #D1FAE5; border: 2px solid #10B981; border-radius: 5px; margin-bottom: 15px;'>
                    <p style='color: #065F46; font-weight: bold; margin: 0; font-size: 14px;'>
                        ✓ No new alerts
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
    except Exception:
        # Silently fail if API is not available
        pass
    
    st.sidebar.markdown('<p class="tech-label">Platform</p>', unsafe_allow_html=True)
    st.sidebar.markdown('<p class="brand-font">Hospital Data</p>', unsafe_allow_html=True)
    st.sidebar.markdown('<p class="tech-label" style="margin-top: -5px;">Pipeline Dashboard</p>', unsafe_allow_html=True)
    st.sidebar.divider()
    
    # Navigation menu
    if 'nav_radio' not in st.session_state:
        # Find the label that contains the current_page name
        initial_index = 0
        for i, name in enumerate(config.PAGE_NAMES):
            if st.session_state.current_page in name:
                initial_index = i
                break
        st.session_state.nav_radio = config.PAGE_NAMES[initial_index]

    selected_page = st.sidebar.radio(
        "Navigation",
        config.PAGE_NAMES,
        key="nav_radio",
        on_change=on_nav_change,
        label_visibility="collapsed"
    )
    
    st.sidebar.divider()
    st.sidebar.markdown(
        f"""
        <div style='font-size: 11px; color: #999; letter-spacing: 0.05em;'>
            <p><strong>API ENDPOINT</strong><br/>{config.API_BASE_URL}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    return selected_page


def route_to_page(page_name: str):
    """
    Load selected page component.
    
    Args:
        page_name: Name of the page to load (includes number)
    """
    # Use page_name directly since we removed numeric prefixes
    clean_name = page_name
    
    page_map = {
        "Run Pipeline": run_pipeline,
        "Patient Master": patient_master,
        "Anomalies": anomalies,
        "Trend Alerts": trend_alerts,
        "Alert Log": alert_log,
        "Vitals": vitals,
        "Labs": labs,
        "Visualizations": visualizations,
        "Risk Leaderboard": risk_leaderboard,
        "Pipeline History": pipeline_history,
    }
    
    page_module = page_map.get(clean_name)
    
    if page_module:
        page_module.render()
    else:
        st.error(f"Page '{clean_name}' not found")


def main():
    """Main application entry point."""
    # Configure page
    configure_page()
    
    # Apply global styles
    inject_global_styles()
    
    # Initialize session state
    initialize_session_state()
    
    # Validate API connection
    if not validate_api_connection():
        st.stop()
    
    # Render navigation and get selected page
    selected_page = render_navigation()
    
    # Route to selected page
    route_to_page(selected_page)


if __name__ == "__main__":
    main()
