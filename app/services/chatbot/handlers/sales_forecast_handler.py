"""
Sales Forecasting Handler

Handles all sales forecasting, scenario analysis, and forecast comparison requests.
Integrates with the sales forecasting service for advanced analytics.
"""

from typing import Dict, List, Tuple
import logging
from .base_handler import BaseHandler


class SalesForecastHandler(BaseHandler):
    """Handles sales forecasting and related analytics"""
    
    def __init__(self, db_manager=None):
        super().__init__(db_manager)
        self.forecasting_service = None
        self._initialize_forecasting_service()
    
    def _initialize_forecasting_service(self):
        """Initialize the sales forecasting service"""
        try:
            from ...sales_forecasting import SalesForecasting
            self.forecasting_service = SalesForecasting(self.db_manager)
            self._log_handler_activity("system", "Forecasting service initialized")
        except ImportError as e:
            logging.warning(f"Could not load forecasting service: {e}")
    
    def handle(self, user_id: str, message: str, user_context: Dict) -> Tuple[str, List[str]]:
        """Handle forecasting requests"""
        self._log_handler_activity(user_id, "forecast_request", {"message": message[:50]})
        
        message_lower = message.lower()
        
        # Determine specific forecasting action
        if any(word in message_lower for word in ['comparison', 'accuracy', 'actual vs predicted']):
            return self._handle_forecast_comparison(user_id, user_context)
        elif any(word in message_lower for word in ['scenario', 'optimistic', 'pessimistic', 'what if']):
            return self._handle_scenario_analysis(user_id, message, user_context)
        elif any(word in message_lower for word in ['quick', 'simple', 'basic']):
            return self._handle_quick_forecast(user_id, user_context)
        else:
            return self._handle_general_forecast(user_id, user_context)
    
    def _handle_general_forecast(self, user_id: str, user_context: Dict) -> Tuple[str, List[str]]:
        """Handle general forecasting request"""
        if not self.forecasting_service:
            return self._get_forecast_unavailable_response()
        
        try:
            # Get forecast for next 30 days
            forecast_result = self.forecasting_service.generate_forecast(user_id, days=30)
            
            if forecast_result.get("status") == "success":
                forecast_data = forecast_result.get("forecast", {})
                return self._format_forecast_response(forecast_data)
            elif forecast_result.get("status") == "no_data":
                return self._get_no_data_response()
            else:
                return self._get_error_response(forecast_result.get("message"))
                
        except Exception as e:
            logging.error(f"Forecast generation error: {e}")
            return self._get_error_response()
    
    def _handle_quick_forecast(self, user_id: str, user_context: Dict) -> Tuple[str, List[str]]:
        """Handle quick forecast request"""
        if not self.forecasting_service:
            return self._get_forecast_unavailable_response()
        
        try:
            forecast_result = self.forecasting_service.generate_forecast(user_id, days=7)
            
            if forecast_result.get("status") == "success":
                forecast_data = forecast_result.get("forecast", {})
                response = self._format_quick_forecast_response(forecast_data)
                suggestions = [
                    "📅 Extended Forecast",
                    "🎯 Scenario Analysis", 
                    "📊 View Details",
                    "🔙 Main Menu"
                ]
                return response, suggestions
            else:
                return self._get_no_data_response()
                
        except Exception as e:
            logging.error(f"Quick forecast error: {e}")
            return self._get_error_response()
    
    def _handle_scenario_analysis(self, user_id: str, message: str, user_context: Dict) -> Tuple[str, List[str]]:
        """Handle scenario analysis request"""
        if not self.forecasting_service:
            return self._get_forecast_unavailable_response()
        
        try:
            # Determine scenario type
            message_lower = message.lower()
            if 'optimistic' in message_lower or 'best case' in message_lower:
                scenario_type = 'optimistic'
            elif 'pessimistic' in message_lower or 'worst case' in message_lower:
                scenario_type = 'pessimistic'
            else:
                scenario_type = 'realistic'
            
            scenarios = self.forecasting_service.generate_scenarios(user_id, scenario_type)
            
            if scenarios.get("status") == "success":
                return self._format_scenario_response(scenarios, scenario_type)
            else:
                return self._get_no_data_response()
                
        except Exception as e:
            logging.error(f"Scenario analysis error: {e}")
            return self._get_error_response()
    
    def _handle_forecast_comparison(self, user_id: str, user_context: Dict) -> Tuple[str, List[str]]:
        """Handle forecast accuracy comparison"""
        if not self.forecasting_service:
            return self._get_forecast_unavailable_response()
        
        try:
            comparison = self.forecasting_service.compare_forecast_accuracy(user_id)
            
            if comparison.get("status") == "success":
                return self._format_comparison_response(comparison)
            else:
                return self._get_no_data_response()
                
        except Exception as e:
            logging.error(f"Forecast comparison error: {e}")
            return self._get_error_response()
    
    def _format_forecast_response(self, forecast_data: Dict) -> Tuple[str, List[str]]:
        """Format forecast data into user-friendly response"""
        predicted_revenue = forecast_data.get('predicted_revenue', 0)
        confidence = forecast_data.get('confidence', 0)
        trend = forecast_data.get('trend', 'stable')
        
        response = f"📊 *30-Day Sales Forecast*\n\n"
        response += f"💰 Predicted Revenue: {self._format_currency(predicted_revenue)}\n"
        response += f"🎯 Confidence: {self._format_percentage(confidence * 100)}\n"
        response += f"📈 Trend: {trend.title()}\n\n"
        
        # Add key insights
        if forecast_data.get('insights'):
            response += "*Key Insights:*\n"
            for insight in forecast_data['insights'][:3]:
                response += f"• {insight}\n"
        
        suggestions = [
            "🎯 Scenario Analysis",
            "📊 View Chart", 
            "💡 Improve Accuracy",
            "🔙 Main Menu"
        ]
        
        return response, suggestions
    
    def _format_quick_forecast_response(self, forecast_data: Dict) -> str:
        """Format quick forecast response"""
        predicted_revenue = forecast_data.get('predicted_revenue', 0)
        daily_avg = predicted_revenue / 7
        
        response = f"⚡ *Quick 7-Day Forecast*\n\n"
        response += f"💰 Week Total: {self._format_currency(predicted_revenue)}\n"
        response += f"📅 Daily Average: {self._format_currency(daily_avg)}\n"
        response += f"📈 Trend: {forecast_data.get('trend', 'stable').title()}"
        
        return response
    
    def _format_scenario_response(self, scenarios: Dict, scenario_type: str) -> Tuple[str, List[str]]:
        """Format scenario analysis response"""
        scenario_data = scenarios.get('scenarios', {}).get(scenario_type, {})
        
        response = f"🎯 *{scenario_type.title()} Scenario Analysis*\n\n"
        response += f"💰 Revenue: {self._format_currency(scenario_data.get('revenue', 0))}\n"
        response += f"📊 Growth: {self._format_percentage(scenario_data.get('growth', 0))}\n"
        response += f"🎲 Probability: {self._format_percentage(scenario_data.get('probability', 0))}\n\n"
        
        if scenario_data.get('factors'):
            response += "*Key Factors:*\n"
            for factor in scenario_data['factors'][:3]:
                response += f"• {factor}\n"
        
        suggestions = [
            "📈 Optimistic View",
            "📉 Conservative View",
            "📊 Compare All",
            "🔙 Main Menu"
        ]
        
        return response, suggestions
    
    def _format_comparison_response(self, comparison: Dict) -> Tuple[str, List[str]]:
        """Format forecast comparison response"""
        accuracy = comparison.get('accuracy', 0)
        mae = comparison.get('mean_absolute_error', 0)
        
        response = f"📊 *Forecast Accuracy Report*\n\n"
        response += f"🎯 Overall Accuracy: {self._format_percentage(accuracy * 100)}\n"
        response += f"📏 Average Error: {self._format_currency(mae)}\n\n"
        
        if accuracy > 0.8:
            response += "✅ *Excellent accuracy!* Your forecasts are very reliable.\n"
        elif accuracy > 0.6:
            response += "👍 *Good accuracy.* Room for slight improvement.\n"
        else:
            response += "⚠️ *Accuracy could be improved.* Consider adding more data.\n"
        
        suggestions = [
            "📈 New Forecast",
            "🎯 Improve Accuracy",
            "📊 View Details", 
            "🔙 Main Menu"
        ]
        
        return response, suggestions
    
    def _get_forecast_unavailable_response(self) -> Tuple[str, List[str]]:
        """Response when forecasting service is unavailable"""
        response = "📊 *Sales Forecasting*\n\n⚠️ The forecasting service is currently unavailable. Please try again later or contact support."
        suggestions = ["🔄 Try Again", "📊 Basic Insights", "🔙 Main Menu"]
        return response, suggestions
    
    def _get_no_data_response(self) -> Tuple[str, List[str]]:
        """Response when no sales data is available"""
        response = "📊 *No Sales Data Available*\n\nI need sales data to generate forecasts. Let's get started!\n\nYou can:"
        suggestions = [
            "➕ Add Sales Record",
            "📤 Upload Sales File", 
            "💡 Learn More",
            "🔙 Main Menu"
        ]
        return response, suggestions