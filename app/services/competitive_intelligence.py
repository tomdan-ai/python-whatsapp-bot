import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

class CompetitiveIntelligence:
    """Market analysis and competitive intelligence service"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        # Industry benchmarks (can be updated with real market data)
        self.industry_benchmarks = {
            "retail": {
                "avg_order_value": 45.0,
                "customer_retention_rate": 0.65,
                "gross_margin": 0.40,
                "inventory_turnover": 6.0
            },
            "food_service": {
                "avg_order_value": 25.0,
                "customer_retention_rate": 0.55,
                "gross_margin": 0.60,
                "inventory_turnover": 12.0
            },invoice_service = InvoiceService()
            "services": {
                "avg_order_value": 150.0,
                "customer_retention_rate": 0.75,
                "gross_margin": 0.70,
                "inventory_turnover": 4.0
            },
            "general": {
                "avg_order_value": 60.0,
                "customer_retention_rate": 0.60,
                "gross_margin": 0.50,
                "inventory_turnover": 8.0
            }
        }
    
    def run_competitive_analysis(self, user_id: str, industry: str = "general") -> Dict:
        """Run comprehensive competitive analysis"""
        try:
            # Get user's business data
            from .advanced_analytics import create_advanced_analytics
            analytics = create_advanced_analytics(self.db_manager)
            
            user_analysis = analytics.run_comprehensive_analysis(user_id, 90)
            
            if user_analysis.get("status") != "success":
                return {
                    "status": "insufficient_data",
                    "message": "Need more business data for competitive analysis"
                }
            
            # Get industry benchmarks
            benchmarks = self.industry_benchmarks.get(industry, self.industry_benchmarks["general"])
            
            # Calculate user metrics
            user_metrics = self._extract_user_metrics(user_analysis)
            
            # Performance comparison
            comparison = self._compare_with_benchmarks(user_metrics, benchmarks)
            
            # Market positioning
            positioning = self._analyze_market_positioning(user_metrics, benchmarks)
            
            # Growth opportunities
            opportunities = self._identify_growth_opportunities(comparison, user_metrics)
            
            # Competitive recommendations
            recommendations = self._generate_competitive_recommendations(comparison, positioning)
            
            return {
                "status": "success",
                "industry": industry,
                "user_metrics": user_metrics,
                "industry_benchmarks": benchmarks,
                "performance_comparison": comparison,
                "market_positioning": positioning,
                "growth_opportunities": opportunities,
                "competitive_recommendations": recommendations,
                "competitive_score": self._calculate_competitive_score(comparison)
            }
            
        except Exception as e:
            logging.error(f"Error in competitive analysis: {e}")
            return {"status": "error", "message": str(e)}
    
    def analyze_market_trends(self, user_id: str, days_back: int = 180) -> Dict:
        """Analyze market trends and business trajectory"""
        try:
            from .sales_models import SalesDataManager
            sales_manager = SalesDataManager(self.db_manager)
            
            # Get extended historical data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            sales_data = sales_manager.get_sales_data(user_id, start_date, end_date, limit=2000)
            
            if len(sales_data) < 20:
                return {"status": "insufficient_data", "message": "Need more historical data"}
            
            df = pd.DataFrame(sales_data)
            df['date'] = pd.to_datetime(df['date'])
            df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce')
            
            # Monthly trend analysis
            monthly_trends = self._analyze_monthly_trends(df)
            
            # Seasonal patterns
            seasonal_analysis = self._analyze_seasonal_patterns(df)
            
            # Growth trajectory
            growth_trajectory = self._analyze_growth_trajectory(df)
            
            # Market signals
            market_signals = self._detect_market_signals(df, monthly_trends)
            
            return {
                "status": "success",
                "monthly_trends": monthly_trends,
                "seasonal_patterns": seasonal_analysis,
                "growth_trajectory": growth_trajectory,
                "market_signals": market_signals,
                "trend_insights": self._generate_trend_insights(monthly_trends, growth_trajectory)
            }
            
        except Exception as e:
            logging.error(f"Error analyzing market trends: {e}")
            return {"status": "error", "message": str(e)}
    
    def benchmark_performance(self, user_id: str, metrics: List[str] = None) -> Dict:
        """Detailed performance benchmarking"""
        try:
            if metrics is None:
                metrics = ["avg_order_value", "customer_retention_rate", "gross_margin"]
            
            # Get user performance data
            from .advanced_analytics import create_advanced_analytics
            analytics = create_advanced_analytics(self.db_manager)
            user_analysis = analytics.run_comprehensive_analysis(user_id, 90)
            
            if user_analysis.get("status") != "success":
                return {"status": "insufficient_data"}
            
            user_metrics = self._extract_user_metrics(user_analysis)
            
            # Benchmark against multiple industries
            benchmark_results = {}
            
            for industry, benchmarks in self.industry_benchmarks.items():
                industry_comparison = {}
                
                for metric in metrics:
                    if metric in user_metrics and metric in benchmarks:
                        user_value = user_metrics[metric]
                        benchmark_value = benchmarks[metric]
                        
                        performance_ratio = user_value / benchmark_value if benchmark_value > 0 else 0
                        
                        industry_comparison[metric] = {
                            "user_value": user_value,
                            "benchmark_value": benchmark_value,
                            "performance_ratio": performance_ratio,
                            "status": "above" if performance_ratio > 1.1 else "below" if performance_ratio < 0.9 else "on_par"
                        }
                
                benchmark_results[industry] = industry_comparison
            
            # Find best-fit industry
            best_fit_industry = self._find_best_fit_industry(user_metrics)
            
            return {
                "status": "success",
                "benchmark_results": benchmark_results,
                "best_fit_industry": best_fit_industry,
                "overall_performance": self._calculate_overall_performance(benchmark_results),
                "improvement_areas": self._identify_improvement_areas(benchmark_results)
            }
            
        except Exception as e:
            logging.error(f"Error in performance benchmarking: {e}")
            return {"status": "error", "message": str(e)}
    
    def _extract_user_metrics(self, user_analysis: Dict) -> Dict:
        """Extract key metrics from user analysis"""
        try:
            performance_metrics = user_analysis.get("performance_metrics", {})
            customer_analysis = user_analysis.get("customer_analysis", {})
            revenue_analysis = user_analysis.get("revenue_analysis", {})
            
            metrics = {
                "avg_order_value": performance_metrics.get("avg_order_value", 0),
                "total_revenue": performance_metrics.get("total_revenue", 0),
                "total_customers": customer_analysis.get("total_customers", 0),
                "customer_retention_rate": self._estimate_retention_rate(customer_analysis),
                "gross_margin": 0.45,  # Default estimate - would be calculated from cost data
                "inventory_turnover": 6.0,  # Default estimate
                "revenue_per_customer": performance_metrics.get("revenue_per_customer", 0)
            }
            
            return metrics
            
        except Exception as e:
            logging.error(f"Error extracting user metrics: {e}")
            return {}
    
    def _compare_with_benchmarks(self, user_metrics: Dict, benchmarks: Dict) -> Dict:
        """Compare user metrics with industry benchmarks"""
        comparison = {}
        
        try:
            for metric, benchmark_value in benchmarks.items():
                if metric in user_metrics:
                    user_value = user_metrics[metric]
                    
                    if benchmark_value > 0:
                        performance_ratio = user_value / benchmark_value
                        variance_percent = ((user_value - benchmark_value) / benchmark_value) * 100
                        
                        comparison[metric] = {
                            "user_value": user_value,
                            "benchmark_value": benchmark_value,
                            "performance_ratio": performance_ratio,
                            "variance_percent": variance_percent,
                            "status": self._get_performance_status(performance_ratio),
                            "interpretation": self._interpret_performance(metric, performance_ratio)
                        }
            
        except Exception as e:
            logging.error(f"Error comparing with benchmarks: {e}")
        
        return comparison
    
    def _analyze_market_positioning(self, user_metrics: Dict, benchmarks: Dict) -> Dict:
        """Analyze market positioning based on performance"""
        try:
            # Calculate overall performance score
            performance_scores = []
            
            for metric, benchmark_value in benchmarks.items():
                if metric in user_metrics and benchmark_value > 0:
                    ratio = user_metrics[metric] / benchmark_value
                    performance_scores.append(min(2.0, ratio))  # Cap at 2x benchmark
            
            avg_performance = np.mean(performance_scores) if performance_scores else 1.0
            
            # Determine market position
            if avg_performance >= 1.3:
                position = "Market Leader"
                description = "Significantly outperforming industry standards"
            elif avg_performance >= 1.1:
                position = "Strong Performer"
                description = "Above industry average with competitive advantages"
            elif avg_performance >= 0.9:
                position = "Market Average"
                description = "Performing in line with industry standards"
            elif avg_performance >= 0.7:
                position = "Below Average"
                description = "Underperforming compared to industry standards"
            else:
                position = "Needs Improvement"
                description = "Significantly below industry performance"
            
            # Identify key strengths and weaknesses
            strengths = []
            weaknesses = []
            
            for metric, benchmark_value in benchmarks.items():
                if metric in user_metrics and benchmark_value > 0:
                    ratio = user_metrics[metric] / benchmark_value
                    if ratio >= 1.2:
                        strengths.append(metric.replace("_", " ").title())
                    elif ratio <= 0.8:
                        weaknesses.append(metric.replace("_", " ").title())
            
            return {
                "market_position": position,
                "description": description,
                "performance_score": round(avg_performance, 2),
                "key_strengths": strengths,
                "key_weaknesses": weaknesses,
                "competitive_advantages": self._identify_competitive_advantages(user_metrics, benchmarks)
            }
            
        except Exception as e:
            logging.error(f"Error analyzing market positioning: {e}")
            return {}
    
    def _identify_growth_opportunities(self, comparison: Dict, user_metrics: Dict) -> List[Dict]:
        """Identify specific growth opportunities"""
        opportunities = []
        
        try:
            # Revenue optimization opportunities
            aov_comparison = comparison.get("avg_order_value", {})
            if aov_comparison.get("performance_ratio", 1) < 0.9:
                revenue_upside = (aov_comparison["benchmark_value"] - aov_comparison["user_value"]) * user_metrics.get("total_customers", 0)
                opportunities.append({
                    "type": "Revenue Optimization",
                    "area": "Average Order Value",
                    "potential_impact": f"${revenue_upside:,.0f}" if revenue_upside > 0 else "High",
                    "description": "Increase average order value through upselling and bundling",
                    "priority": "High" if aov_comparison.get("performance_ratio", 1) < 0.8 else "Medium"
                })
            
            # Customer retention opportunities
            retention_comparison = comparison.get("customer_retention_rate", {})
            if retention_comparison.get("performance_ratio", 1) < 0.9:
                opportunities.append({
                    "type": "Customer Retention",
                    "area": "Loyalty Programs",
                    "potential_impact": "High",
                    "description": "Implement customer retention strategies to reduce churn",
                    "priority": "High"
                })
            
            # Market expansion opportunities
            if user_metrics.get("total_customers", 0) < 100:
                opportunities.append({
                    "type": "Market Expansion",
                    "area": "Customer Acquisition",
                    "potential_impact": "Very High",
                    "description": "Focus on customer acquisition to scale business",
                    "priority": "High"
                })
            
            # Operational efficiency opportunities
            margin_comparison = comparison.get("gross_margin", {})
            if margin_comparison.get("performance_ratio", 1) < 0.9:
                opportunities.append({
                    "type": "Operational Efficiency",
                    "area": "Cost Management",
                    "potential_impact": "Medium",
                    "description": "Optimize costs and improve profit margins",
                    "priority": "Medium"
                })
            
        except Exception as e:
            logging.error(f"Error identifying growth opportunities: {e}")
        
        return opportunities[:6]  # Return top 6 opportunities
    
    def _generate_competitive_recommendations(self, comparison: Dict, positioning: Dict) -> List[str]:
        """Generate competitive strategy recommendations"""
        recommendations = []
        
        try:
            position = positioning.get("market_position", "")
            weaknesses = positioning.get("key_weaknesses", [])
            strengths = positioning.get("key_strengths", [])
            
            # Position-based recommendations
            if position == "Market Leader":
                recommendations.extend([
                    "Maintain competitive advantages and market share",
                    "Invest in innovation to stay ahead of competitors",
                    "Consider market expansion opportunities"
                ])
            elif position == "Strong Performer":
                recommendations.extend([
                    "Leverage strengths to gain market share",
                    "Identify and address remaining weaknesses",
                    "Monitor competitors for emerging threats"
                ])
            elif position in ["Below Average", "Needs Improvement"]:
                recommendations.extend([
                    "Focus on fundamental business improvements",
                    "Study successful competitors and best practices",
                    "Prioritize addressing critical weaknesses"
                ])
            
            # Weakness-based recommendations
            if "Avg Order Value" in weaknesses:
                recommendations.append("Implement upselling and cross-selling strategies")
            if "Customer Retention Rate" in weaknesses:
                recommendations.append("Develop customer loyalty and retention programs")
            if "Gross Margin" in weaknesses:
                recommendations.append("Optimize pricing and cost structure")
            
            # Strength-based recommendations
            if strengths:
                recommendations.append(f"Leverage your strength in {strengths[0]} for competitive advantage")
            
            # Performance gap recommendations
            for metric, data in comparison.items():
                if data.get("performance_ratio", 1) < 0.7:  # Significant underperformance
                    recommendations.append(f"Critical: Address {metric.replace('_', ' ')} performance gap")
            
        except Exception as e:
            logging.error(f"Error generating competitive recommendations: {e}")
        
        return recommendations[:8]
    
    def _calculate_competitive_score(self, comparison: Dict) -> Dict:
        """Calculate overall competitive score"""
        try:
            scores = []
            for metric, data in comparison.items():
                ratio = data.get("performance_ratio", 1)
                # Convert ratio to score (0-100)
                score = min(100, ratio * 50)  # 2x benchmark = 100 points
                scores.append(score)
            
            overall_score = np.mean(scores) if scores else 50
            
            # Determine grade
            if overall_score >= 80:
                grade = "A"
                description = "Excellent competitive position"
            elif overall_score >= 70:
                grade = "B"
                description = "Good competitive position"
            elif overall_score >= 60:
                grade = "C"
                description = "Average competitive position"
            elif overall_score >= 50:
                grade = "D"
                description = "Below average competitive position"
            else:
                grade = "F"
                description = "Poor competitive position"
            
            return {
                "overall_score": round(overall_score, 1),
                "grade": grade,
                "description": description,
                "metric_scores": {metric: min(100, data.get("performance_ratio", 1) * 50) for metric, data in comparison.items()}
            }
            
        except Exception as e:
            logging.error(f"Error calculating competitive score: {e}")
            return {"overall_score": 50, "grade": "C", "description": "Average"}

# Initialize competitive intelligence
def create_competitive_intelligence(db_manager):
    return CompetitiveIntelligence(db_manager)