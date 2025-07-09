import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

class SalesAnalytics:
    """Advanced sales analytics and insights"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def generate_business_insights(self, user_id: str, period_days: int = 30) -> Dict:
        """Generate comprehensive business insights"""
        try:
            from .sales_models import SalesDataManager
            sales_manager = SalesDataManager(self.db_manager)
            
            # Get sales summary
            summary = sales_manager.get_sales_summary(user_id, period_days)
            trends = sales_manager.detect_sales_trends(user_id)
            
            if not summary or summary.get("total_sales", 0) == 0:
                return {
                    "status": "no_data",
                    "message": f"No sales data found for the last {period_days} days",
                    "suggestions": [
                        "Add your first sales record",
                        "Upload sales data from spreadsheet",
                        "Start tracking daily sales"
                    ]
                }
            
            insights = {
                "period": f"Last {period_days} days",
                "summary": summary,
                "trends": trends,
                "insights": [],
                "recommendations": [],
                "alerts": []
            }
            
            # Generate insights
            insights["insights"] = self._generate_insights(summary, trends)
            insights["recommendations"] = self._generate_recommendations(summary, trends)
            insights["alerts"] = self._generate_alerts(summary, trends)
            
            return insights
            
        except Exception as e:
            logging.error(f"Error generating business insights: {e}")
            return {"status": "error", "message": f"Error generating insights: {str(e)}"}
    
    def _generate_insights(self, summary: Dict, trends: Dict) -> List[str]:
        """Generate business insights from data"""
        insights = []
        
        try:
            total_revenue = summary.get("total_revenue", 0)
            total_sales = summary.get("total_sales", 0)
            avg_order_value = summary.get("average_order_value", 0)
            top_products = summary.get("top_products", [])
            
            # Revenue insights
            if total_revenue > 0:
                insights.append(f"💰 Generated ${total_revenue:,.2f} in revenue from {total_sales} sales")
                insights.append(f"📊 Average order value is ${avg_order_value:.2f}")
            
            # Product insights
            if top_products:
                top_product = top_products[0]
                insights.append(f"🏆 Best seller: {top_product['name']} (${top_product['revenue']:.2f})")
                
                if len(top_products) >= 3:
                    top_3_revenue = sum(p['revenue'] for p in top_products[:3])
                    revenue_percentage = (top_3_revenue / total_revenue) * 100
                    insights.append(f"📈 Top 3 products account for {revenue_percentage:.1f}% of revenue")
            
            # Trend insights
            if trends:
                revenue_trend = trends.get("revenue_trend", {})
                if revenue_trend:
                    direction = revenue_trend["direction"]
                    change = revenue_trend["change_percent"]
                    if direction == "up":
                        insights.append(f"📈 Revenue is trending up by {change}% vs previous period")
                    else:
                        insights.append(f"📉 Revenue is down {abs(change)}% vs previous period")
                
                aov_trend = trends.get("aov_trend", {})
                if aov_trend:
                    direction = aov_trend["direction"]
                    change = aov_trend["change_percent"]
                    if direction == "up":
                        insights.append(f"💡 Customers are spending {change}% more per order")
                    else:
                        insights.append(f"⚠️ Average order value decreased by {abs(change)}%")
            
            # Daily performance insights
            daily_breakdown = summary.get("daily_breakdown", [])
            if len(daily_breakdown) >= 7:
                # Find best and worst days
                best_day = max(daily_breakdown, key=lambda x: x["revenue"])
                worst_day = min(daily_breakdown, key=lambda x: x["revenue"])
                
                insights.append(f"🌟 Best day: {best_day['date']} (${best_day['revenue']:.2f})")
                if worst_day["revenue"] > 0:
                    insights.append(f"📅 Consider improving performance on days like {worst_day['date']}")
            
        except Exception as e:
            logging.error(f"Error generating insights: {e}")
        
        return insights
    
    def _generate_recommendations(self, summary: Dict, trends: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        try:
            total_revenue = summary.get("total_revenue", 0)
            total_sales = summary.get("total_sales", 0)
            avg_order_value = summary.get("average_order_value", 0)
            top_products = summary.get("top_products", [])
            
            # Revenue-based recommendations
            if total_revenue < 1000:
                recommendations.append("🎯 Focus on increasing daily sales volume")
                recommendations.append("📱 Consider WhatsApp marketing to existing customers")
            
            # AOV recommendations
            if avg_order_value < 50:
                recommendations.append("📦 Try product bundling to increase order value")
                recommendations.append("💡 Offer upsells and cross-sells")
            
            # Product recommendations
            if len(top_products) > 0:
                top_product = top_products[0]
                recommendations.append(f"🚀 Promote your best seller: {top_product['name']}")
                
                if len(top_products) > 1:
                    recommendations.append("📊 Analyze why top products perform well")
            
            # Trend-based recommendations
            if trends:
                revenue_trend = trends.get("revenue_trend", {})
                if revenue_trend and revenue_trend["direction"] == "down":
                    recommendations.append("🔄 Review pricing strategy")
                    recommendations.append("👥 Implement customer retention programs")
                
                if revenue_trend and revenue_trend["direction"] == "up":
                    recommendations.append("⚡ Scale up marketing efforts")
                    recommendations.append("📈 Consider expanding successful product lines")
            
            # General recommendations
            recommendations.extend([
                "📊 Track daily sales consistently",
                "🎁 Create customer loyalty programs",
                "📸 Use high-quality product photos"
            ])
            
        except Exception as e:
            logging.error(f"Error generating recommendations: {e}")
        
        return recommendations[:8]  # Limit to 8 recommendations
    
    def _generate_alerts(self, summary: Dict, trends: Dict) -> List[str]:
        """Generate important alerts and warnings"""
        alerts = []
        
        try:
            # Trend alerts
            if trends:
                revenue_trend = trends.get("revenue_trend", {})
                if revenue_trend and revenue_trend["direction"] == "down":
                    change = abs(revenue_trend["change_percent"])
                    if change > 20:
                        alerts.append(f"🚨 Revenue dropped significantly by {change}%")
                    elif change > 10:
                        alerts.append(f"⚠️ Revenue declined by {change}% - monitor closely")
                
                sales_trend = trends.get("sales_count_trend", {})
                if sales_trend and sales_trend["direction"] == "down":
                    change = abs(sales_trend["change_percent"])
                    if change > 25:
                        alerts.append(f"📉 Sales volume down {change}% - action needed")
            
            # Low activity alerts
            total_sales = summary.get("total_sales", 0)
            if total_sales < 5:
                alerts.append("📊 Low sales activity - consider marketing boost")
            
            # AOV alerts
            avg_order_value = summary.get("average_order_value", 0)
            if avg_order_value < 20:
                alerts.append("💰 Low average order value - try bundling products")
            
        except Exception as e:
            logging.error(f"Error generating alerts: {e}")
        
        return alerts
    
    def compare_periods(self, user_id: str, current_days: int = 30, comparison_days: int = 30) -> Dict:
        """Compare two time periods"""
        try:
            from .sales_models import SalesDataManager
            sales_manager = SalesDataManager(self.db_manager)
            
            # Get current period data
            current_summary = sales_manager.get_sales_summary(user_id, current_days)
            
            # Get comparison period data
            start_date = datetime.utcnow() - timedelta(days=current_days + comparison_days)
            end_date = datetime.utcnow() - timedelta(days=current_days)
            comparison_summary = sales_manager.get_sales_summary_for_period(user_id, start_date, end_date)
            
            # Calculate comparisons
            comparison = {
                "current_period": f"Last {current_days} days",
                "comparison_period": f"Previous {comparison_days} days",
                "metrics": {}
            }
            
            metrics = ["total_revenue", "total_sales", "average_order_value"]
            
            for metric in metrics:
                current_value = current_summary.get(metric, 0)
                previous_value = comparison_summary.get(metric, 0)
                
                if previous_value > 0:
                    change_percent = ((current_value - previous_value) / previous_value) * 100
                    comparison["metrics"][metric] = {
                        "current": current_value,
                        "previous": previous_value,
                        "change_percent": round(change_percent, 1),
                        "direction": "up" if change_percent > 0 else "down"
                    }
                else:
                    comparison["metrics"][metric] = {
                        "current": current_value,
                        "previous": previous_value,
                        "change_percent": 0,
                        "direction": "neutral"
                    }
            
            return comparison
            
        except Exception as e:
            logging.error(f"Error comparing periods: {e}")
            return {"status": "error", "message": f"Error comparing periods: {str(e)}"}