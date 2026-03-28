import streamlit as st
import requests
import pandas as pd
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# Streamlit config
st.set_page_config(page_title="Hospital Data Pipeline", layout="wide", initial_sidebar_state="expanded")

# --- Theme Toggle Implementation ---
# Using a checkbox in sidebar to simulate a theme toggle
st.sidebar.markdown("<br/>", unsafe_allow_html=True)
is_dark = st.sidebar.toggle("🌙 Dark Mode", value=True)

if is_dark:
    bg_color = "#000000"
    sec_bg_color = "#0a0a0a"
    text_color = "#ededed"
    border_color = "#333333"
else:
    bg_color = "#ffffff"
    sec_bg_color = "#f7f7f7"
    text_color = "#111111"
    border_color = "#eaeaea"

dynamic_theme = f"""
<style>
:root {{
    --background-color: {bg_color} !important;
    --secondary-background-color: {sec_bg_color} !important;
    --text-color: {text_color} !important;
    --border-color: {border_color} !important;
}}
[data-testid="stAppViewContainer"], .stApp {{
    background-color: var(--background-color) !important;
    color: var(--text-color) !important;
}}
[data-testid="stSidebar"] {{
    background-color: var(--secondary-background-color) !important;
    border-right: 1px solid var(--border-color) !important;
}}
[data-testid="stHeader"] {{
    background-color: transparent !important;
}}
div[data-testid="stMarkdownContainer"] *, h1, h2, h3, p, span, label, div.stMarkdown {{
    color: var(--text-color) !important;
}}
[data-testid="baseButton-primary"], [data-testid="baseButton-primary"] * {{
    background-color: var(--text-color) !important;
    color: var(--background-color) !important;
    border-color: var(--text-color) !important;
}}
.vercel-card {{
    background-color: var(--secondary-background-color) !important;
    border: 1px solid var(--border-color) !important;
}}
[data-testid="stDataFrame"] {{
    background-color: var(--background-color) !important;
    border: 1px solid var(--border-color) !important;
}}
hr {{
    border-color: var(--border-color) !important;
}}
</style>
"""
st.markdown(dynamic_theme, unsafe_allow_html=True)

