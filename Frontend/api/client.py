"""
API Client module for Hospital Data Pipeline Frontend.
Handles all communication with the Backend API.
"""
import requests
import pandas as pd
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HospitalAPIClient:
    """
    Client for interacting with the Hospital Data Pipeline Backend API.
    """
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the Backend API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, endpoint: str, method: str = 'GET') -> Optional[requests.Response]:
        """
        Internal method to make HTTP requests.
        
        Args:
            endpoint: API endpoint (e.g., '/patient-master')
            method: HTTP method (GET, POST, etc.)
            
        Returns:
            Response object or None if request failed
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.info(f"Making {method} request to {url}")
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise ConnectionError(f"Failed to connect to API at {url}. Is the backend running?")
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout: {e}")
            raise TimeoutError(f"Request to {url} timed out after {self.timeout} seconds")
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            self._handle_error(response)
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise Exception(f"Unexpected error occurred: {str(e)}")
    
    def _handle_error(self, response: requests.Response) -> None:
        """
        Internal method to handle HTTP errors.
        
        Args:
            response: Response object with error status
        """
        status_code = response.status_code
        
        if status_code == 400:
            raise ValueError(f"Bad request: {response.text}")
        elif status_code == 404:
            raise FileNotFoundError(f"Resource not found: {response.url}")
        elif status_code == 500:
            raise Exception(f"Server error: {response.text}")
        else:
            raise Exception(f"HTTP {status_code}: {response.text}")
    
    def run_pipeline(self) -> Dict[str, Any]:
        """
        Trigger pipeline execution.
        
        Returns:
            Dictionary with pipeline execution status and logs
        """
        try:
            response = self._make_request('/run-pipeline', 'GET')
            return response.json()
        except Exception as e:
            logger.error(f"Failed to run pipeline: {e}")
            raise
    
    def get_patient_master(self) -> pd.DataFrame:
        """
        Fetch patient master data.
        
        Returns:
            DataFrame with patient master data
        """
        try:
            response = self._make_request('/patient-master', 'GET')
            data = response.json()
            
            if not data:
                logger.warning("No patient master data returned")
                return pd.DataFrame()
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Failed to fetch patient master: {e}")
            raise
    
    def get_anomalies(self) -> pd.DataFrame:
        """
        Fetch anomaly data.
        
        Returns:
            DataFrame with anomaly data
        """
        try:
            response = self._make_request('/anomalies', 'GET')
            data = response.json()
            
            if not data:
                logger.warning("No anomaly data returned")
                return pd.DataFrame()
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Failed to fetch anomalies: {e}")
            raise
    
    def get_risk_scores(self) -> pd.DataFrame:
        """
        Fetch risk scores data.
        
        Returns:
            DataFrame with risk scores data
        """
        try:
            response = self._make_request('/risk-scores', 'GET')
            data = response.json()
            
            if not data:
                logger.warning("No risk scores data returned")
                return pd.DataFrame()
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Failed to fetch risk scores: {e}")
            # Do not raise error to prevent UI crash if file doesn't exist initially
            return pd.DataFrame()
    
    def get_trend_alerts(self) -> pd.DataFrame:
        """
        Fetch trend alerts data.
        
        Returns:
            DataFrame with trend alerts data
        """
        try:
            response = self._make_request('/trend-alerts', 'GET')
            data = response.json()
            
            if not data:
                logger.warning("No trend alerts data returned")
                return pd.DataFrame()
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Failed to fetch trend alerts: {e}")
            # Do not raise error to prevent UI crash if file doesn't exist initially
            return pd.DataFrame()
    
    def get_pipeline_history(self) -> pd.DataFrame:
        """
        Fetch pipeline run history data.
        
        Returns:
            DataFrame with pipeline run history data
        """
        try:
            response = self._make_request('/pipeline-history', 'GET')
            data = response.json()
            
            if not data:
                logger.warning("No pipeline history data returned")
                return pd.DataFrame()
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Failed to fetch pipeline history: {e}")
            # Do not raise error to prevent UI crash if table doesn't exist initially
            return pd.DataFrame()
    
    def get_alert_log(self) -> pd.DataFrame:
        """
        Fetch alert log data.
        
        Returns:
            DataFrame with alert log data
        """
        try:
            response = self._make_request('/alert-log', 'GET')
            data = response.json()
            
            if not data:
                logger.warning("No alert log data returned")
                return pd.DataFrame()
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Failed to fetch alert log: {e}")
            return pd.DataFrame()
    
    def get_new_alerts_count(self) -> dict:
        """
        Fetch new alerts count from most recent run.
        
        Returns:
            Dictionary with count and run_id
        """
        try:
            response = self._make_request('/new-alerts-count', 'GET')
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to fetch new alerts count: {e}")
            return {"count": 0, "run_id": None}
    
    def subscribe_webhook(self, url: str) -> dict:
        """
        Subscribe a webhook URL for alert notifications.
        
        Args:
            url: Webhook URL to subscribe
            
        Returns:
            Subscription status
        """
        try:
            response = self.session.post(
                f"{self.base_url}/webhook/subscribe",
                json={"url": url},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to subscribe webhook: {e}")
            raise

    def get_vitals(self) -> pd.DataFrame:
        """
        Fetch vitals data.
        
        Returns:
            DataFrame with vitals data
        """
        try:
            response = self._make_request('/vitals', 'GET')
            data = response.json()
            
            if not data:
                logger.warning("No vitals data returned")
                return pd.DataFrame()
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Failed to fetch vitals: {e}")
            raise
    
    def get_labs(self) -> pd.DataFrame:
        """
        Fetch labs data.
        
        Returns:
            DataFrame with labs data
        """
        try:
            response = self._make_request('/labs', 'GET')
            data = response.json()
            
            if not data:
                logger.warning("No labs data returned")
                return pd.DataFrame()
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Failed to fetch labs: {e}")
            raise
    
    def get_visualization(self, filename: str) -> bytes:
        """
        Fetch visualization image.
        
        Args:
            filename: Name of the visualization file (e.g., 'hr_trend.png')
            
        Returns:
            Image bytes
        """
        try:
            response = self._make_request(f'/visualizations/{filename}', 'GET')
            return response.content
            
        except Exception as e:
            logger.error(f"Failed to fetch visualization {filename}: {e}")
            raise
    
    def check_connection(self) -> bool:
        """
        Check if the API is reachable.
        
        Returns:
            True if API is reachable, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.base_url}/",
                timeout=5
            )
            return response.status_code < 500
        except Exception as e:
            logger.error(f"API connection check failed: {e}")
            return False
