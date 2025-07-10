"""
Anomaly Detection Message Handlers

Handles anomaly detection requests and analysis operations.
"""

import logging
from typing import Dict, List, Tuple


class AnomalyHandlers:
    """Handles anomaly detection chatbot interactions"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
    
    def handle_anomaly_analysis_request(self, user_id: str, message: str) -> Tuple[str, List[str]]:
        """
        Handle anomaly detection and analysis requests
        
        Args:
            user_id: User ID
            message: User message
            
        Returns:
            Tuple of (response_text, suggestions_list)
        """
        try:
            from ..anomaly_analyzer import create_anomaly_analyzer
            analyzer = create_anomaly_analyzer(self.db_manager)
            
            # Determine type of analysis requested
            if any(word in message.lower() for word in ['alert', 'critical', 'urgent']):
                result = analyzer.get_anomaly_alerts(user_id)
                return self._handle_alerts_result(result)
            else:
                result = analyzer.run_full_analysis(user_id)
                return self._handle_analysis_result(result)
            
        except Exception as e:
            logging.error(f"Error handling anomaly analysis: {e}")
            response = "❌ Sorry, I couldn't run anomaly analysis right now. Please try again later."
            suggestions = ["🔄 Try Again", "🔙 Main Menu"]
            return response, suggestions
    
    def _handle_analysis_result(self, result: Dict) -> Tuple[str, List[str]]:
        """Handle full analysis result"""
        if result.get("status") == "success":
            response = self._format_anomaly_response(result)
            suggestions = [
                "📊 View Details",
                "🚨 Critical Alerts",
                "💡 Get Recommendations", 
                "🔙 Main Menu"
            ]
        elif result.get("status") == "no_anomalies":
            response = f"✅ *Great News!*\n\n{result.get('message')}\n\nYour business metrics look healthy with no significant anomalies detected."
            suggestions = [
                "📈 Sales Forecast",
                "📊 Business Insights",
                "➕ Add More Data",
                "🔙 Main Menu"
            ]
        else:
            response = f"❌ *Analysis Error*\n\n{result.get('message', 'Could not run anomaly analysis')}"
            suggestions = ["🔄 Try Again", "🔙 Main Menu"]
        
        return response, suggestions
    
    def _handle_alerts_result(self, result: Dict) -> Tuple[str, List[str]]:
        """Handle alerts-specific result"""
        if result.get("status") == "alerts_found":
            response = self._format_alert_response(result)
            suggestions = [
                "🔍 Investigate Issues",
                "✅ Mark Resolved",
                "📊 Full Analysis",
                "🔙 Main Menu"
            ]
        elif result.get("status") == "no_alerts":
            response = "✅ *No Critical Alerts*\n\nGreat news! No urgent issues detected in your business data."
            suggestions = [
                "📊 Full Analysis",
                "📈 Sales Forecast",
                "🔙 Main Menu"
            ]
        else:
            response = f"❌ *Alert Check Error*\n\n{result.get('message', 'Could not check alerts')}"
            suggestions = ["🔄 Try Again", "🔙 Main Menu"]
        
        return response, suggestions
    
    def _format_anomaly_response(self, result: Dict) -> str:
        """
        Format anomaly analysis results for WhatsApp display
        
        Args:
            result: Analysis result dictionary
            
        Returns:
            Formatted response string
        """
        try:
            anomalies = result.get("anomalies", [])
            summary = result.get("summary", {})
            
            response = "🔍 *Anomaly Detection Results*\n\n"
            
            # Summary stats
            total_anomalies = summary.get("total_anomalies", len(anomalies))
            critical_count = summary.get("critical_count", 0)
            warning_count = summary.get("warning_count", 0)
            
            if total_anomalies == 0:
                response += "✅ No anomalies detected in your data!\n\nYour business metrics appear healthy."
                return response
            
            response += f"📊 Found {total_anomalies} anomalies:\n"
            if critical_count > 0:
                response += f"🚨 Critical: {critical_count}\n"
            if warning_count > 0:
                response += f"⚠️ Warning: {warning_count}\n"
            
            response += "\n*Top Issues:*\n"
            
            # Show top 3 anomalies
            for i, anomaly in enumerate(anomalies[:3]):
                severity = anomaly.get("severity", "unknown")
                anomaly_type = anomaly.get("type", "unknown")
                description = anomaly.get("description", "No description")
                
                severity_icon = "🚨" if severity == "critical" else "⚠️"
                response += f"{severity_icon} {anomaly_type.title()}: {description}\n"
                
                # Add date/context if available
                date = anomaly.get("date")
                if date:
                    response += f"   Date: {date}\n"
            
            if len(anomalies) > 3:
                response += f"\n... and {len(anomalies) - 3} more issues"
            
            return response.strip()
            
        except Exception as e:
            logging.error(f"Error formatting anomaly response: {e}")
            return "❌ Error formatting anomaly data"
    
    def _format_alert_response(self, result: Dict) -> str:
        """
        Format alert results for WhatsApp display
        
        Args:
            result: Alert result dictionary
            
        Returns:
            Formatted response string
        """
        try:
            alerts = result.get("alerts", [])
            
            response = "🚨 *Critical Alerts*\n\n"
            
            if not alerts:
                return "✅ No critical alerts found!"
            
            response += f"Found {len(alerts)} urgent issues:\n\n"
            
            for i, alert in enumerate(alerts[:3]):  # Show top 3
                title = alert.get("title", "Unknown Issue")
                description = alert.get("description", "No details")
                severity = alert.get("severity", "medium")
                
                severity_icon = "🚨" if severity == "critical" else "⚠️"
                response += f"{severity_icon} *{title}*\n"
                response += f"   {description}\n"
                
                # Add recommended action if available
                action = alert.get("recommended_action")
                if action:
                    response += f"   💡 Action: {action}\n"
                
                response += "\n"
            
            if len(alerts) > 3:
                response += f"... and {len(alerts) - 3} more alerts"
            
            return response.strip()
            
        except Exception as e:
            logging.error(f"Error formatting alert response: {e}")
            return "❌ Error formatting alert data"
    
    def get_anomaly_summary(self, user_id: str) -> Dict:
        """
        Get anomaly summary for user
        
        Args:
            user_id: User ID
            
        Returns:
            Anomaly summary dictionary
        """
        try:
            from ..anomaly_analyzer import create_anomaly_analyzer
            analyzer = create_anomaly_analyzer(self.db_manager)
            return analyzer.get_anomaly_summary(user_id)
        except Exception as e:
            logging.error(f"Error getting anomaly summary: {e}")
            return {"status": "error", "message": str(e)}
    
    def mark_anomaly_resolved(self, user_id: str, anomaly_id: str) -> bool:
        """
        Mark an anomaly as resolved
        
        Args:
            user_id: User ID
            anomaly_id: Anomaly identifier
            
        Returns:
            Success status
        """
        try:
            from ..anomaly_analyzer import create_anomaly_analyzer
            analyzer = create_anomaly_analyzer(self.db_manager)
            return analyzer.mark_resolved(user_id, anomaly_id)
        except Exception as e:
            logging.error(f"Error marking anomaly resolved: {e}")
            return False