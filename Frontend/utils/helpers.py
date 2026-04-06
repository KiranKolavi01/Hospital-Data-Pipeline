"""
Utility functions for Hospital Data Pipeline Frontend.
"""
from datetime import datetime
from typing import Optional
import re


def format_timestamp(ts: str) -> str:
    """
    Format timestamp string for display.
    
    Args:
        ts: Timestamp string (ISO format or Unix timestamp)
        
    Returns:
        Formatted timestamp string (e.g., "2024-03-27 14:30:00")
    """
    try:
        # Try parsing as ISO format
        dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        try:
            # Try parsing as Unix timestamp
            dt = datetime.fromtimestamp(float(ts))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            # Return original if parsing fails
            return str(ts)


def format_number(num: float, decimals: int = 2) -> str:
    """
    Format number with proper precision.
    
    Args:
        num: Number to format
        decimals: Number of decimal places
        
    Returns:
        Formatted number string
    """
    try:
        return f"{float(num):.{decimals}f}"
    except (ValueError, TypeError):
        return str(num)


def validate_api_url(url: str) -> bool:
    """
    Validate API URL format.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if URL is valid, False otherwise
    """
    # Basic URL validation pattern
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP address
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url))


def truncate_text(text: str, max_length: int = 50) -> str:
    """
    Truncate text to maximum length with ellipsis.
    
    Args:
        text: Text to truncate
        max_length: Maximum length before truncation
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def get_anomaly_color(anomaly_type: str) -> str:
    """
    Get color code for anomaly type.
    
    Args:
        anomaly_type: Type of anomaly
        
    Returns:
        Hex color code
    """
    color_map = {
        'High Heart Rate': '#e00',
        'Low Oxygen': '#f5a623',
        'High Blood Pressure': '#e00',
    }
    return color_map.get(anomaly_type, '#666666')


def get_anomaly_icon(anomaly_type: str) -> str:
    """
    Get icon/emoji for anomaly type.
    
    Args:
        anomaly_type: Type of anomaly
        
    Returns:
        Icon/emoji string
    """
    icon_map = {
        'High Heart Rate': '',
        'Low Oxygen': '',
        'High Blood Pressure': '',
    }
    return icon_map.get(anomaly_type, '')
