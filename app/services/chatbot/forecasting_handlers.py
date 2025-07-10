"""
Forecasting-related Message Handlers

Handles sales forecasting requests, scenario analysis,
and forecast comparison operations.
"""

import logging
from typing import Dict, List, Tuple, Optional


class ForecastingHandlers:
    """Handles forecasting-related chatbot interactions"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
    
    def handle_forecasting_request(self, user_id: str, message: str) -> Tuple[str, List[str]]:
        """
        Handle sales forecasting requests
        
        Args:
            user_id: User ID
            message: Message containing forecast request
            
        Returns:
            Tuple of (response_text, suggestions_list)
        """
        try:
            from ..sales_forecasting import SalesForecasting
            forecaster = SalesForecasting(self.db_manager)
            
            # Parse forecasting request
            forecast_type = self._parse_forecast_request(message)
            
            if forecast_type == "quick":
                result = forecaster.generate_quick_forecast(user_id)
            elif forecast_type == "weekly":
                result = forecaster.generate_weekly_forecast(user_id)
            elif forecast_type == "monthly":
                result = forecaster.generate_monthly_forecast(user_id)
            elif forecast_type == "trend":
                result = forecaster.analyze_trends(user_id)
            else:
                # Default to quick forecast
                result = forecaster.generate_quick_forecast(user_id)
            
            if result.get("status") == "success":
                response = self._format_forecast_response(result)
                suggestions = [
                    "📊 View Details",
                    "📈 Weekly Forecast", 
                    "📅 Monthly Forecast",
                    "🔙 Main Menu"
                ]
            elif result.get("status") == "insufficient_data":
                response = f"📊 *Need More Data for Forecasting*\n\n{result.get('message', 'Not enough sales data')}\n\nTo generate accurate forecasts, I need:\n• At least 7 days of sales data\n• Multiple sales records\n• Consistent data entry"
                suggestions = [
                    "➕ Add Sales Data",
                    "📤 Upload Sales File",
                    "💡 Learn More",
                    "🔙 Main Menu"
                ]
            else:
                response = f"❌ *Forecasting Error*\n\n{result.get('message', 'Could not generate forecast')}"
                suggestions = ["🔄 Try Again", "🔙 Main Menu"]
            
            return response, suggestions
            
        except Exception as e:
            logging.error(f"Error handling forecasting request: {e}")
            response = "❌ Sorry, I couldn't generate a forecast right now. Please try again later."
            suggestions = ["🔄 Try Again", "🔙 Main Menu"]
            return response, suggestions
    
    def handle_forecast_comparison(self, user_id: str) -> Tuple[str, List[str]]:
        """
        Handle forecast vs actual comparison
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple of (response_text, suggestions_list)
        """
        try:
            from ..sales_forecasting import SalesForecasting
            forecaster = SalesForecasting(self.db_manager)
            
            comparison = forecaster.compare_forecast_vs_actual(user_id)
            
            if comparison.get("status") == "success":
                response = self._format_comparison_response(comparison)
                suggestions = [
                    "📈 New Forecast",
                    "📊 Accuracy Details",
                    "🎯 Improve Accuracy",
                    "🔙 Main Menu"
                ]
            elif comparison.get("status") == "no_forecasts":
                response = "📊 *No Previous Forecasts*\n\nI don't have any previous forecasts to compare with actual results.\n\nLet's create your first forecast!"
                suggestions = [
                    "📈 Quick Forecast",
                    "📅 Weekly Forecast",
                    "📤 Upload Data",
                    "🔙 Main Menu"
                ]
            else:
                response = f"❌ *Comparison Error*\n\n{comparison.get('message', 'Could not compare forecasts')}"
                suggestions = ["🔄 Try Again", "🔙 Main Menu"]
            
            return response, suggestions
            
        except Exception as e:
            logging.error(f"Error handling forecast comparison: {e}")
            response = "❌ Sorry, I couldn't compare forecasts right now. Please try again later."
            suggestions = ["🔄 Try Again", "🔙 Main Menu"]
            return response, suggestions
    
    def handle_scenario_analysis(self, user_id: str, message: str) -> Tuple[str, List[str]]:
        """
        Handle what-if scenario analysis
        
        Args:
            user_id: User ID
            message: Message containing scenario request
            
        Returns:
            Tuple of (response_text, suggestions_list)
        """
        try:
            from ..sales_forecasting import SalesForecasting
            forecaster = SalesForecasting(self.db_manager)
            
            # Parse scenario from message
            scenario = self._parse_scenario_request(message)
            
            result = forecaster.generate_scenario_forecast(user_id, scenario)
            
            if result.get("status") == "success":
                response = self._format_scenario_response(result, scenario)
                suggestions = [
                    "📈 Optimistic Scenario",
                    "📉 Conservative Scenario",
                    "🎯 Custom Scenario",
                    "🔙 Main Menu"
                ]
            else:
                response = f"❌ *Scenario Analysis Error*\n\n{result.get('message', 'Could not analyze scenario')}"
                suggestions = ["🔄 Try Again", "🔙 Main Menu"]
            
            return response, suggestions
            
        except Exception as e:
            logging.error(f"Error handling scenario analysis: {e}")
            response = "❌ Sorry, I couldn't analyze scenarios right now. Please try again later."
            suggestions = ["🔄 Try Again", "🔙 Main Menu"]
            return response, suggestions
    
    def _parse_forecast_request(self, message: str) -> str:
        """
        Parse the type of forecast requested
        
        Args:
            message: User message
            
        Returns:
            Forecast type string
        """
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['quick', 'fast', 'brief', 'summary']):
            return "quick"
        elif any(word in message_lower for word in ['week', 'weekly', '7 day']):
            return "weekly"
        elif any(word in message_lower for word in ['month', 'monthly', '30 day']):
            return "monthly"
        elif any(word in message_lower for word in ['trend', 'pattern', 'direction']):
            return "trend"
        else:
            return "quick"  # Default
    
    def _parse_scenario_request(self, message: str) -> Dict:
        """
        Parse scenario parameters from message
        
        Args:
            message: User message
            
        Returns:
            Scenario parameters dictionary
        """
        message_lower = message.lower()
        
        scenario = {
            "type": "normal",
            "growth_rate": 0.0,
            "market_conditions": "normal"
        }
        
        if any(word in message_lower for word in ['optimistic', 'best case', 'good', 'growth']):
            scenario["type"] = "optimistic"
            scenario["growth_rate"] = 0.15  # 15% growth
            scenario["market_conditions"] = "favorable"
        elif any(word in message_lower for word in ['pessimistic', 'worst case', 'bad', 'decline']):
            scenario["type"] = "pessimistic"
            scenario["growth_rate"] = -0.10  # 10% decline
            scenario["market_conditions"] = "unfavorable"
        elif any(word in message_lower for word in ['conservative', 'cautious', 'steady']):
            scenario["type"] = "conservative"
            scenario["growth_rate"] = 0.05  # 5% growth
            scenario["market_conditions"] = "stable"
        
        return scenario
    
    def _format_forecast_response(self, result: Dict) -> str:
        """
        Format forecast results for WhatsApp display
        
        Args:
            result: Forecast result dictionary
            
        Returns:
            Formatted response string
        """
        try:
            forecast_data = result.get("forecast", {})
            
            response = f"📈 *Sales Forecast* - {forecast_data.get('period', 'Next Period')}\n\n"
            
            # Main prediction
            predicted_revenue = forecast_data.get("predicted_revenue", 0)
            predicted_sales = forecast_data.get("predicted_sales", 0)
            confidence = forecast_data.get("confidence_score", 0)
            
            response += f"💰 Predicted Revenue: ${predicted_revenue:,.2f}\n"
            response += f"📊 Predicted Sales: {predicted_sales} transactions\n"
            response += f"🎯 Confidence: {confidence:.1%}\n\n"
            
            # Trend information
            trend = forecast_data.get("trend", {})
            if trend:
                direction = trend.get("direction", "stable")
                magnitude = trend.get("magnitude", 0)
                
                if direction == "increasing":
                    response += f"📈 Trend: Growing by {magnitude:.1%}\n"
                elif direction == "decreasing":
                    response += f"📉 Trend: Declining by {magnitude:.1%}\n"
                else:
                    response += f"➡️ Trend: Stable\n"
            
            # Key insights
            insights = forecast_data.get("insights", [])
            if insights:
                response += "\n*Key Points:*\n"
                for insight in insights[:3]:  # Show top 3
                    response += f"• {insight}\n"
            
            # Recommendations
            recommendations = forecast_data.get("recommendations", [])
            if recommendations:
                response += "\n*Recommendations:*\n"
                for rec in recommendations[:2]:  # Show top 2
                    response += f"• {rec}\n"
            
            return response.strip()
            
        except Exception as e:
            logging.error(f"Error formatting forecast response: {e}")
            return "❌ Error formatting forecast data"
    
    def _format_comparison_response(self, comparison: Dict) -> str:
        """
        Format forecast comparison results
        
        Args:
            comparison: Comparison result dictionary
            
        Returns:
            Formatted response string
        """
        try:
            accuracy = comparison.get("accuracy", {})
            
            response = "📊 *Forecast vs Actual Results*\n\n"
            
            # Overall accuracy
            overall_accuracy = accuracy.get("overall_accuracy", 0)
            response += f"🎯 Overall Accuracy: {overall_accuracy:.1%}\n\n"
            
            # Revenue comparison
            revenue_comparison = comparison.get("revenue_comparison", {})
            if revenue_comparison:
                predicted = revenue_comparison.get("predicted", 0)
                actual = revenue_comparison.get("actual", 0)
                accuracy_pct = revenue_comparison.get("accuracy", 0)
                
                response += f"💰 Revenue Accuracy: {accuracy_pct:.1%}\n"
                response += f"   Predicted: ${predicted:,.2f}\n"
                response += f"   Actual: ${actual:,.2f}\n\n"
            
            # Performance insights
            insights = comparison.get("insights", [])
            if insights:
                response += "*Performance Insights:*\n"
                for insight in insights[:3]:
                    response += f"• {insight}\n"
            
            return response.strip()
            
        except Exception as e:
            logging.error(f"Error formatting comparison response: {e}")
            return "❌ Error formatting comparison data"
    
    def _format_scenario_response(self, result: Dict, scenario: Dict) -> str:
        """
        Format scenario analysis results
        
        Args:
            result: Scenario result dictionary
            scenario: Scenario parameters
            
        Returns:
            Formatted response string
        """
        try:
            scenario_data = result.get("scenario_forecast", {})
            scenario_type = scenario.get("type", "normal").title()
            
            response = f"🎯 *{scenario_type} Scenario Analysis*\n\n"
            
            # Scenario predictions
            predicted_revenue = scenario_data.get("predicted_revenue", 0)
            baseline_revenue = result.get("baseline_revenue", 0)
            
            response += f"💰 Scenario Revenue: ${predicted_revenue:,.2f}\n"
            response += f"📊 Baseline Revenue: ${baseline_revenue:,.2f}\n"
            
            if baseline_revenue > 0:
                difference = predicted_revenue - baseline_revenue
                diff_pct = (difference / baseline_revenue) * 100
                
                if difference > 0:
                    response += f"📈 Upside: +${difference:,.2f} ({diff_pct:+.1f}%)\n"
                else:
                    response += f"📉 Risk: ${difference:,.2f} ({diff_pct:+.1f}%)\n"
            
            response += f"\n*Scenario Assumptions:*\n"
            response += f"• Market Conditions: {scenario.get('market_conditions', 'Normal')}\n"
            response += f"• Growth Rate: {scenario.get('growth_rate', 0):+.1%}\n"
            
            # Scenario insights
            insights = scenario_data.get("insights", [])
            if insights:
                response += "\n*Key Insights:*\n"
                for insight in insights[:2]:
                    response += f"• {insight}\n"
            
            return response.strip()
            
        except Exception as e:
            logging.error(f"Error formatting scenario response: {e}")
            return "❌ Error formatting scenario data"