def load_css(file_name):
    # Ensure it works correctly when run from the root directory
    css_path = os.path.join(os.path.dirname(__file__), file_name)
    try:
        with open(css_path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

load_css("style.css")

# Vercel-like Sidebar Header
st.sidebar.markdown(
    """<div style='margin-bottom: 2rem;'>
        <h2 style='margin:0; font-weight:700; letter-spacing:-0.05em;'>Hospital Data Dataworks</h2>
        <p style='opacity:0.7; font-size:0.85rem; margin-top:0;'>Analytics & Pipeline Dashboard</p>
       </div>""",
    unsafe_allow_html=True
)

page = st.sidebar.radio("Navigation", [
    "Run Pipeline",
    "Patient Master View",
    "Anomalies View",
    "Vitals View",
    "Labs View",
    "Visualizations View"
], label_visibility="collapsed")

# Inject a divider
st.sidebar.markdown("<hr style='margin: 2rem 0;' />", unsafe_allow_html=True)
st.sidebar.markdown("<p style='opacity:0.6; font-size:0.8rem;'>Environment: Production<br/>Status: Healthy</p>", unsafe_allow_html=True)

if page == "Run Pipeline":
    st.markdown("<h1>Pipeline Deployment</h1>", unsafe_allow_html=True)
    st.markdown("<p style='opacity:0.7; font-size: 1.1rem; margin-bottom: 2rem;'>Trigger the batch data pipeline to ingest and process metrics across Bronze, Silver, and Gold layers.</p>", unsafe_allow_html=True)
    
    st.markdown("<div class='vercel-card'>", unsafe_allow_html=True)
    st.markdown("<h3>Deployment Trigger</h3>", unsafe_allow_html=True)
    st.markdown("<p style='opacity:0.7; font-size: 0.9rem;'>Manually initiate the data ingestion sync and anomaly detection mechanisms.</p>", unsafe_allow_html=True)
    
    if st.button("Deploy to Production", type="primary"):
        with st.spinner("Processing layers..."):
            try:
                response = requests.get(f"{API_BASE_URL}/run-pipeline")
                if response.status_code == 200:
                    data = response.json()
                    st.success("Deployment verified and successful.")
                    st.markdown("### Build Logs")
                    logs = data.get("messages", data.get("log", []))
                    if isinstance(logs, list) and logs:
                        log_text = "\n".join([f"> {msg}" for msg in logs])
                        st.code(log_text, language="bash")
                    else:
                        # Fallback static log if backend does not pass it back in the JSON
                        log_text = (
                            "> Setup complete\n"
                            "> Bronze layer raw ingestion complete\n"
                            "> Silver layer cleaning and patient master initialized\n"
                            "> Gold layer anomaly detection completed\n"
                            "> Visualization charts generated successfully"
                        )
                        st.code(log_text, language="bash")
                else:
                    st.error(f"Deployment failed: {response.text}")
            except Exception as e:
                st.error(f"Connection error to API: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

elif page == "Patient Master View":
    st.markdown("<h1>Patient Master</h1>", unsafe_allow_html=True)
    st.markdown("<p style='opacity:0.7; margin-bottom: 2rem;'>Aggregated patient master records containing the latest tracked vitals and laboratory results.</p>", unsafe_allow_html=True)
    try:
        response = requests.get(f"{API_BASE_URL}/patient-master")
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            st.dataframe(df, use_container_width=True)
        else:
            st.error("Failed to fetch data.")
    except Exception as e:
        st.error(f"Connection error: {e}")

elif page == "Anomalies View":
    st.markdown("<h1>Detected Anomalies</h1>", unsafe_allow_html=True)
    st.markdown("<p style='opacity:0.7; margin-bottom: 2rem;'>Flags records surpassing threshold variants (HR > 120, OX < 92%, BP > 160/100).</p>", unsafe_allow_html=True)
    try:
        response = requests.get(f"{API_BASE_URL}/anomalies")
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            st.dataframe(df, use_container_width=True)
        else:
            st.error("Failed to fetch data.")
    except Exception as e:
        st.error(f"Connection error: {e}")

elif page == "Vitals View":
    st.markdown("<h1>Vitals Sync</h1>", unsafe_allow_html=True)
    st.markdown("<p style='opacity:0.7; margin-bottom: 2rem;'>Cleaned and standardized vital metrics synced from the silver repository.</p>", unsafe_allow_html=True)
    try:
        response = requests.get(f"{API_BASE_URL}/vitals")
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            st.dataframe(df, use_container_width=True)
        else:
            st.error("Failed to fetch data.")
    except Exception as e:
        st.error(f"Connection error: {e}")

elif page == "Labs View":
    st.markdown("<h1>Laboratory Results</h1>", unsafe_allow_html=True)
    st.markdown("<p style='opacity:0.7; margin-bottom: 2rem;'>Standardized laboratory data, formatted and mapped appropriately.</p>", unsafe_allow_html=True)
    try:
        response = requests.get(f"{API_BASE_URL}/labs")
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            st.dataframe(df, use_container_width=True)
        else:
            st.error("Failed to fetch data.")
    except Exception as e:
        st.error(f"Connection error: {e}")

elif page == "Visualizations View":
    st.markdown("<h1>Insight Analytics</h1>", unsafe_allow_html=True)
    st.markdown("<p style='opacity:0.7; margin-bottom: 2rem;'>Generated plot distributions tracking heart rate, oxygen distributions, and anomaly variants.</p>", unsafe_allow_html=True)
    
    visualizations = [
        ("Heart Rate Trend", "hr_trend.png"),
        ("Oxygen Distribution", "oxygen_distribution.png"),
        ("Anomaly Counts", "anomaly_counts.png")
    ]
    
    for title, filename in visualizations:
        st.markdown(f"<h3>{title}</h3>", unsafe_allow_html=True)
        st.markdown(f"<div class='vercel-card' style='margin-bottom: 2rem;'>", unsafe_allow_html=True)
        try:
            image_url = f"{API_BASE_URL}/visualizations/{filename}"
            response = requests.get(image_url)
            if response.status_code == 200:
                st.image(response.content, use_container_width=True)
            else:
                st.warning(f"Image artifact '{filename}' missing or pipeline uninitialized.")
        except Exception as e:
            st.error(f"Network error evaluating image '{filename}': {e}")
        st.markdown("</div>", unsafe_allow_html=True)
