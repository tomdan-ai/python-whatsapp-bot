import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

class ChurnRisk(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class PriceStrategy(Enum):
    INCREASE = "increase"
    DECREASE = "decrease"
    MAINTAIN = "maintain"
    DYNAMIC = "dynamic"

@dataclass
class ChurnPrediction:
    customer_name: str
    churn_probability: float
    risk_level: ChurnRisk
    days_until_churn: int
    key_factors: List[str]
    retention_strategies: List[str]
    confidence: float

@dataclass
class InventoryRecommendation:
    product_name: str
    current_demand: float
    predicted_demand: float
    recommended_stock: int
    reorder_point: int
    seasonality_factor: float
    recommendations: List[str]

@dataclass
class PricingRecommendation:
    product_name: str
    current_price: float
    recommended_price: float
    price_strategy: PriceStrategy
    expected_impact: Dict[str, float]
    confidence: float
    rationale: str

class PredictiveInsights:
    """Advanced predictive analytics for business intelligence"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.models = {}
        self.scalers = {}
        
    def predict_customer_churn(self, user_id: str, days_back: int = 180) -> Dict:
        """Predict customer churn risk using machine learning"""
        try:
            # Get customer data
            customer_data = self._prepare_customer_features(user_id, days_back)
            
            if len(customer_data) < 10:
                return {
                    "status": "insufficient_data",
                    "message": "Need at least 10 customers with purchase history for churn prediction"
                }
            
            # Train or load churn model
            model = self._get_or_train_churn_model(customer_data, user_id)
            
            # Make predictions
            predictions = []
            for _, customer in customer_data.iterrows():
                prediction = self._predict_individual_churn(customer, model, user_id)
                predictions.append(prediction)
            
            # Sort by churn risk
            predictions.sort(key=lambda x: x.churn_probability, reverse=True)
            
            # Generate insights
            churn_insights = self._generate_churn_insights(predictions)
            
            return {
                "status": "success",
                "total_customers_analyzed": len(predictions),
                "high_risk_customers": len([p for p in predictions if p.risk_level in [ChurnRisk.HIGH, ChurnRisk.CRITICAL]]),
                "predictions": [self._format_churn_prediction(p) for p in predictions[:20]],  # Top 20
                "churn_insights": churn_insights,
                "retention_strategies": self._generate_retention_strategies(predictions),
                "model_accuracy": model.get("accuracy", 0.75)
            }
            
        except Exception as e:
            logging.error(f"Error predicting customer churn: {e}")
            return {"status": "error", "message": str(e)}
    
    def optimize_inventory(self, user_id: str, days_back: int = 90) -> Dict:
        """Provide inventory optimization recommendations"""
        try:
            # Get product sales data
            product_data = self._prepare_product_demand_data(user_id, days_back)
            
            if len(product_data) < 5:
                return {
                    "status": "insufficient_data",
                    "message": "Need sales data for at least 5 products for inventory optimization"
                }
            
            # Predict demand for each product
            inventory_recommendations = []
            
            for product_name in product_data['product_name'].unique():
                recommendation = self._optimize_product_inventory(product_data, product_name)
                if recommendation:
                    inventory_recommendations.append(recommendation)
            
            # Sort by importance (high demand products first)
            inventory_recommendations.sort(key=lambda x: x.predicted_demand, reverse=True)
            
            # Generate overall insights
            inventory_insights = self._generate_inventory_insights(inventory_recommendations)
            
            return {
                "status": "success",
                "total_products_analyzed": len(inventory_recommendations),
                "inventory_recommendations": [self._format_inventory_recommendation(r) for r in inventory_recommendations],
                "inventory_insights": inventory_insights,
                "optimization_opportunities": self._identify_inventory_opportunities(inventory_recommendations),
                "total_investment_needed": sum(r.recommended_stock * (r.current_demand * 10) for r in inventory_recommendations)  # Rough estimate
            }
            
        except Exception as e:
            logging.error(f"Error optimizing inventory: {e}")
            return {"status": "error", "message": str(e)}
    
    def recommend_pricing_strategy(self, user_id: str, days_back: int = 60) -> Dict:
        """Generate pricing strategy recommendations"""
        try:
            # Get pricing and sales data
            pricing_data = self._prepare_pricing_data(user_id, days_back)
            
            if len(pricing_data) < 20:
                return {
                    "status": "insufficient_data",
                    "message": "Need at least 20 sales records for pricing analysis"
                }
            
            # Analyze price elasticity and optimization opportunities
            pricing_recommendations = []
            
            for product_name in pricing_data['product_name'].unique():
                recommendation = self._analyze_product_pricing(pricing_data, product_name)
                if recommendation:
                    pricing_recommendations.append(recommendation)
            
            # Sort by potential impact
            pricing_recommendations.sort(key=lambda x: abs(x.expected_impact.get("revenue_change", 0)), reverse=True)
            
            # Generate pricing insights
            pricing_insights = self._generate_pricing_insights(pricing_recommendations, pricing_data)
            
            return {
                "status": "success",
                "total_products_analyzed": len(pricing_recommendations),
                "pricing_recommendations": [self._format_pricing_recommendation(r) for r in pricing_recommendations],
                "pricing_insights": pricing_insights,
                "revenue_optimization_potential": sum(r.expected_impact.get("revenue_change", 0) for r in pricing_recommendations),
                "market_analysis": self._analyze_market_conditions(pricing_data)
            }
            
        except Exception as e:
            logging.error(f"Error generating pricing recommendations: {e}")
            return {"status": "error", "message": str(e)}
    
    def run_predictive_analysis_suite(self, user_id: str) -> Dict:
        """Run comprehensive predictive analysis"""
        try:
            results = {
                "status": "success",
                "analysis_date": datetime.utcnow(),
                "churn_analysis": self.predict_customer_churn(user_id),
                "inventory_optimization": self.optimize_inventory(user_id),
                "pricing_strategy": self.recommend_pricing_strategy(user_id)
            }
            
            # Generate combined insights
            results["integrated_insights"] = self._generate_integrated_insights(results)
            results["priority_actions"] = self._generate_priority_actions(results)
            
            return results
            
        except Exception as e:
            logging.error(f"Error running predictive analysis suite: {e}")
            return {"status": "error", "message": str(e)}
    
    def _prepare_customer_features(self, user_id: str, days_back: int) -> pd.DataFrame:
        """Prepare customer features for churn prediction"""
        try:
            from .sales_models import SalesDataManager
            sales_manager = SalesDataManager(self.db_manager)
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            sales_data = sales_manager.get_sales_data(user_id, start_date, end_date, limit=2000)
            
            if not sales_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(sales_data)
            df['date'] = pd.to_datetime(df['date'])
            df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce')
            
            # Filter out unknown customers
            df = df[df['customer_name'] != 'Unknown Customer']
            
            # Calculate customer features
            current_date = datetime.utcnow()
            
            customer_features = df.groupby('customer_name').agg({
                'total_amount': ['sum', 'count', 'mean', 'std'],
                'date': ['min', 'max'],
                'quantity': 'sum'
            }).round(2)
            
            # Flatten column names
            customer_features.columns = [
                'total_revenue', 'purchase_count', 'avg_order_value', 'order_value_std',
                'first_purchase', 'last_purchase', 'total_quantity'
            ]
            customer_features = customer_features.reset_index()
            
            # Calculate derived features
            customer_features['days_since_last_purchase'] = (current_date - pd.to_datetime(customer_features['last_purchase'])).dt.days
            customer_features['customer_lifespan'] = (pd.to_datetime(customer_features['last_purchase']) - pd.to_datetime(customer_features['first_purchase'])).dt.days + 1
            customer_features['purchase_frequency'] = customer_features['purchase_count'] / (customer_features['customer_lifespan'] / 30)
            customer_features['recency_score'] = 1 / (1 + customer_features['days_since_last_purchase'] / 30)  # Exponential decay
            customer_features['monetary_score'] = (customer_features['total_revenue'] - customer_features['total_revenue'].min()) / (customer_features['total_revenue'].max() - customer_features['total_revenue'].min() + 1)
            customer_features['frequency_score'] = (customer_features['purchase_frequency'] - customer_features['purchase_frequency'].min()) / (customer_features['purchase_frequency'].max() - customer_features['purchase_frequency'].min() + 1)
            
            # Handle missing values
            customer_features['order_value_std'] = customer_features['order_value_std'].fillna(0)
            customer_features = customer_features.fillna(0)
            
            # Create churn label (customers who haven't purchased in 60+ days are considered churned)
            customer_features['is_churned'] = (customer_features['days_since_last_purchase'] > 60).astype(int)
            
            return customer_features
            
        except Exception as e:
            logging.error(f"Error preparing customer features: {e}")
            return pd.DataFrame()
    
    def _get_or_train_churn_model(self, customer_data: pd.DataFrame, user_id: str) -> Dict:
        """Get existing churn model or train a new one"""
        try:
            model_key = f"churn_model_{user_id}"
            
            # Check if model exists and is recent
            if model_key in self.models:
                model_info = self.models[model_key]
                if (datetime.utcnow() - model_info["trained_at"]).days < 7:  # Model is less than 7 days old
                    return model_info
            
            # Prepare features and target
            feature_columns = [
                'total_revenue', 'purchase_count', 'avg_order_value', 'purchase_frequency',
                'days_since_last_purchase', 'customer_lifespan', 'recency_score',
                'monetary_score', 'frequency_score'
            ]
            
            X = customer_data[feature_columns].fillna(0)
            y = customer_data['is_churned']
            
            if len(X) < 10 or y.sum() < 2:  # Need minimum data and some churned customers
                # Use simple heuristic model
                return {
                    "type": "heuristic",
                    "trained_at": datetime.utcnow(),
                    "accuracy": 0.7,
                    "features": feature_columns
                }
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            if len(X_train) > 20:
                # Use Random Forest for larger datasets
                model = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=5)
            else:
                # Use Logistic Regression for smaller datasets
                model = LogisticRegression(random_state=42, max_iter=1000)
            
            model.fit(X_train_scaled, y_train)
            
            # Calculate accuracy
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Store model
            model_info = {
                "type": "ml_model",
                "model": model,
                "scaler": scaler,
                "features": feature_columns,
                "accuracy": accuracy,
                "trained_at": datetime.utcnow()
            }
            
            self.models[model_key] = model_info
            
            logging.info(f"Trained churn model for user {user_id} with accuracy: {accuracy:.2f}")
            
            return model_info
            
        except Exception as e:
            logging.error(f"Error training churn model: {e}")
            return {"type": "heuristic", "trained_at": datetime.utcnow(), "accuracy": 0.7}
    
    def _predict_individual_churn(self, customer: pd.Series, model_info: Dict, user_id: str) -> ChurnPrediction:
        """Predict churn for individual customer"""
        try:
            customer_name = customer['customer_name']
            
            if model_info["type"] == "heuristic":
                # Simple heuristic prediction
                days_since_last = customer['days_since_last_purchase']
                purchase_frequency = customer['purchase_frequency']
                
                if days_since_last > 90:
                    churn_prob = 0.9
                elif days_since_last > 60:
                    churn_prob = 0.7
                elif days_since_last > 30:
                    churn_prob = 0.4
                else:
                    churn_prob = 0.1
                
                # Adjust based on frequency
                if purchase_frequency > 2:
                    churn_prob *= 0.7
                elif purchase_frequency < 0.5:
                    churn_prob *= 1.3
                
                churn_prob = min(0.95, max(0.05, churn_prob))
                
            else:
                # ML model prediction
                features = customer[model_info["features"]].values.reshape(1, -1)
                features_scaled = model_info["scaler"].transform(features)
                churn_prob = model_info["model"].predict_proba(features_scaled)[0][1]
            
            # Determine risk level
            if churn_prob >= 0.8:
                risk_level = ChurnRisk.CRITICAL
            elif churn_prob >= 0.6:
                risk_level = ChurnRisk.HIGH
            elif churn_prob >= 0.3:
                risk_level = ChurnRisk.MEDIUM
            else:
                risk_level = ChurnRisk.LOW
            
            # Estimate days until churn
            days_until_churn = max(1, int(30 * (1 - churn_prob)))
            
            # Identify key factors
            key_factors = self._identify_churn_factors(customer)
            
            # Generate retention strategies
            retention_strategies = self._generate_individual_retention_strategies(customer, risk_level)
            
            return ChurnPrediction(
                customer_name=customer_name,
                churn_probability=churn_prob,
                risk_level=risk_level,
                days_until_churn=days_until_churn,
                key_factors=key_factors,
                retention_strategies=retention_strategies,
                confidence=model_info.get("accuracy", 0.7)
            )
            
        except Exception as e:
            logging.error(f"Error predicting individual churn: {e}")
            return ChurnPrediction(
                customer_name="Unknown",
                churn_probability=0.5,
                risk_level=ChurnRisk.MEDIUM,
                days_until_churn=30,
                key_factors=[],
                retention_strategies=[],
                confidence=0.5
            )
    
    def _prepare_product_demand_data(self, user_id: str, days_back: int) -> pd.DataFrame:
        """Prepare product demand data for inventory optimization"""
        try:
            from .sales_models import SalesDataManager
            sales_manager = SalesDataManager(self.db_manager)
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            sales_data = sales_manager.get_sales_data(user_id, start_date, end_date, limit=2000)
            
            if not sales_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(sales_data)
            df['date'] = pd.to_datetime(df['date'])
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
            
            # Add time features
            df['week'] = df['date'].dt.isocalendar().week
            df['day_of_week'] = df['date'].dt.dayofweek
            df['day_of_month'] = df['date'].dt.day
            
            return df
            
        except Exception as e:
            logging.error(f"Error preparing product demand data: {e}")
            return pd.DataFrame()
    
    def _optimize_product_inventory(self, product_data: pd.DataFrame, product_name: str) -> Optional[InventoryRecommendation]:
        """Optimize inventory for specific product"""
        try:
            product_sales = product_data[product_data['product_name'] == product_name].copy()
            
            if len(product_sales) < 5:
                return None
            
            # Calculate demand metrics
            daily_demand = product_sales.groupby(product_sales['date'].dt.date)['quantity'].sum()
            current_demand = daily_demand.mean()
            demand_std = daily_demand.std()
            
            # Predict future demand (simple trend analysis)
            if len(daily_demand) > 7:
                recent_demand = daily_demand.tail(7).mean()
                early_demand = daily_demand.head(7).mean()
                trend = (recent_demand - early_demand) / early_demand if early_demand > 0 else 0
                predicted_demand = current_demand * (1 + trend)
            else:
                predicted_demand = current_demand
            
            # Calculate seasonality factor
            weekly_demand = product_sales.groupby('day_of_week')['quantity'].mean()
            seasonality_factor = weekly_demand.std() / weekly_demand.mean() if weekly_demand.mean() > 0 else 0
            
            # Calculate inventory recommendations
            # Safety stock = Z-score * std * sqrt(lead_time)
            lead_time_days = 7  # Assume 7-day lead time
            service_level = 0.95  # 95% service level
            z_score = 1.65  # For 95% service level
            
            safety_stock = z_score * (demand_std if demand_std > 0 else current_demand * 0.2) * np.sqrt(lead_time_days)
            recommended_stock = int((predicted_demand * lead_time_days) + safety_stock)
            reorder_point = int((predicted_demand * lead_time_days) + (safety_stock * 0.5))
            
            # Generate recommendations
            recommendations = []
            if predicted_demand > current_demand * 1.2:
                recommendations.append("Demand trending up - increase stock levels")
            elif predicted_demand < current_demand * 0.8:
                recommendations.append("Demand declining - reduce stock levels")
            
            if seasonality_factor > 0.3:
                recommendations.append("High seasonality - plan for demand fluctuations")
            
            if current_demand > 5:
                recommendations.append("High-volume product - consider bulk ordering discounts")
            
            return InventoryRecommendation(
                product_name=product_name,
                current_demand=current_demand,
                predicted_demand=predicted_demand,
                recommended_stock=max(1, recommended_stock),
                reorder_point=max(1, reorder_point),
                seasonality_factor=seasonality_factor,
                recommendations=recommendations
            )
            
        except Exception as e:
            logging.error(f"Error optimizing inventory for {product_name}: {e}")
            return None
    
    def _prepare_pricing_data(self, user_id: str, days_back: int) -> pd.DataFrame:
        """Prepare pricing analysis data"""
        try:
            from .sales_models import SalesDataManager
            sales_manager = SalesDataManager(self.db_manager)
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            sales_data = sales_manager.get_sales_data(user_id, start_date, end_date, limit=2000)
            
            if not sales_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(sales_data)
            df['date'] = pd.to_datetime(df['date'])
            df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
            df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce')
            
            # Add time features for trend analysis
            df['week'] = df['date'].dt.isocalendar().week
            df['day_of_week'] = df['date'].dt.dayofweek
            
            return df
            
        except Exception as e:
            logging.error(f"Error preparing pricing data: {e}")
            return pd.DataFrame()
    
    def _analyze_product_pricing(self, pricing_data: pd.DataFrame, product_name: str) -> Optional[PricingRecommendation]:
        """Analyze pricing strategy for specific product"""
        try:
            product_sales = pricing_data[pricing_data['product_name'] == product_name].copy()
            
            if len(product_sales) < 10:
                return None
            
            current_price = product_sales['unit_price'].median()
            
            # Analyze price elasticity (simplified)
            # Group by price ranges and analyze volume
            product_sales['price_range'] = pd.cut(product_sales['unit_price'], bins=5, labels=['Low', 'Low-Med', 'Medium', 'Med-High', 'High'])
            price_elasticity = product_sales.groupby('price_range').agg({
                'quantity': 'sum',
                'total_amount': 'sum',
                'unit_price': 'mean'
            })
            
            # Calculate revenue per price range
            if len(price_elasticity) > 2:
                max_revenue_range = price_elasticity['total_amount'].idxmax()
                optimal_price = price_elasticity.loc[max_revenue_range, 'unit_price']
            else:
                optimal_price = current_price
            
            # Determine strategy
            price_change_percent = (optimal_price - current_price) / current_price if current_price > 0 else 0
            
            if price_change_percent > 0.1:
                strategy = PriceStrategy.INCREASE
                recommended_price = current_price * 1.1  # Conservative 10% increase
            elif price_change_percent < -0.1:
                strategy = PriceStrategy.DECREASE
                recommended_price = current_price * 0.9  # Conservative 10% decrease
            else:
                strategy = PriceStrategy.MAINTAIN
                recommended_price = current_price
            
            # Estimate impact
            if strategy == PriceStrategy.INCREASE:
                volume_change = -0.15  # Assume 15% volume decrease
                revenue_change = (1.1 * 0.85) - 1  # Price up 10%, volume down 15%
            elif strategy == PriceStrategy.DECREASE:
                volume_change = 0.20  # Assume 20% volume increase
                revenue_change = (0.9 * 1.2) - 1  # Price down 10%, volume up 20%
            else:
                volume_change = 0
                revenue_change = 0
            
            current_weekly_revenue = product_sales['total_amount'].sum() / (len(product_sales) / 7)
            revenue_impact = current_weekly_revenue * revenue_change
            
            expected_impact = {
                "volume_change_percent": volume_change * 100,
                "revenue_change": revenue_impact,
                "profit_margin_impact": 0  # Would need cost data to calculate
            }
            
            # Generate rationale
            if strategy == PriceStrategy.INCREASE:
                rationale = f"Data suggests demand can support {((recommended_price - current_price) / current_price * 100):.1f}% price increase"
            elif strategy == PriceStrategy.DECREASE:
                rationale = f"Lower price could increase volume and total revenue"
            else:
                rationale = "Current pricing appears optimal based on available data"
            
            return PricingRecommendation(
                product_name=product_name,
                current_price=current_price,
                recommended_price=recommended_price,
                price_strategy=strategy,
                expected_impact=expected_impact,
                confidence=0.6,  # Moderate confidence due to simplified analysis
                rationale=rationale
            )
            
        except Exception as e:
            logging.error(f"Error analyzing pricing for {product_name}: {e}")
            return None
    
    def _identify_churn_factors(self, customer: pd.Series) -> List[str]:
        """Identify key factors contributing to churn risk"""
        factors = []
        
        try:
            days_since_last = customer['days_since_last_purchase']
            purchase_frequency = customer['purchase_frequency']
            avg_order_value = customer['avg_order_value']
            
            if days_since_last > 60:
                factors.append("Long time since last purchase")
            if purchase_frequency < 0.5:
                factors.append("Low purchase frequency")
            if avg_order_value < 30:
                factors.append("Low average order value")
            if customer['customer_lifespan'] < 30:
                factors.append("New customer - still establishing loyalty")
            
            return factors[:3]  # Return top 3 factors
            
        except Exception as e:
            logging.error(f"Error identifying churn factors: {e}")
            return []
    
    def _generate_individual_retention_strategies(self, customer: pd.Series, risk_level: ChurnRisk) -> List[str]:
        """Generate customer-specific retention strategies"""
        strategies = []
        
        try:
            if risk_level == ChurnRisk.CRITICAL:
                strategies.extend([
                    "Immediate personal outreach with special offer",
                    "Exclusive VIP discount or free gift",
                    "Direct call to understand issues"
                ])
            elif risk_level == ChurnRisk.HIGH:
                strategies.extend([
                    "Send targeted re-engagement email campaign",
                    "Offer personalized discount on favorite products",
                    "Invite to exclusive customer event"
                ])
            elif risk_level == ChurnRisk.MEDIUM:
                strategies.extend([
                    "Include in regular loyalty program communications",
                    "Send product recommendations based on history",
                    "Offer small incentive for next purchase"
                ])
            else:
                strategies.extend([
                    "Continue regular engagement",
                    "Monitor for any changes in behavior"
                ])
            
            # Add value-based strategies
            if customer['avg_order_value'] > 100:
                strategies.append("Focus on premium product recommendations")
            else:
                strategies.append("Offer bundle deals to increase order value")
            
            return strategies[:3]
            
        except Exception as e:
            logging.error(f"Error generating retention strategies: {e}")
            return []

    # Helper methods for formatting and insights generation
    def _format_churn_prediction(self, prediction: ChurnPrediction) -> Dict:
        """Format churn prediction for display"""
        return {
            "customer_name": prediction.customer_name,
            "churn_probability": f"{prediction.churn_probability:.1%}",
            "risk_level": prediction.risk_level.value.upper(),
            "days_until_churn": prediction.days_until_churn,
            "key_factors": prediction.key_factors,
            "retention_strategies": prediction.retention_strategies,
            "confidence": f"{prediction.confidence:.1%}"
        }
    
    def _format_inventory_recommendation(self, recommendation: InventoryRecommendation) -> Dict:
        """Format inventory recommendation for display"""
        return {
            "product_name": recommendation.product_name,
            "current_demand": f"{recommendation.current_demand:.1f} units/day",
            "predicted_demand": f"{recommendation.predicted_demand:.1f} units/day",
            "recommended_stock": recommendation.recommended_stock,
            "reorder_point": recommendation.reorder_point,
            "seasonality": "High" if recommendation.seasonality_factor > 0.3 else "Medium" if recommendation.seasonality_factor > 0.1 else "Low",
            "recommendations": recommendation.recommendations
        }
    
    def _format_pricing_recommendation(self, recommendation: PricingRecommendation) -> Dict:
        """Format pricing recommendation for display"""
        return {
            "product_name": recommendation.product_name,
            "current_price": f"${recommendation.current_price:.2f}",
            "recommended_price": f"${recommendation.recommended_price:.2f}",
            "strategy": recommendation.price_strategy.value.title(),
            "expected_volume_change": f"{recommendation.expected_impact.get('volume_change_percent', 0):+.1f}%",
            "expected_revenue_change": f"${recommendation.expected_impact.get('revenue_change', 0):+.0f}/week",
            "confidence": f"{recommendation.confidence:.1%}",
            "rationale": recommendation.rationale
        }
    
    def _generate_churn_insights(self, predictions: List[ChurnPrediction]) -> List[str]:
        """Generate insights from churn predictions"""
        insights = []
        
        try:
            total_customers = len(predictions)
            high_risk = len([p for p in predictions if p.risk_level in [ChurnRisk.HIGH, ChurnRisk.CRITICAL]])
            
            if high_risk > 0:
                insights.append(f"{high_risk} customers at high risk of churning")
            
            # Most common churn factors
            all_factors = []
            for prediction in predictions:
                all_factors.extend(prediction.key_factors)
            
            if all_factors:
                from collections import Counter
                common_factors = Counter(all_factors).most_common(3)
                insights.append(f"Most common risk factor: {common_factors[0][0]}")
            
            avg_confidence = np.mean([p.confidence for p in predictions])
            insights.append(f"Model confidence: {avg_confidence:.1%}")
            
            return insights
            
        except Exception as e:
            logging.error(f"Error generating churn insights: {e}")
            return []
    
    def _generate_inventory_insights(self, recommendations: List[InventoryRecommendation]) -> List[str]:
        """Generate insights from inventory recommendations"""
        insights = []
        
        try:
            high_demand_products = [r for r in recommendations if r.predicted_demand > r.current_demand * 1.2]
            declining_products = [r for r in recommendations if r.predicted_demand < r.current_demand * 0.8]
            
            if high_demand_products:
                insights.append(f"{len(high_demand_products)} products showing increased demand")
            
            if declining_products:
                insights.append(f"{len(declining_products)} products showing declining demand")
            
            total_investment = sum(r.recommended_stock * 10 for r in recommendations)  # Rough estimate
            insights.append(f"Estimated inventory investment needed: ${total_investment:,.0f}")
            
            return insights
            
        except Exception as e:
            logging.error(f"Error generating inventory insights: {e}")
            return []
    
    def _generate_pricing_insights(self, recommendations: List[PricingRecommendation], pricing_data: pd.DataFrame) -> List[str]:
        """Generate insights from pricing recommendations"""
        insights = []
        
        try:
            increase_recs = [r for r in recommendations if r.price_strategy == PriceStrategy.INCREASE]
            decrease_recs = [r for r in recommendations if r.price_strategy == PriceStrategy.DECREASE]
            
            if increase_recs:
                insights.append(f"{len(increase_recs)} products could support price increases")
            
            if decrease_recs:
                insights.append(f"{len(decrease_recs)} products might benefit from price reductions")
            
            total_revenue_impact = sum(r.expected_impact.get("revenue_change", 0) for r in recommendations)
            if total_revenue_impact > 0:
                insights.append(f"Potential weekly revenue increase: ${total_revenue_impact:+.0f}")
            
            return insights
            
        except Exception as e:
            logging.error(f"Error generating pricing insights: {e}")
            return []

# Initialize predictive insights
def create_predictive_insights(db_manager):
    return PredictiveInsights(db_manager)