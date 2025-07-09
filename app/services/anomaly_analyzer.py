from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from .anomaly_detection import StatisticalAnomalyDetector, Anomaly, AnomalySeverity, AnomalyType

class AnomalyAnalyzer:
    """High-level anomaly analysis and reporting service"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.detector = StatisticalAnomalyDetector(db_manager)
    
    def run_full_analysis(self, user_id: str, days_back: int = 30) -> Dict:
        """Run comprehensive anomaly analysis for user"""
        try:
            # Detect all anomalies
            anomalies = self.detector.detect_all_anomalies(user_id, days_back)
            
            if not anomalies:
                return {
                    "status": "no_anomalies",
                    "message": f"No anomalies detected in the last {days_back} days",
                    "summary": {
                        "total_anomalies": 0,
                        "critical_count": 0,
                        "high_count": 0,
                        "medium_count": 0,
                        "low_count": 0
                    },
                    "recommendations": [
                        "Continue monitoring your business metrics",
                        "Maintain consistent data entry",
                        "Review performance regularly"
                    ]
                }
            
            # Analyze and categorize anomalies
            analysis = self._analyze_anomalies(anomalies)
            
            # Generate insights and recommendations
            insights = self._generate_insights(anomalies)
            recommendations = self._generate_recommendations(anomalies)
            
            return {
                "status": "success",
                "summary": analysis,
                "anomalies": self._format_anomalies_for_display(anomalies[:10]),  # Top 10
                "insights": insights,
                "recommendations": recommendations,
                "analysis_period": f"Last {days_back} days",
                "analysis_date": datetime.utcnow()
            }
            
        except Exception as e:
            logging.error(f"Error running anomaly analysis: {e}")
            return {
                "status": "error",
                "message": f"Error running analysis: {str(e)}"
            }
    
    def get_anomaly_alerts(self, user_id: str) -> Dict:
        """Get critical anomaly alerts that need immediate attention"""
        try:
            # Get recent critical and high severity anomalies
            critical_anomalies = []
            recent_anomalies = self.detector.get_user_anomalies(user_id, status="new", limit=50)
            
            for anomaly in recent_anomalies:
                if anomaly.severity in [AnomalySeverity.CRITICAL, AnomalySeverity.HIGH]:
                    # Check if it's recent (within last 7 days)
                    days_ago = (datetime.utcnow() - anomaly.date).days
                    if days_ago <= 7:
                        critical_anomalies.append(anomaly)
            
            if not critical_anomalies:
                return {
                    "status": "no_alerts",
                    "message": "No critical anomalies requiring immediate attention",
                    "alert_count": 0
                }
            
            # Format alerts
            alerts = []
            for anomaly in critical_anomalies[:5]:  # Top 5 most critical
                days_ago = (datetime.utcnow() - anomaly.date).days
                alert = {
                    "id": anomaly.id,
                    "severity": anomaly.severity.value,
                    "type": anomaly.type.value,
                    "description": anomaly.description,
                    "days_ago": days_ago,
                    "confidence": anomaly.confidence,
                    "immediate_actions": anomaly.suggestions[:2]  # Top 2 suggestions
                }
                alerts.append(alert)
            
            return {
                "status": "alerts_found",
                "alert_count": len(critical_anomalies),
                "alerts": alerts,
                "summary_message": f"Found {len(critical_anomalies)} critical issues requiring attention"
            }
            
        except Exception as e:
            logging.error(f"Error getting anomaly alerts: {e}")
            return {
                "status": "error",
                "message": f"Error getting alerts: {str(e)}"
            }
    
    def explain_anomaly(self, user_id: str, anomaly_id: str) -> Dict:
        """Provide detailed explanation of a specific anomaly"""
        try:
            # Get the specific anomaly
            anomalies = self.detector.get_user_anomalies(user_id, limit=100)
            target_anomaly = None
            
            for anomaly in anomalies:
                if anomaly.id == anomaly_id:
                    target_anomaly = anomaly
                    break
            
            if not target_anomaly:
                return {
                    "status": "not_found",
                    "message": "Anomaly not found"
                }
            
            # Generate detailed explanation
            explanation = self._generate_detailed_explanation(target_anomaly)
            
            return {
                "status": "success",
                "anomaly": {
                    "id": target_anomaly.id,
                    "type": target_anomaly.type.value,
                    "severity": target_anomaly.severity.value,
                    "date": target_anomaly.date.strftime("%Y-%m-%d"),
                    "description": target_anomaly.description,
                    "confidence": target_anomaly.confidence
                },
                "explanation": explanation,
                "recommendations": target_anomaly.suggestions,
                "technical_details": target_anomaly.metadata
            }
            
        except Exception as e:
            logging.error(f"Error explaining anomaly: {e}")
            return {
                "status": "error",
                "message": f"Error explaining anomaly: {str(e)}"
            }
    
    def _analyze_anomalies(self, anomalies: List[Anomaly]) -> Dict:
        """Analyze and categorize anomalies"""
        analysis = {
            "total_anomalies": len(anomalies),
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "by_type": {},
            "by_impact": {"positive": 0, "negative": 0},
            "most_recent": None,
            "highest_severity": None
        }
        
        try:
            for anomaly in anomalies:
                # Count by severity
                if anomaly.severity == AnomalySeverity.CRITICAL:
                    analysis["critical_count"] += 1
                elif anomaly.severity == AnomalySeverity.HIGH:
                    analysis["high_count"] += 1
                elif anomaly.severity == AnomalySeverity.MEDIUM:
                    analysis["medium_count"] += 1
                else:
                    analysis["low_count"] += 1
                
                # Count by type
                type_name = anomaly.type.value
                analysis["by_type"][type_name] = analysis["by_type"].get(type_name, 0) + 1
                
                # Count by impact
                if anomaly.impact in analysis["by_impact"]:
                    analysis["by_impact"][anomaly.impact] += 1
            
            # Find most recent and highest severity
            if anomalies:
                analysis["most_recent"] = max(anomalies, key=lambda x: x.date)
                analysis["highest_severity"] = max(anomalies, key=lambda x: x.deviation_score)
            
        except Exception as e:
            logging.error(f"Error analyzing anomalies: {e}")
        
        return analysis
    
    def _generate_insights(self, anomalies: List[Anomaly]) -> List[str]:
        """Generate business insights from anomalies"""
        insights = []
        
        try:
            if not anomalies:
                return insights
            
            # Severity insights
            critical_count = sum(1 for a in anomalies if a.severity == AnomalySeverity.CRITICAL)
            high_count = sum(1 for a in anomalies if a.severity == AnomalySeverity.HIGH)
            
            if critical_count > 0:
                insights.append(f"🚨 {critical_count} critical issues detected requiring immediate action")
            
            if high_count > 0:
                insights.append(f"⚠️ {high_count} high-priority issues need attention")
            
            # Type insights
            type_counts = {}
            for anomaly in anomalies:
                type_name = anomaly.type.value
                type_counts[type_name] = type_counts.get(type_name, 0) + 1
            
            most_common_type = max(type_counts.items(), key=lambda x: x[1])
            if most_common_type[1] > 1:
                insights.append(f"📊 Most common issue: {most_common_type[0]} ({most_common_type[1]} occurrences)")
            
            # Impact insights
            negative_count = sum(1 for a in anomalies if a.impact == "negative")
            positive_count = sum(1 for a in anomalies if a.impact == "positive")
            
            if negative_count > positive_count:
                insights.append(f"📉 {negative_count} negative anomalies vs {positive_count} positive ones")
            elif positive_count > negative_count:
                insights.append(f"📈 {positive_count} positive anomalies vs {negative_count} negative ones")
            
            # Recent activity insights
            recent_anomalies = [a for a in anomalies if (datetime.utcnow() - a.date).days <= 3]
            if len(recent_anomalies) > 3:
                insights.append(f"⚡ {len(recent_anomalies)} anomalies detected in the last 3 days")
            
            # Confidence insights
            high_confidence = [a for a in anomalies if a.confidence > 0.8]
            if len(high_confidence) > 0:
                insights.append(f"🎯 {len(high_confidence)} anomalies have high confidence (>80%)")
            
        except Exception as e:
            logging.error(f"Error generating insights: {e}")
        
        return insights[:6]  # Limit to 6 insights
    
    def _generate_recommendations(self, anomalies: List[Anomaly]) -> List[str]:
        """Generate actionable recommendations based on anomalies"""
        recommendations = []
        
        try:
            if not anomalies:
                return recommendations
            
            # Priority recommendations based on critical issues
            critical_anomalies = [a for a in anomalies if a.severity == AnomalySeverity.CRITICAL]
            
            if critical_anomalies:
                recommendations.append("🚨 Address critical issues immediately - review business operations")
                
                # Get unique suggestions from critical anomalies
                critical_suggestions = set()
                for anomaly in critical_anomalies:
                    critical_suggestions.update(anomaly.suggestions[:2])
                
                recommendations.extend(list(critical_suggestions)[:3])
            
            # Recommendations based on patterns
            revenue_anomalies = [a for a in anomalies if a.type == AnomalyType.REVENUE_ANOMALY]
            sales_anomalies = [a for a in anomalies if a.type in [AnomalyType.SALES_DROP, AnomalyType.SALES_SPIKE]]
            product_anomalies = [a for a in anomalies if a.type == AnomalyType.PRODUCT_ANOMALY]
            
            if len(revenue_anomalies) > 2:
                recommendations.append("💰 Review pricing and revenue strategies - multiple revenue anomalies detected")
            
            if len(sales_anomalies) > 2:
                recommendations.append("📊 Analyze sales patterns and external factors affecting volume")
            
            if len(product_anomalies) > 1:
                recommendations.append("🛍️ Conduct comprehensive product performance review")
            
            # General recommendations
            negative_anomalies = [a for a in anomalies if a.impact == "negative"]
            if len(negative_anomalies) > len(anomalies) // 2:
                recommendations.extend([
                    "📈 Focus on corrective actions to reverse negative trends",
                    "🔍 Investigate root causes of performance issues"
                ])
            
            # Monitoring recommendations
            recommendations.extend([
                "📊 Increase monitoring frequency for early detection",
                "📝 Document resolution actions for future reference"
            ])
            
        except Exception as e:
            logging.error(f"Error generating recommendations: {e}")
        
        return recommendations[:8]  # Limit to 8 recommendations
    
    def _format_anomalies_for_display(self, anomalies: List[Anomaly]) -> List[Dict]:
        """Format anomalies for user-friendly display"""
        formatted = []
        
        try:
            for anomaly in anomalies:
                days_ago = (datetime.utcnow() - anomaly.date).days
                
                formatted_anomaly = {
                    "id": anomaly.id,
                    "type": anomaly.type.value.replace("_", " ").title(),
                    "severity": anomaly.severity.value.upper(),
                    "description": anomaly.description,
                    "days_ago": days_ago,
                    "date": anomaly.date.strftime("%Y-%m-%d"),
                    "impact": anomaly.impact,
                    "confidence": f"{anomaly.confidence:.1%}",
                    "deviation_score": round(anomaly.deviation_score, 2),
                    "top_suggestions": anomaly.suggestions[:2]
                }
                
                formatted.append(formatted_anomaly)
                
        except Exception as e:
            logging.error(f"Error formatting anomalies: {e}")
        
        return formatted
    
    def _generate_detailed_explanation(self, anomaly: Anomaly) -> Dict:
        """Generate detailed explanation for a specific anomaly"""
        explanation = {
            "what_happened": "",
            "why_detected": "",
            "business_impact": "",
            "next_steps": []
        }
        
        try:
            # What happened
            if anomaly.type == AnomalyType.SALES_DROP:
                explanation["what_happened"] = f"Sales volume dropped significantly to {anomaly.value} on {anomaly.date.strftime('%Y-%m-%d')}, which is {anomaly.deviation_score:.1f} standard deviations below normal."
            elif anomaly.type == AnomalyType.SALES_SPIKE:
                explanation["what_happened"] = f"Sales volume spiked unusually to {anomaly.value} on {anomaly.date.strftime('%Y-%m-%d')}, which is {anomaly.deviation_score:.1f} standard deviations above normal."
            elif anomaly.type == AnomalyType.REVENUE_ANOMALY:
                explanation["what_happened"] = f"Revenue deviated significantly to ${anomaly.value:.2f}, compared to expected ${anomaly.expected_value:.2f}."
            elif anomaly.type == AnomalyType.PRODUCT_ANOMALY:
                product_name = anomaly.metadata.get("product_name", "Unknown")
                explanation["what_happened"] = f"Product '{product_name}' showed unusual performance patterns compared to other products."
            elif anomaly.type == AnomalyType.PATTERN_BREAK:
                day_name = anomaly.metadata.get("day_name", "Unknown")
                explanation["what_happened"] = f"Normal {day_name} sales patterns were significantly different from expected."
            elif anomaly.type == AnomalyType.TREND_REVERSAL:
                direction = anomaly.metadata.get("trend_direction", "unknown")
                explanation["what_happened"] = f"A significant trend reversal was detected, with sales moving {direction}ward."
            
            # Why detected
            explanation["why_detected"] = f"This anomaly was detected using statistical analysis with {anomaly.confidence:.1%} confidence. The deviation score of {anomaly.deviation_score:.2f} indicates this is a statistically significant outlier."
            
            # Business impact
            if anomaly.impact == "negative":
                explanation["business_impact"] = "This anomaly indicates a potential issue that could affect business performance if not addressed."
            else:
                explanation["business_impact"] = "This anomaly represents a positive deviation that could indicate successful strategies worth replicating."
            
            # Next steps
            explanation["next_steps"] = anomaly.suggestions
            
        except Exception as e:
            logging.error(f"Error generating detailed explanation: {e}")
        
        return explanation

# Initialize anomaly analyzer
def create_anomaly_analyzer(db_manager):
    return AnomalyAnalyzer(db_manager)