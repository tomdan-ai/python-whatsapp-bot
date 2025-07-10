"""
Anomaly Detection Handler

Handles anomaly detection requests and provides insights about unusual patterns
in business data.
"""

from typing import Dict, List, Tuple
import logging
from .base_handler import BaseHandler


class AnomalyHandler(BaseHandler):
    """Handles anomaly detection and analysis"""
    
    def __init__(self, db_manager=None):
        super().__init__(db_manager)
        self.anomaly_service = None
        self._initialize_anomaly_service()
    
    def _initialize_anomaly_service(self):
        """Initialize the anomaly detection service"""
        try:
            from ...anomaly_detection import AnomalyDetection
            self.anomaly_service = AnomalyDetection(self.db_manager)
            self._log_handler_activity("system", "Anomaly service initialized")
        except ImportError as e:
            logging.warning(f"Could not load anomaly service: {e}")
    
    def handle(self, user_id: str, message: str, user_context: Dict) -> Tuple[str, List[str]]:
        """Handle anomaly detection requests"""
        self._log_handler_activity(user_id, "anomaly_request")
        
        if not self.anomaly_service:
            return self._get_service_unavailable_response()
        
        try:
            # Analyze recent data for anomalies
            anomalies = self.anomaly_service.detect_anomalies(user_id, days=30)
            
            if anomalies.get("status") == "success":
                anomaly_data = anomalies.get("anomalies", [])
                if anomaly_data:
                    return self._format_anomalies_response(anomaly_data)
                else:
                    return self._get_no_anomalies_response()
            elif anomalies.get("status") == "no_data":
                return self._get_no_data_response()
            else:
                return self._get_error_response(anomalies.get("message"))
                
        except Exception as e:
            logging.error(f"Anomaly detection error: {e}")
            return self._get_error_response()
    
    def _format_anomalies_response(self, anomalies: List[Dict]) -> Tuple[str, List[str]]:
        """Format anomaly detection results"""
        response = "🔍 *Anomaly Detection Results*\n\n"
        
        if len(anomalies) == 1:
            response += "⚠️ Found 1 potential issue:\n\n"
        else:
            response += f"⚠️ Found {len(anomalies)} potential issues:\n\n"
        
        # Show top 3 most significant anomalies
        for i, anomaly in enumerate(anomalies[:3]):
            severity = anomaly.get('severity', 'medium')
            severity_emoji = self._get_severity_emoji(severity)
            
            response += f"{severity_emoji} **{anomaly.get('type', 'Unknown')}**\n"
            response += f"• Date: {anomaly.get('date', 'Unknown')}\n"
            response += f"• Impact: {anomaly.get('description', 'No description')}\n"
            
            if anomaly.get('possible_cause'):
                response += f"• Possible cause: {anomaly['possible_cause']}\n"
            
            response += "\n"
        
        if len(anomalies) > 3:
            response += f"...and {len(anomalies) - 3} more issues\n"
        
        suggestions = [
            "📊 Show Details",
            "💡 Get Solutions",
            "📅 Compare Periods",
            "🔙 Main Menu"
        ]
        
        return response, suggestions
    
    def _get_severity_emoji(self, severity: str) -> str:
        """Get emoji for anomaly severity"""
        severity_map = {
            'high': '🚨',
            'medium': '⚠️',
            'low': '📊',
            'critical': '🔴'
        }
        return severity_map.get(severity.lower(), '⚠️')
    
    def _get_no_anomalies_response(self) -> Tuple[str, List[str]]:
        """Response when no anomalies are detected"""
        response = "✅ *No Anomalies Detected*\n\n🎉 Great news! Your recent business data looks normal. No unusual patterns or issues detected in the last 30 days.\n\nKeep monitoring regularly for optimal performance!"
        
        suggestions = [
            "📊 View Analytics",
            "📈 Check Trends",
            "🔄 Check Again", 
            "🔙 Main Menu"
        ]
        
        return response, suggestions
    
    def _get_no_data_response(self) -> Tuple[str, List[str]]:
        """Response when no data is available for analysis"""
        response = "🔍 *Insufficient Data for Analysis*\n\nI need more sales data to detect anomalies effectively. Please add some sales records first."
        
        suggestions = [
            "➕ Add Sales Data",
            "📤 Upload File",
            "💡 Learn More",
            "🔙 Main Menu"
        ]
        
        return response, suggestions
    
    def _get_service_unavailable_response(self) -> Tuple[str, List[str]]:
        """Response when anomaly service is unavailable"""
        response = "🔍 *Anomaly Detection Unavailable*\n\n⚠️ The anomaly detection service is currently unavailable. Please try again later."
        
        suggestions = ["🔄 Try Again", "📊 Basic Analytics", "🔙 Main Menu"]
        return response, suggestions