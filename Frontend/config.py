f"""
Configuration module for Hospital Data Pipeline Frontend.
Manages application settings and environment variables.
"""
import os

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Request Configuration
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

# Cache Configuration
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))

# Page Configuration
PAGE_NAMES = [
    "Run Pipeline",
    "Patient Master",
    "Anomalies",
    "Trend Alerts",
    "Alert Log",
    "Vitals",
    "Labs",
    "Visualizations",
    "Risk Leaderboard",
    "Pipeline History"
]
