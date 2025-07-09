import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import json

class SalesForecastingEngine:
    """Advanced sales forecasting with multiple algorithms"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.models = {}
        self.model_performance = {}
    
    def generate_forecast(self, user_id: str, forecast_days: int = 30, historical_days: int = 90) -> Dict:
        """Generate sales forecast for specified period"""
        try:
            from .sales_models import SalesDataManager
            sales_manager = SalesDataManager(self.db_manager)
            
            # Get historical data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=historical_days)
            historical_data = sales_manager.get_sales_data(user_id, start_date, end_date)
            
            if len(historical_data) < 7:  # Need at least a week of data
                return {
                    "status": "insufficient_data",
                    "message": f"Need at least 7 days of sales data for forecasting. You have {len(historical_data)} records.",
                    "suggestions": [
                        "Add more historical sales data",
                        "Upload past sales records from spreadsheet",
                        "Track daily sales for at least a week"
                    ]
                }
            
            # Prepare data for forecasting
            forecast_data = self._prepare_forecast_data(historical_data)
            
            if forecast_data.empty:
                return {
                    "status": "error",
                    "message": "Could not prepare data for forecasting",
                    "suggestions": ["Check data quality and try again"]
                }
            
            # Generate forecasts using multiple methods
            forecasts = {}
            
            # Method 1: Linear Trend
            linear_forecast = self._linear_trend_forecast(forecast_data, forecast_days)
            if linear_forecast:
                forecasts['linear_trend'] = linear_forecast
            
            # Method 2: Moving Average
            moving_avg_forecast = self._moving_average_forecast(forecast_data, forecast_days)
            if moving_avg_forecast:
                forecasts['moving_average'] = moving_avg_forecast
            
            # Method 3: Seasonal Decomposition (if enough data)
            if len(forecast_data) >= 14:  # At least 2 weeks
                seasonal_forecast = self._seasonal_forecast(forecast_data, forecast_days)
                if seasonal_forecast:
                    forecasts['seasonal'] = seasonal_forecast
            
            # Method 4: Exponential Smoothing
            exp_forecast = self._exponential_smoothing_forecast(forecast_data, forecast_days)
            if exp_forecast:
                forecasts['exponential'] = exp_forecast
            
            if not forecasts:
                return {
                    "status": "error",
                    "message": "Could not generate any forecasts",
                    "suggestions": ["Add more consistent sales data"]
                }
            
            # Select best forecast
            best_forecast = self._select_best_forecast(forecasts, forecast_data)
            
            # Generate insights
            insights = self._generate_forecast_insights(best_forecast, forecast_data, forecasts)
            
            return {
                "status": "success",
                "forecast_period": f"Next {forecast_days} days",
                "historical_period": f"Based on {len(historical_data)} records from last {historical_days} days",
                "best_method": best_forecast['method'],
                "forecast": best_forecast,
                "alternative_forecasts": {k: v for k, v in forecasts.items() if k != best_forecast['method']},
                "insights": insights,
                "confidence": self._calculate_confidence(best_forecast, forecast_data)
            }
            
        except Exception as e:
            logging.error(f"Error generating forecast: {e}")
            return {"status": "error", "message": f"Error generating forecast: {str(e)}"}
    
    def _prepare_forecast_data(self, sales_data: List[Dict]) -> pd.DataFrame:
        """Prepare sales data for forecasting"""
        try:
            # Convert to DataFrame
            df = pd.DataFrame(sales_data)
            
            # Ensure date column is datetime
            df['date'] = pd.to_datetime(df['date'])
            
            # Group by date and sum total amounts
            daily_sales = df.groupby(df['date'].dt.date).agg({
                'total_amount': 'sum',
                'quantity': 'sum',
                'product_name': 'count'  # Number of transactions
            }).reset_index()
            
            daily_sales.columns = ['date', 'revenue', 'quantity', 'transactions']
            daily_sales['date'] = pd.to_datetime(daily_sales['date'])
            
            # Sort by date
            daily_sales = daily_sales.sort_values('date').reset_index(drop=True)
            
            # Add time-based features
            daily_sales['day_of_week'] = daily_sales['date'].dt.dayofweek
            daily_sales['day_of_month'] = daily_sales['date'].dt.day
            daily_sales['week_of_year'] = daily_sales['date'].dt.isocalendar().week
            daily_sales['days_since_start'] = (daily_sales['date'] - daily_sales['date'].min()).dt.days
            
            # Add rolling averages
            daily_sales['revenue_ma_7'] = daily_sales['revenue'].rolling(window=7, min_periods=1).mean()
            daily_sales['revenue_ma_14'] = daily_sales['revenue'].rolling(window=14, min_periods=1).mean()
            
            return daily_sales
            
        except Exception as e:
            logging.error(f"Error preparing forecast data: {e}")
            return pd.DataFrame()
    
    def _linear_trend_forecast(self, data: pd.DataFrame, forecast_days: int) -> Optional[Dict]:
        """Generate forecast using linear regression"""
        try:
            if len(data) < 3:
                return None
            
            # Prepare features
            X = data[['days_since_start']].values
            y = data['revenue'].values
            
            # Fit model
            model = LinearRegression()
            model.fit(X, y)
            
            # Generate predictions
            last_day = data['days_since_start'].max()
            future_days = np.array([[last_day + i + 1] for i in range(forecast_days)])
            predictions = model.predict(future_days)
            
            # Ensure non-negative predictions
            predictions = np.maximum(predictions, 0)
            
            # Create forecast dates
            last_date = data['date'].max()
            forecast_dates = [last_date + timedelta(days=i+1) for i in range(forecast_days)]
            
            # Calculate model performance
            train_predictions = model.predict(X)
            mae = mean_absolute_error(y, train_predictions)
            rmse = np.sqrt(mean_squared_error(y, train_predictions))
            
            return {
                'method': 'linear_trend',
                'predictions': predictions.tolist(),
                'dates': [date.strftime('%Y-%m-%d') for date in forecast_dates],
                'total_forecast': float(predictions.sum()),
                'average_daily': float(predictions.mean()),
                'performance': {
                    'mae': float(mae),
                    'rmse': float(rmse),
                    'model_score': float(model.score(X, y))
                },
                'trend': 'increasing' if model.coef_[0] > 0 else 'decreasing',
                'daily_change': float(model.coef_[0])
            }
            
        except Exception as e:
            logging.error(f"Linear trend forecast error: {e}")
            return None
    
    def _moving_average_forecast(self, data: pd.DataFrame, forecast_days: int, window: int = 7) -> Optional[Dict]:
        """Generate forecast using moving average"""
        try:
            if len(data) < window:
                window = len(data)
            
            # Calculate moving average
            recent_avg = data['revenue'].tail(window).mean()
            
            # Generate predictions (constant forecast)
            predictions = [recent_avg] * forecast_days
            
            # Create forecast dates
            last_date = data['date'].max()
            forecast_dates = [last_date + timedelta(days=i+1) for i in range(forecast_days)]
            
            # Calculate performance using historical moving average
            historical_ma = data['revenue'].rolling(window=window, min_periods=1).mean()
            actual = data['revenue'].iloc[window-1:]
            predicted = historical_ma.iloc[window-1:]
            
            if len(actual) > 0:
                mae = mean_absolute_error(actual, predicted)
                rmse = np.sqrt(mean_squared_error(actual, predicted))
            else:
                mae = rmse = 0
            
            return {
                'method': 'moving_average',
                'predictions': predictions,
                'dates': [date.strftime('%Y-%m-%d') for date in forecast_dates],
                'total_forecast': float(recent_avg * forecast_days),
                'average_daily': float(recent_avg),
                'performance': {
                    'mae': float(mae),
                    'rmse': float(rmse),
                    'window': window
                },
                'trend': 'stable',
                'daily_change': 0.0
            }
            
        except Exception as e:
            logging.error(f"Moving average forecast error: {e}")
            return None
    
    def _seasonal_forecast(self, data: pd.DataFrame, forecast_days: int) -> Optional[Dict]:
        """Generate forecast considering seasonal patterns"""
        try:
            if len(data) < 14:
                return None
            
            # Calculate day-of-week averages
            dow_avg = data.groupby('day_of_week')['revenue'].mean()
            
            # Generate predictions based on day of week pattern
            last_date = data['date'].max()
            predictions = []
            forecast_dates = []
            
            for i in range(forecast_days):
                forecast_date = last_date + timedelta(days=i+1)
                dow = forecast_date.weekday()
                
                # Use day-of-week average with overall trend
                base_prediction = dow_avg.get(dow, data['revenue'].mean())
                
                # Apply slight trend if data shows it
                recent_trend = data['revenue'].tail(7).mean() / data['revenue'].head(7).mean()
                if not np.isnan(recent_trend) and recent_trend != 0:
                    trend_factor = min(max(recent_trend, 0.5), 2.0)  # Limit extreme trends
                    base_prediction *= trend_factor
                
                predictions.append(max(base_prediction, 0))
                forecast_dates.append(forecast_date)
            
            # Calculate performance
            # Simulate performance by comparing predicted vs actual for historical data
            mae = rmse = 0
            if len(data) >= 14:
                test_size = min(7, len(data) // 2)
                test_data = data.tail(test_size)
                predicted_test = []
                
                for _, row in test_data.iterrows():
                    dow = row['day_of_week']
                    pred = dow_avg.get(dow, data['revenue'].mean())
                    predicted_test.append(pred)
                
                mae = mean_absolute_error(test_data['revenue'], predicted_test)
                rmse = np.sqrt(mean_squared_error(test_data['revenue'], predicted_test))
            
            return {
                'method': 'seasonal',
                'predictions': predictions,
                'dates': [date.strftime('%Y-%m-%d') for date in forecast_dates],
                'total_forecast': float(sum(predictions)),
                'average_daily': float(np.mean(predictions)),
                'performance': {
                    'mae': float(mae),
                    'rmse': float(rmse)
                },
                'trend': 'seasonal_pattern',
                'daily_change': float(np.std(predictions)),
                'weekly_pattern': dow_avg.to_dict()
            }
            
        except Exception as e:
            logging.error(f"Seasonal forecast error: {e}")
            return None
    
    def _exponential_smoothing_forecast(self, data: pd.DataFrame, forecast_days: int, alpha: float = 0.3) -> Optional[Dict]:
        """Generate forecast using exponential smoothing"""
        try:
            if len(data) < 2:
                return None
            
            revenue_data = data['revenue'].values
            
            # Simple exponential smoothing
            smoothed = [revenue_data[0]]
            for i in range(1, len(revenue_data)):
                smoothed_value = alpha * revenue_data[i] + (1 - alpha) * smoothed[-1]
                smoothed.append(smoothed_value)
            
            # Forecast future values
            last_smoothed = smoothed[-1]
            predictions = [last_smoothed] * forecast_days
            
            # Create forecast dates
            last_date = data['date'].max()
            forecast_dates = [last_date + timedelta(days=i+1) for i in range(forecast_days)]
            
            # Calculate performance
            mae = mean_absolute_error(revenue_data[1:], smoothed[1:])
            rmse = np.sqrt(mean_squared_error(revenue_data[1:], smoothed[1:]))
            
            return {
                'method': 'exponential',
                'predictions': predictions,
                'dates': [date.strftime('%Y-%m-%d') for date in forecast_dates],
                'total_forecast': float(last_smoothed * forecast_days),
                'average_daily': float(last_smoothed),
                'performance': {
                    'mae': float(mae),
                    'rmse': float(rmse),
                    'alpha': alpha
                },
                'trend': 'smoothed',
                'daily_change': 0.0
            }
            
        except Exception as e:
            logging.error(f"Exponential smoothing forecast error: {e}")
            return None
    
    def _select_best_forecast(self, forecasts: Dict, historical_data: pd.DataFrame) -> Dict:
        """Select the best forecast based on performance metrics"""
        try:
            best_method = None
            best_score = float('inf')
            
            for method, forecast in forecasts.items():
                # Score based on MAE (lower is better)
                mae = forecast.get('performance', {}).get('mae', float('inf'))
                
                # Penalize extreme predictions
                avg_daily = forecast.get('average_daily', 0)
                historical_avg = historical_data['revenue'].mean()
                
                if historical_avg > 0:
                    ratio = avg_daily / historical_avg
                    if ratio > 3 or ratio < 0.1:  # Too extreme
                        mae *= 2  # Penalty
                
                if mae < best_score:
                    best_score = mae
                    best_method = method
            
            return forecasts[best_method] if best_method else list(forecasts.values())[0]
            
        except Exception as e:
            logging.error(f"Error selecting best forecast: {e}")
            return list(forecasts.values())[0] if forecasts else {}
    
    def _generate_forecast_insights(self, best_forecast: Dict, historical_data: pd.DataFrame, all_forecasts: Dict) -> List[str]:
        """Generate insights about the forecast"""
        insights = []
        
        try:
            forecast_total = best_forecast.get('total_forecast', 0)
            forecast_daily = best_forecast.get('average_daily', 0)
            historical_daily = historical_data['revenue'].mean()
            
            # Revenue comparison
            if historical_daily > 0:
                change_percent = ((forecast_daily - historical_daily) / historical_daily) * 100
                if change_percent > 10:
                    insights.append(f"📈 Forecast shows {change_percent:.1f}% increase in daily revenue")
                elif change_percent < -10:
                    insights.append(f"📉 Forecast indicates {abs(change_percent):.1f}% decrease in daily revenue")
                else:
                    insights.append("📊 Forecast shows stable revenue trends")
            
            # Forecast totals
            insights.append(f"💰 Projected total revenue: ${forecast_total:.2f}")
            insights.append(f"📅 Expected daily average: ${forecast_daily:.2f}")
            
            # Method insights
            method = best_forecast.get('method', 'unknown')
            if method == 'linear_trend':
                trend = best_forecast.get('trend', 'stable')
                insights.append(f"📈 Based on {trend} trend analysis")
            elif method == 'seasonal':
                insights.append("🔄 Accounts for weekly sales patterns")
            elif method == 'moving_average':
                insights.append("📊 Based on recent sales average")
            
            # Performance insights
            mae = best_forecast.get('performance', {}).get('mae', 0)
            if mae > 0:
                accuracy_percent = max(0, 100 - (mae / historical_daily * 100)) if historical_daily > 0 else 0
                insights.append(f"🎯 Model accuracy: {accuracy_percent:.1f}%")
            
            # Recommendations
            if forecast_daily < historical_daily * 0.8:
                insights.append("⚠️ Consider marketing boost to maintain revenue")
            elif forecast_daily > historical_daily * 1.2:
                insights.append("🚀 Prepare for increased demand and inventory")
            
        except Exception as e:
            logging.error(f"Error generating insights: {e}")
        
        return insights
    
    def _calculate_confidence(self, forecast: Dict, historical_data: pd.DataFrame) -> str:
        """Calculate confidence level for the forecast"""
        try:
            mae = forecast.get('performance', {}).get('mae', float('inf'))
            historical_avg = historical_data['revenue'].mean()
            data_points = len(historical_data)
            
            # Calculate confidence based on multiple factors
            confidence_score = 0
            
            # Factor 1: Accuracy (MAE relative to average)
            if historical_avg > 0:
                accuracy_ratio = mae / historical_avg
                if accuracy_ratio < 0.1:
                    confidence_score += 40
                elif accuracy_ratio < 0.2:
                    confidence_score += 30
                elif accuracy_ratio < 0.3:
                    confidence_score += 20
                else:
                    confidence_score += 10
            
            # Factor 2: Data quantity
            if data_points >= 30:
                confidence_score += 30
            elif data_points >= 14:
                confidence_score += 20
            elif data_points >= 7:
                confidence_score += 10
            
            # Factor 3: Data consistency (low variance is better)
            revenue_cv = historical_data['revenue'].std() / historical_avg if historical_avg > 0 else float('inf')
            if revenue_cv < 0.5:
                confidence_score += 20
            elif revenue_cv < 1.0:
                confidence_score += 15
            elif revenue_cv < 2.0:
                confidence_score += 10
            
            # Factor 4: Method reliability
            method = forecast.get('method', '')
            if method in ['linear_trend', 'seasonal']:
                confidence_score += 10
            
            # Convert to confidence level
            if confidence_score >= 80:
                return "High"
            elif confidence_score >= 60:
                return "Medium"
            elif confidence_score >= 40:
                return "Low"
            else:
                return "Very Low"
                
        except Exception as e:
            logging.error(f"Error calculating confidence: {e}")
            return "Unknown"
    
    def get_forecast_accuracy(self, user_id: str) -> Dict:
        """Get historical forecast accuracy for user"""
        try:
            # This would track past forecasts vs actual results
            # For now, return placeholder
            return {
                "historical_accuracy": "Not enough data",
                "suggestions": [
                    "Make more forecasts to track accuracy",
                    "Continue recording daily sales",
                    "Compare forecasts with actual results"
                ]
            }
        except Exception as e:
            logging.error(f"Error getting forecast accuracy: {e}")
            return {"error": str(e)}

# Initialize forecasting engine
def create_forecasting_engine(db_manager):
    return SalesForecastingEngine(db_manager)

class KorraChatbot:
    # Existing methods...
    
    def handle_sales_forecast_request(self, user_id: str, message: str) -> Tuple[str, List[str]]:
        """Handle sales forecasting requests"""
        try:
            from .sales_forecasting import create_forecasting_engine
            forecasting_engine = create_forecasting_engine(self.db_manager)
            
            # Parse forecast period from message
            forecast_days = self._parse_forecast_period(message)
            
            # Generate forecast
            forecast_result = forecasting_engine.generate_forecast(user_id, forecast_days)
            
            if forecast_result["status"] == "insufficient_data":
                response = f"📊 *Sales Forecasting*\n\n{forecast_result['message']}\n\nTo get accurate forecasts, I need more sales data."
                suggestions = [
                    "➕ Add Sales Records",
                    "📤 Upload Sales File",
                    "💡 Learn About Forecasting",
                    "🔙 Main Menu"
                ]
                
            elif forecast_result["status"] == "error":
                response = f"❌ *Forecasting Error*\n\n{forecast_result['message']}"
                suggestions = ["🔄 Try Again", "📊 View Current Data", "🔙 Main Menu"]
                
            else:
                # Format successful forecast
                response = self._format_forecast_response(forecast_result)
                suggestions = [
                    "📈 Detailed Analysis",
                    "📊 Compare Methods",
                    "💡 Get Recommendations",
                    "🔙 Main Menu"
                ]
            
            return response, suggestions
            
        except Exception as e:
            logging.error(f"Error handling forecast request: {e}")
            response = "❌ Sorry, I couldn't generate your forecast right now. Please try again."
            suggestions = ["🔄 Try Again", "🔙 Main Menu"]
            return response, suggestions
    
    def _parse_forecast_period(self, message: str) -> int:
        """Parse forecast period from user message"""
        try:
            import re
            
            # Look for numbers followed by period indicators
            patterns = [
                r'(\d+)\s*days?',
                r'(\d+)\s*weeks?',
                r'(\d+)\s*months?',
                r'next\s+(\d+)',
                r'(\d+)'  # Just a number
            ]
            
            for pattern in patterns:
                match = re.search(pattern, message.lower())
                if match:
                    number = int(match.group(1))
                    
                    # Convert to days
                    if 'week' in pattern:
                        return min(number * 7, 90)
                    elif 'month' in pattern:
                        return min(number * 30, 90)
                    else:
                        return min(number, 90)
            
            # Default to 30 days
            return 30
            
        except Exception as e:
            logging.error(f"Error parsing forecast period: {e}")
            return 30
    
    def _format_forecast_response(self, forecast_result: Dict) -> str:
        """Format forecast results for WhatsApp display"""
        try:
            forecast = forecast_result.get("forecast", {})
            insights = forecast_result.get("insights", [])
            confidence = forecast_result.get("confidence", "Unknown")
            
            response = f"📈 *Sales Forecast* - {forecast_result.get('forecast_period', '')}\n\n"
            
            # Main forecast numbers
            total_forecast = forecast.get("total_forecast", 0)
            daily_average = forecast.get("average_daily", 0)
            method = forecast.get("method", "").replace("_", " ").title()
            
            response += f"💰 *Projected Revenue*: ${total_forecast:.2f}\n"
            response += f"📅 *Daily Average*: ${daily_average:.2f}\n"
            response += f"🔮 *Method*: {method}\n"
            response += f"🎯 *Confidence*: {confidence}\n\n"
            
            # Key insights
            if insights:
                response += "*Key Insights:*\n"
                for insight in insights[:3]:  # Show top 3
                    response += f"• {insight}\n"
            
            return response.strip()
            
        except Exception as e:
            logging.error(f"Error formatting forecast response: {e}")
            return "❌ Error formatting forecast data"
    
    def handle_forecast_comparison(self, user_id: str) -> Tuple[str, List[str]]:
        """Handle request to compare different forecasting methods"""
        try:
            from .sales_forecasting import create_forecasting_engine
            forecasting_engine = create_forecasting_engine(self.db_manager)
            
            # Generate forecast with all methods
            forecast_result = forecasting_engine.generate_forecast(user_id, 30)
            
            if forecast_result["status"] != "success":
                response = "❌ Could not generate forecast comparison. Please ensure you have enough sales data."
                suggestions = ["📊 View Current Data", "➕ Add More Data", "🔙 Main Menu"]
                return response, suggestions
            
            # Format comparison
            response = "📊 *Forecast Method Comparison* (30 days)\n\n"
            
            best_method = forecast_result.get("best_method", "")
            main_forecast = forecast_result.get("forecast", {})
            alternatives = forecast_result.get("alternative_forecasts", {})
            
            # Show best method first
            response += f"🏆 *Best: {best_method.replace('_', ' ').title()}*\n"
            response += f"   Revenue: ${main_forecast.get('total_forecast', 0):.2f}\n"
            response += f"   Daily: ${main_forecast.get('average_daily', 0):.2f}\n\n"
            
            # Show alternatives
            for method, forecast in alternatives.items():
                method_name = method.replace('_', ' ').title()
                response += f"📈 *{method_name}*\n"
                response += f"   Revenue: ${forecast.get('total_forecast', 0):.2f}\n"
                response += f"   Daily: ${forecast.get('average_daily', 0):.2f}\n\n"
            
            response += f"✅ *Recommendation*: Using {best_method.replace('_', ' ')} method for highest accuracy."
            
            suggestions = [
                "📈 Use Best Forecast",
                "🎯 Check Accuracy",
                "💡 Forecast Tips",
                "🔙 Main Menu"
            ]
            
            return response, suggestions
            
        except Exception as e:
            logging.error(f"Error handling forecast comparison: {e}")
            response = "❌ Sorry, I couldn't compare forecasting methods right now."
            suggestions = ["🔄 Try Again", "🔙 Main Menu"]
            return response, suggestions

    # Update the existing _generate_response method to handle forecasting
    def _generate_response(self, user_id: str, intent: str, message: str, user_name: str, user_session: Dict) -> Tuple[str, List[str]]:
        """Generate response based on intent with enhanced forecasting"""
        
        # Get user context for AI (now includes database history)
        user_context = user_session.get('context', {})
        user_context['name'] = user_name
        user_context['last_action'] = user_session.get('last_action')
        user_context['session_count'] = user_session.get('session_count', 1)
        
        # Add recent conversation context if available
        if self.db_enabled:
            recent_history = self.get_conversation_history(user_id, 5)
            if recent_history:
                user_context['recent_conversations'] = [
                    f"{conv['message_type']}: {conv['message'][:100]}" 
                    for conv in recent_history[-3:]  # Last 3 messages
                ]
        
        # Handle specific forecasting requests
        if intent == 'sales_forecast' or any(keyword in message.lower() for keyword in ['forecast', 'predict', 'projection']):
            return self.handle_sales_forecast_request(user_id, message)
        
        # Check for forecast comparison requests
        elif any(keyword in message.lower() for keyword in ['compare forecast', 'forecast comparison']):
            return self.handle_forecast_comparison(user_id)
        
        # Default response for other intents
        return super()._generate_response(user_id, intent, message, user_name, user_session)