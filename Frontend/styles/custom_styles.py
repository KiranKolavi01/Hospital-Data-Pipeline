"""
Custom styling module for Hospital Data Pipeline Frontend.
Provides the new dark-themed SaaS aesthetic based on the Frguide blueprint.
"""
import streamlit as st

def get_blueprint_styles() -> str:
    """
    Returns the complete Frguide standard dark theme CSS.
    """
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Michroma&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700;800&display=swap');
    
    /* Main body background and technical grid */
    .stApp { 
        background-color: #F8F9FB; 
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
        color: #111827;
        background-image: 
            linear-gradient(#E5E7EB 1px, transparent 1px),
            linear-gradient(90deg, #E5E7EB 1px, transparent 1px);
        background-size: 40px 40px;
        background-position: center;
    }
    
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100%; height: 100%;
        background: radial-gradient(circle at 100% 0%, rgba(255, 255, 255, 0.9) 0%, rgba(248, 249, 251, 0.8) 100%);
        z-index: -1;
    }
    
    /* Headers - Clean Infrastructure Feel */
    h1, h2, h3 { 
        font-family: 'Montserrat', sans-serif !important;
        color: #111827 !important; 
        font-weight: 600 !important; 
        letter-spacing: 0.02em !important; 
        line-height: 1.2 !important;
        text-transform: none !important;
    }
    
    /* Branding Font - Michroma (Geometric/Square) */
    .brand-font {
        font-family: 'Michroma', sans-serif !important;
        text-transform: uppercase !important;
        letter-spacing: -0.02em !important;
        color: #000000 !important;
        font-size: 20px !important;
        margin-bottom: 0 !important;
    }
    
    /* Technical Status Labels (Render Style) */
    .tech-label {
        font-size: 14px !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.15em !important;
        color: #6B7280 !important;
        margin-bottom: 4px !important;
    }
    
    /* Sidebar matching the light tech theme */
    [data-testid="stSidebar"] { 
        background-color: #FFFFFF !important; 
        border-right: 1px solid #E5E7EB !important; 
        padding-top: 1rem;
    }
    
    /* Hide native Streamlit page links */
    [data-testid="stSidebarNav"] { display: none !important; }
    
    /* Metrics - Infrastructure Overview Style */
    [data-testid="stMetricValue"] { 
        color: #000000 !important; 
        font-weight: 800; 
        font-size: 2.2rem !important;
        letter-spacing: -0.03em;
    }
    [data-testid="stMetricLabel"] { 
        color: #6B7280 !important; 
        font-weight: 800; 
        font-size: 0.65rem; 
        text-transform: uppercase; 
        letter-spacing: 0.12em; 
    }
    [data-testid="stMetric"] { 
        background-color: #FFFFFF; 
        padding: 24px !important; 
        border-radius: 6px; 
        border: 1px solid #E5E7EB;
        box-shadow: none;
        transition: border-color 0.2s;
    }
    [data-testid="stMetric"]:hover { border-color: #34ACED; }
    
    /* Navigation Radio Items Styling - Sleek Sidebar */
    div[data-testid="stRadio"] { padding: 0 !important; }
    div[data-testid="stRadio"] [role="radiogroup"] { gap: 0.2rem !important; }

    div[data-testid="stRadio"] label {
        padding: 8px 12px !important;
        margin-bottom: 2px !important;
        cursor: pointer !important;
        border-radius: 4px !important;
        border: 1px solid transparent !important;
        background-color: transparent !important;
    }
    
    div[data-testid="stRadio"] label:hover {
        background-color: #F8F9FB !important;
    }
    
    /* Hide radio dots (robust across Streamlit versions) */
    div[role="radiogroup"] > label > div:first-child,
    div[data-testid="stRadio"] label div[data-baseweb="radio"],
    .stRadio [role="radio"] > div:first-child,
    .stRadio div[role="radiogroup"] label > div:first-child {
        display: none !important;
        opacity: 0 !important;
        width: 0px !important;
        height: 0px !important;
        overflow: hidden !important;
    }
    
    /* Sidebar Link Text */
    div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p {
        color: #4B5563 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        letter-spacing: -0.01em !important;
    }
    
    /* Selected Item styling (Render Active State) */
    div[data-testid="stRadio"] label[data-checked="true"] {
        background-color: #F0F9FF !important;
        border: 1px solid #BAE6FD !important;
    }
    div[data-testid="stRadio"] label[data-checked="true"] div[data-testid="stMarkdownContainer"] p {
        color: #34ACED !important;
        font-weight: 800 !important;
    }
    
    /* Clean Dividers */
    hr { border-bottom: 1px solid #E5E7EB !important; opacity: 1; margin: 2rem 0 !important; }
    
    /* DataFrames / Tables - Sharp and Professional */
    [data-testid="stDataFrame"] { 
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB; 
        border-radius: 4px; 
        padding: 0;
    }
    
    /* Button - Sharp Technical Style (Render) */
    .stButton > button, .stDownloadButton > button, div[data-testid="stDownloadButton"] > button {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 4px !important; 
        font-weight: 700 !important;
        font-size: 13px !important;
        padding: 0.75rem 1.5rem !important;
        text-transform: none !important;
        letter-spacing: -0.01em !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button *, .stDownloadButton > button *, div[data-testid="stDownloadButton"] > button * {
        color: #FFFFFF !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover, div[data-testid="stDownloadButton"] > button:hover {
        background-color: #34ACED !important;
        transform: translateY(-1px);
    }
    .stButton > button:active, .stDownloadButton > button:active, div[data-testid="stDownloadButton"] > button:active { transform: translateY(0); }

    /* Minimalist Badges (Indicator Style) */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: 100px;
        font-size: 10px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        background-color: #F3F4F6;
        border: 1px solid #E5E7EB;
        color: #4B5563;
    }
    .status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        margin-right: 6px;
    }
    .dot-success { background-color: #10B981; box-shadow: 0 0 8px rgba(16, 185, 129, 0.4); }
    .dot-error { background-color: #EF4444; box-shadow: 0 0 8px rgba(239, 68, 68, 0.4); }
    .dot-warning { background-color: #F59E0B; box-shadow: 0 0 8px rgba(245, 158, 11, 0.4); }
    
    /* Visualization Cards - Sharp & Grid Matched */
    .viz-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        padding: 24px;
        margin-bottom: 24px;
    }
    </style>
    """

def inject_styles(css_string: str) -> None:
    """Helper function to inject CSS"""
    st.markdown(css_string, unsafe_allow_html=True)

def apply_all_styles() -> None:
    """Convenience function to apply all custom styles at once."""
    inject_styles(get_blueprint_styles())
