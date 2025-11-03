"""Alert/SLM integration."""

import logging
from typing import Dict, Any, Optional, List
import requests

logger = logging.getLogger(__name__)


class AlertSystem:
    """Alert/SLM system integration."""
    
    def __init__(self, endpoint: str, api_key: Optional[str] = None, namespace: Optional[str] = None):
        """
        Initialize alert system client.
        
        Args:
            endpoint: Alert endpoint URL
            api_key: API key for authentication
            namespace: Namespace/scope for alerts
        """
        self.endpoint = endpoint.rstrip('/')
        self.namespace = namespace
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({
                'Authorization': f'Key {api_key}',
                'Content-Type': 'application/json'
            })
    
    def list_alerts(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        List alerts with filtering.
        
        Args:
            status: Filter by status (open, closed, ack, etc.)
            severity: Filter by severity
            limit: Maximum number of results
            
        Returns:
            List of alerts
        """
        params = {
            "limit": min(limit, 100),  # Cap at 100
            "page_size": min(limit, 100)
        }
        
        if status:
            params["status"] = status
        
        if severity:
            params["severity"] = severity
        
        if self.namespace:
            params["namespace"] = self.namespace
        
        try:
            # Alerta API endpoint
            url = f"{self.endpoint}/alerts"
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            alerts = data.get("alerts", []) if isinstance(data, dict) else data
            
            return {
                "success": True,
                "alerts": alerts[:limit],
                "count": len(alerts)
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Alert API error: {e}")
            return {
                "success": False,
                "error": "API_ERROR",
                "message": str(e)
            }
    
    def get_alert(self, alert_id: str) -> Dict[str, Any]:
        """
        Get specific alert details.
        
        Args:
            alert_id: Alert ID
            
        Returns:
            Alert details
        """
        try:
            url = f"{self.endpoint}/alert/{alert_id}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            return {
                "success": True,
                "alert": response.json()
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Alert API error: {e}")
            return {
                "success": False,
                "error": "API_ERROR",
                "message": str(e)
            }
    
    def acknowledge_alert(self, alert_id: str, note: Optional[str] = None) -> Dict[str, Any]:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: Alert ID
            note: Optional acknowledgment note
            
        Returns:
            Acknowledgment result
        """
        try:
            url = f"{self.endpoint}/alert/{alert_id}/action"
            payload = {
                "action": "ack",
                "text": note or "Acknowledged via MCP"
            }
            
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            return {
                "success": True,
                "alert_id": alert_id,
                "action": "acknowledged"
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Alert API error: {e}")
            return {
                "success": False,
                "error": "API_ERROR",
                "message": str(e)
            }