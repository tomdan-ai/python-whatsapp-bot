import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum
import json

class CustomerSegment(Enum):
    VIP = "vip"
    LOYAL = "loyal" 
    REGULAR = "regular"
    NEW = "new"
    AT_RISK = "at_risk"
    DORMANT = "dormant"

class ProductTier(Enum):
    STAR = "star"           # High revenue, high frequency
    CASH_COW = "cash_cow"   # High revenue, low frequency
    POTENTIAL = "potential"  # Low revenue, high frequency  
    DOG = "dog"             # Low revenue, low frequency

@dataclass
class CustomerInsight:
    customer_name: str
    segment: CustomerSegment
    total_revenue: float
    purchase_frequency: int
    avg_order_value: float
    last_purchase_days: int
    lifetime_value: float
    churn_risk: float
    recommendations: List[str]

@dataclass
class ProductInsight:
    product_name: str
    tier: ProductTier
    total_revenue: float
    sales_count: int
    profit_margin: float
    growth_rate: float
    market_share: float
    recommendations: List[str]

class AdvancedAnalytics:
    """Advanced business analytics and customer intelligence"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
    def run_comprehensive_analysis(self, user_id: str, days_back: int = 90) -> Dict:
        """Run comprehensive business intelligence analysis"""
        try:
            # Get sales data
            sales_data = self._get_sales_data(user_id, days_back)
            
            if not sales_data:
                return {
                    "status": "insufficient_data",
                    "message": "Not enough data for comprehensive analysis",
                    "minimum_required": "At least 10 sales records needed"
                }
            
            df = self._prepare_dataframe(sales_data)
            
            # Run all analyses
            analysis_results = {
                "status": "success",
                "analysis_date": datetime.utcnow(),
                "period": f"Last {days_back} days",
                "data_summary": self._generate_data_summary(df),
                "customer_analysis": self._analyze_customers(df),
                "product_analysis": self._analyze_products(df),
                "revenue_analysis": self._analyze_revenue_drivers(df),
                "growth_analysis": self._analyze_growth_opportunities(df),
                "performance_metrics": self._calculate_performance_metrics(df),
                "strategic_insights": [],
                "action_items": []
            }
            
            # Generate strategic insights
            analysis_results["strategic_insights"] = self._generate_strategic_insights(analysis_results)
            analysis_results["action_items"] = self._generate_action_items(analysis_results)
            
            return analysis_results
            
        except Exception as e:
            logging.error(f"Error in comprehensive analysis: {e}")
            return {
                "status": "error",
                "message": f"Analysis failed: {str(e)}"
            }
    
    def analyze_customer_segmentation(self, user_id: str, days_back: int = 90) -> Dict:
        """Detailed customer segmentation analysis"""
        try:
            sales_data = self._get_sales_data(user_id, days_back)
            
            if not sales_data:
                return {"status": "no_data", "message": "No customer data available"}
            
            df = self._prepare_dataframe(sales_data)
            
            # Customer metrics
            customer_metrics = df.groupby('customer_name').agg({
                'total_amount': ['sum', 'count', 'mean'],
                'date': ['min', 'max']
            }).round(2)
            
            # Flatten column names
            customer_metrics.columns = ['total_revenue', 'purchase_count', 'avg_order_value', 'first_purchase', 'last_purchase']
            customer_metrics = customer_metrics.reset_index()
            
            # Calculate additional metrics
            current_date = datetime.utcnow()
            customer_metrics['days_since_last_purchase'] = (current_date - pd.to_datetime(customer_metrics['last_purchase'])).dt.days
            customer_metrics['customer_lifespan'] = (pd.to_datetime(customer_metrics['last_purchase']) - pd.to_datetime(customer_metrics['first_purchase'])).dt.days + 1
            customer_metrics['purchase_frequency'] = customer_metrics['purchase_count'] / (customer_metrics['customer_lifespan'] / 30)  # purchases per month
            
            # Segment customers
            customer_insights = []
            
            for _, customer in customer_metrics.iterrows():
                insight = self._segment_customer(customer, df)
                customer_insights.append(insight)
            
            # Sort by value
            customer_insights.sort(key=lambda x: x.total_revenue, reverse=True)
            
            # Generate segment summary
            segment_summary = self._generate_segment_summary(customer_insights)
            
            return {
                "status": "success",
                "total_customers": len(customer_insights),
                "segment_summary": segment_summary,
                "top_customers": [self._format_customer_insight(c) for c in customer_insights[:10]],
                "segmentation_insights": self._generate_segmentation_insights(customer_insights),
                "retention_metrics": self._calculate_retention_metrics(customer_metrics)
            }
            
        except Exception as e:
            logging.error(f"Error in customer segmentation: {e}")
            return {"status": "error", "message": str(e)}
    
    def analyze_product_performance(self, user_id: str, days_back: int = 90) -> Dict:
        """Comprehensive product performance analysis"""
        try:
            sales_data = self._get_sales_data(user_id, days_back)
            
            if not sales_data:
                return {"status": "no_data", "message": "No product data available"}
            
            df = self._prepare_dataframe(sales_data)
            
            # Product metrics
            product_metrics = df.groupby('product_name').agg({
                'total_amount': ['sum', 'count', 'mean'],
                'quantity': 'sum',
                'unit_price': 'mean'
            }).round(2)
            
            # Flatten columns
            product_metrics.columns = ['total_revenue', 'sales_count', 'avg_sale_value', 'total_quantity', 'avg_price']
            product_metrics = product_metrics.reset_index()
            
            # Calculate performance metrics
            total_revenue = product_metrics['total_revenue'].sum()
            total_sales = product_metrics['sales_count'].sum()
            
            product_metrics['revenue_share'] = (product_metrics['total_revenue'] / total_revenue * 100).round(1)
            product_metrics['sales_share'] = (product_metrics['sales_count'] / total_sales * 100).round(1)
            
            # Calculate growth rates (compare first half vs second half of period)
            product_metrics['growth_rate'] = product_metrics.apply(
                lambda row: self._calculate_product_growth(df, row['product_name'], days_back), axis=1
            )
            
            # Classify products into performance tiers
            product_insights = []
            
            for _, product in product_metrics.iterrows():
                insight = self._classify_product_performance(product, product_metrics)
                product_insights.append(insight)
            
            # Sort by revenue
            product_insights.sort(key=lambda x: x.total_revenue, reverse=True)
            
            # Generate performance matrix
            performance_matrix = self._generate_product_matrix(product_insights)
            
            return {
                "status": "success",
                "total_products": len(product_insights),
                "performance_matrix": performance_matrix,
                "top_performers": [self._format_product_insight(p) for p in product_insights[:10]],
                "product_insights": self._generate_product_insights(product_insights),
                "optimization_opportunities": self._identify_optimization_opportunities(product_insights)
            }
            
        except Exception as e:
            logging.error(f"Error in product performance analysis: {e}")
            return {"status": "error", "message": str(e)}
    
    def identify_revenue_drivers(self, user_id: str, days_back: int = 90) -> Dict:
        """Identify key revenue drivers and patterns"""
        try:
            sales_data = self._get_sales_data(user_id, days_back)
            
            if not sales_data:
                return {"status": "no_data", "message": "No data for revenue analysis"}
            
            df = self._prepare_dataframe(sales_data)
            
            # Revenue by different dimensions
            drivers = {
                "temporal_drivers": self._analyze_temporal_patterns(df),
                "product_drivers": self._analyze_product_revenue_contribution(df),
                "customer_drivers": self._analyze_customer_revenue_contribution(df),
                "price_drivers": self._analyze_pricing_impact(df),
                "volume_drivers": self._analyze_volume_impact(df)
            }
            
            # Identify primary drivers
            primary_drivers = self._identify_primary_drivers(drivers, df)
            
            # Generate recommendations
            recommendations = self._generate_revenue_recommendations(drivers, primary_drivers)
            
            return {
                "status": "success",
                "revenue_drivers": drivers,
                "primary_drivers": primary_drivers,
                "total_revenue": float(df['total_amount'].sum()),
                "revenue_insights": self._generate_revenue_insights(drivers),
                "recommendations": recommendations
            }
            
        except Exception as e:
            logging.error(f"Error identifying revenue drivers: {e}")
            return {"status": "error", "message": str(e)}
    
    def _get_sales_data(self, user_id: str, days_back: int) -> List[Dict]:
        """Get sales data for analysis"""
        try:
            from .sales_models import SalesDataManager
            sales_manager = SalesDataManager(self.db_manager)
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            return sales_manager.get_sales_data(user_id, start_date, end_date, limit=2000)
            
        except Exception as e:
            logging.error(f"Error getting sales data: {e}")
            return []
    
    def _prepare_dataframe(self, sales_data: List[Dict]) -> pd.DataFrame:
        """Prepare DataFrame for analysis"""
        try:
            df = pd.DataFrame(sales_data)
            
            # Convert date column
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            
            # Convert numeric columns
            numeric_columns = ['total_amount', 'quantity', 'unit_price']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Clean customer names (handle empty values)
            if 'customer_name' in df.columns:
                df['customer_name'] = df['customer_name'].fillna('Unknown Customer')
                df['customer_name'] = df['customer_name'].replace('', 'Unknown Customer')
            
            # Add derived columns
            df['week'] = df['date'].dt.isocalendar().week
            df['month'] = df['date'].dt.month
            df['day_of_week'] = df['date'].dt.dayofweek
            df['hour'] = df['date'].dt.hour
            
            return df.sort_values('date')
            
        except Exception as e:
            logging.error(f"Error preparing DataFrame: {e}")
            return pd.DataFrame()
    
    def _segment_customer(self, customer_data: pd.Series, df: pd.DataFrame) -> CustomerInsight:
        """Segment individual customer based on behavior"""
        try:
            name = customer_data['customer_name']
            total_revenue = customer_data['total_revenue']
            purchase_count = customer_data['purchase_count']
            avg_order_value = customer_data['avg_order_value']
            days_since_last = customer_data['days_since_last_purchase']
            purchase_frequency = customer_data['purchase_frequency']
            
            # Calculate lifetime value (simplified)
            lifetime_value = total_revenue * (purchase_frequency / 12)  # Annualized
            
            # Calculate churn risk
            churn_risk = min(1.0, days_since_last / 60)  # Higher risk after 60+ days
            
            # Determine segment
            if total_revenue >= df['total_amount'].sum() * 0.1:  # Top 10% revenue
                segment = CustomerSegment.VIP
            elif purchase_count >= 5 and days_since_last <= 30:
                segment = CustomerSegment.LOYAL
            elif days_since_last > 60:
                segment = CustomerSegment.AT_RISK if purchase_count > 1 else CustomerSegment.DORMANT
            elif purchase_count == 1:
                segment = CustomerSegment.NEW
            else:
                segment = CustomerSegment.REGULAR
            
            # Generate recommendations
            recommendations = self._generate_customer_recommendations(segment, churn_risk, avg_order_value)
            
            return CustomerInsight(
                customer_name=name,
                segment=segment,
                total_revenue=total_revenue,
                purchase_frequency=int(purchase_count),
                avg_order_value=avg_order_value,
                last_purchase_days=int(days_since_last),
                lifetime_value=lifetime_value,
                churn_risk=churn_risk,
                recommendations=recommendations
            )
            
        except Exception as e:
            logging.error(f"Error segmenting customer: {e}")
            return CustomerInsight(
                customer_name="Unknown",
                segment=CustomerSegment.REGULAR,
                total_revenue=0,
                purchase_frequency=0,
                avg_order_value=0,
                last_purchase_days=999,
                lifetime_value=0,
                churn_risk=1.0,
                recommendations=[]
            )
    
    def _classify_product_performance(self, product_data: pd.Series, all_products: pd.DataFrame) -> ProductInsight:
        """Classify product into performance tier"""
        try:
            name = product_data['product_name']
            total_revenue = product_data['total_revenue']
            sales_count = product_data['sales_count']
            growth_rate = product_data['growth_rate']
            revenue_share = product_data['revenue_share']
            
            # Calculate performance percentiles
            revenue_percentile = (all_products['total_revenue'] <= total_revenue).mean()
            sales_percentile = (all_products['sales_count'] <= sales_count).mean()
            
            # Classify into tiers
            if revenue_percentile >= 0.7 and sales_percentile >= 0.7:
                tier = ProductTier.STAR
            elif revenue_percentile >= 0.7 and sales_percentile < 0.7:
                tier = ProductTier.CASH_COW
            elif revenue_percentile < 0.7 and sales_percentile >= 0.7:
                tier = ProductTier.POTENTIAL
            else:
                tier = ProductTier.DOG
            
            # Estimate profit margin (simplified)
            avg_price = product_data['avg_price']
            profit_margin = min(50, max(10, avg_price * 0.3))  # Rough estimate
            
            # Market share (within this business)
            market_share = revenue_share
            
            # Generate recommendations
            recommendations = self._generate_product_recommendations(tier, growth_rate, market_share)
            
            return ProductInsight(
                product_name=name,
                tier=tier,
                total_revenue=total_revenue,
                sales_count=int(sales_count),
                profit_margin=profit_margin,
                growth_rate=growth_rate,
                market_share=market_share,
                recommendations=recommendations
            )
            
        except Exception as e:
            logging.error(f"Error classifying product: {e}")
            return ProductInsight(
                product_name="Unknown",
                tier=ProductTier.DOG,
                total_revenue=0,
                sales_count=0,
                profit_margin=0,
                growth_rate=0,
                market_share=0,
                recommendations=[]
            )
    
    def _calculate_product_growth(self, df: pd.DataFrame, product_name: str, days_back: int) -> float:
        """Calculate product growth rate"""
        try:
            product_sales = df[df['product_name'] == product_name].copy()
            
            if len(product_sales) < 4:  # Need minimum data
                return 0.0
            
            # Split into two periods
            mid_point = datetime.utcnow() - timedelta(days=days_back//2)
            
            first_half = product_sales[product_sales['date'] < mid_point]
            second_half = product_sales[product_sales['date'] >= mid_point]
            
            if len(first_half) == 0 or len(second_half) == 0:
                return 0.0
            
            first_revenue = first_half['total_amount'].sum()
            second_revenue = second_half['total_amount'].sum()
            
            if first_revenue == 0:
                return 100.0 if second_revenue > 0 else 0.0
            
            growth_rate = ((second_revenue - first_revenue) / first_revenue) * 100
            return round(growth_rate, 1)
            
        except Exception as e:
            logging.error(f"Error calculating product growth: {e}")
            return 0.0
    
    def _analyze_temporal_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze revenue patterns by time"""
        try:
            patterns = {}
            
            # Daily patterns
            daily_revenue = df.groupby('day_of_week')['total_amount'].sum()
            patterns['best_day'] = {
                "day": daily_revenue.idxmax(),
                "revenue": float(daily_revenue.max()),
                "day_name": ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][daily_revenue.idxmax()]
            }
            
            patterns['worst_day'] = {
                "day": daily_revenue.idxmin(),
                "revenue": float(daily_revenue.min()),
                "day_name": ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][daily_revenue.idxmin()]
            }
            
            # Weekly patterns
            weekly_revenue = df.groupby('week')['total_amount'].sum()
            if len(weekly_revenue) > 1:
                patterns['weekly_trend'] = {
                    "direction": "increasing" if weekly_revenue.iloc[-1] > weekly_revenue.iloc[0] else "decreasing",
                    "change_percent": ((weekly_revenue.iloc[-1] - weekly_revenue.iloc[0]) / weekly_revenue.iloc[0] * 100) if weekly_revenue.iloc[0] > 0 else 0
                }
            
            # Monthly patterns (if enough data)
            monthly_revenue = df.groupby('month')['total_amount'].sum()
            if len(monthly_revenue) > 1:
                patterns['seasonal_peak'] = {
                    "month": int(monthly_revenue.idxmax()),
                    "revenue": float(monthly_revenue.max())
                }
            
            return patterns
            
        except Exception as e:
            logging.error(f"Error analyzing temporal patterns: {e}")
            return {}
    
    def _analyze_product_revenue_contribution(self, df: pd.DataFrame) -> Dict:
        """Analyze product contribution to revenue"""
        try:
            product_revenue = df.groupby('product_name')['total_amount'].sum().sort_values(ascending=False)
            total_revenue = product_revenue.sum()
            
            contribution = {
                "top_product": {
                    "name": product_revenue.index[0],
                    "revenue": float(product_revenue.iloc[0]),
                    "percentage": float(product_revenue.iloc[0] / total_revenue * 100)
                },
                "top_3_products": {
                    "names": product_revenue.head(3).index.tolist(),
                    "combined_percentage": float(product_revenue.head(3).sum() / total_revenue * 100)
                },
                "product_concentration": {
                    "products_contributing_80_percent": int((product_revenue.cumsum() / total_revenue <= 0.8).sum())
                }
            }
            
            return contribution
            
        except Exception as e:
            logging.error(f"Error analyzing product revenue: {e}")
            return {}
    
    def _analyze_customer_revenue_contribution(self, df: pd.DataFrame) -> Dict:
        """Analyze customer contribution to revenue"""
        try:
            # Filter out unknown customers for this analysis
            customer_df = df[df['customer_name'] != 'Unknown Customer']
            
            if len(customer_df) == 0:
                return {"status": "no_customer_data"}
            
            customer_revenue = customer_df.groupby('customer_name')['total_amount'].sum().sort_values(ascending=False)
            total_revenue = customer_revenue.sum()
            
            if len(customer_revenue) == 0:
                return {"status": "no_customer_data"}
            
            contribution = {
                "top_customer": {
                    "name": customer_revenue.index[0],
                    "revenue": float(customer_revenue.iloc[0]),
                    "percentage": float(customer_revenue.iloc[0] / total_revenue * 100)
                } if len(customer_revenue) > 0 else None,
                "customer_concentration": {
                    "customers_contributing_80_percent": int((customer_revenue.cumsum() / total_revenue <= 0.8).sum()) if total_revenue > 0 else 0
                }
            }
            
            if len(customer_revenue) >= 3:
                contribution["top_3_customers"] = {
                    "combined_percentage": float(customer_revenue.head(3).sum() / total_revenue * 100)
                }
            
            return contribution
            
        except Exception as e:
            logging.error(f"Error analyzing customer revenue: {e}")
            return {}
    
    def _analyze_pricing_impact(self, df: pd.DataFrame) -> Dict:
        """Analyze impact of pricing on revenue"""
        try:
            # Price distribution analysis
            price_stats = df['unit_price'].describe()
            
            # High vs low price performance
            median_price = df['unit_price'].median()
            high_price_sales = df[df['unit_price'] > median_price]
            low_price_sales = df[df['unit_price'] <= median_price]
            
            pricing_impact = {
                "price_range": {
                    "min": float(price_stats['min']),
                    "max": float(price_stats['max']),
                    "median": float(median_price)
                },
                "high_price_performance": {
                    "avg_revenue_per_sale": float(high_price_sales['total_amount'].mean()) if len(high_price_sales) > 0 else 0,
                    "total_revenue": float(high_price_sales['total_amount'].sum())
                },
                "low_price_performance": {
                    "avg_revenue_per_sale": float(low_price_sales['total_amount'].mean()) if len(low_price_sales) > 0 else 0,
                    "total_revenue": float(low_price_sales['total_amount'].sum())
                }
            }
            
            return pricing_impact
            
        except Exception as e:
            logging.error(f"Error analyzing pricing impact: {e}")
            return {}
    
    def _analyze_volume_impact(self, df: pd.DataFrame) -> Dict:
        """Analyze impact of sales volume on revenue"""
        try:
            # Daily volume analysis
            daily_volume = df.groupby(df['date'].dt.date).agg({
                'total_amount': ['count', 'sum']
            })
            
            daily_volume.columns = ['transaction_count', 'revenue']
            
            # Correlation between volume and revenue
            correlation = daily_volume['transaction_count'].corr(daily_volume['revenue'])
            
            volume_impact = {
                "volume_revenue_correlation": float(correlation) if not pd.isna(correlation) else 0,
                "avg_transactions_per_day": float(daily_volume['transaction_count'].mean()),
                "avg_revenue_per_transaction": float(df['total_amount'].mean()),
                "peak_volume_day": {
                    "transactions": int(daily_volume['transaction_count'].max()),
                    "revenue": float(daily_volume.loc[daily_volume['transaction_count'].idxmax(), 'revenue'])
                }
            }
            
            return volume_impact
            
        except Exception as e:
            logging.error(f"Error analyzing volume impact: {e}")
            return {}
    
    def _generate_customer_recommendations(self, segment: CustomerSegment, churn_risk: float, avg_order_value: float) -> List[str]:
        """Generate customer-specific recommendations"""
        recommendations = []
        
        if segment == CustomerSegment.VIP:
            recommendations.extend([
                "Provide exclusive VIP benefits and early access",
                "Assign dedicated customer success manager",
                "Create personalized product recommendations"
            ])
        elif segment == CustomerSegment.LOYAL:
            recommendations.extend([
                "Implement loyalty rewards program",
                "Send personalized thank you messages",
                "Offer referral incentives"
            ])
        elif segment == CustomerSegment.AT_RISK:
            recommendations.extend([
                "Send re-engagement campaigns immediately",
                "Offer special discounts to win back",
                "Conduct exit interview to understand issues"
            ])
        elif segment == CustomerSegment.NEW:
            recommendations.extend([
                "Send welcome series and onboarding",
                "Offer new customer incentives",
                "Gather feedback on first experience"
            ])
        elif segment == CustomerSegment.DORMANT:
            recommendations.extend([
                "Launch win-back campaign with attractive offers",
                "Survey to understand reason for leaving",
                "Consider removing from active marketing lists"
            ])
        
        # Risk-based recommendations
        if churn_risk > 0.7:
            recommendations.append("High churn risk - immediate intervention needed")
        
        # Value-based recommendations
        if avg_order_value < 50:
            recommendations.append("Implement upselling strategies to increase order value")
        
        return recommendations[:4]
    
    def _generate_product_recommendations(self, tier: ProductTier, growth_rate: float, market_share: float) -> List[str]:
        """Generate product-specific recommendations"""
        recommendations = []
        
        if tier == ProductTier.STAR:
            recommendations.extend([
                "Invest in marketing and scale production",
                "Expand product line with variations",
                "Use as flagship product in promotions"
            ])
        elif tier == ProductTier.CASH_COW:
            recommendations.extend([
                "Maintain quality and optimize costs",
                "Use profits to invest in other products",
                "Consider premium positioning"
            ])
        elif tier == ProductTier.POTENTIAL:
            recommendations.extend([
                "Increase marketing to boost revenue",
                "Optimize pricing strategy",
                "Improve product positioning"
            ])
        elif tier == ProductTier.DOG:
            recommendations.extend([
                "Consider discontinuing or repositioning",
                "Analyze if bundling might help",
                "Evaluate cost reduction opportunities"
            ])
        
        # Growth-based recommendations
        if growth_rate > 20:
            recommendations.append("High growth - increase inventory and marketing")
        elif growth_rate < -10:
            recommendations.append("Declining - investigate causes and take corrective action")
        
        return recommendations[:4]

# Initialize advanced analytics
def create_advanced_analytics(db_manager):
    return AdvancedAnalytics(db_manager)
