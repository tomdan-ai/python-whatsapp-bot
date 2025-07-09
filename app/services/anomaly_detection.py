import numpy as np
import pandas as pd
from scipy import stats
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging
from dataclasses import dataclass
from enum import Enum

class AnomalySeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AnomalyType(Enum):
    SALES_DROP = "sales_drop"
    SALES_SPIKE = "sales_spike"
    REVENUE_ANOMALY = "revenue_anomaly"
    PRODUCT_ANOMALY = "product_anomaly"
    PATTERN_BREAK = "pattern_break"
    SEASONAL_DEVIATION = "seasonal_deviation"
    TREND_REVERSAL = "trend_reversal"

@dataclass
class Anomaly:
    """Data class for anomaly detection results"""
    id: str
    type: AnomalyType
    severity: AnomalySeverity
    date: datetime
    value: float
    expected_value: float
    deviation_score: float
    description: str
    impact: str
    suggestions: List[str]
    confidence: float
    metadata: Dict[str, Any]

class StatisticalAnomalyDetector:
    """Advanced statistical anomaly detection for business data"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.z_score_threshold = 2.0  # Standard deviations for anomaly
        self.iqr_multiplier = 1.5     # IQR multiplier for outliers
        self.min_data_points = 7      # Minimum data points for analysis
        
    def detect_all_anomalies(self, user_id: str, days_back: int = 30) -> List[Anomaly]:
        """Detect all types of anomalies in user's data"""
        try:
            anomalies = []
            
            # Get sales data
            sales_data = self._get_sales_data(user_id, days_back)
            
            if len(sales_data) < self.min_data_points:
                logging.info(f"Insufficient data for anomaly detection: {len(sales_data)} records")
                return []
            
            # Convert to DataFrame for analysis
            df = self._prepare_dataframe(sales_data)
            
            if df.empty:
                return []
            
            # 1. Sales Volume Anomalies
            volume_anomalies = self._detect_sales_volume_anomalies(df, user_id)
            anomalies.extend(volume_anomalies)
            
            # 2. Revenue Anomalies
            revenue_anomalies = self._detect_revenue_anomalies(df, user_id)
            anomalies.extend(revenue_anomalies)
            
            # 3. Product Performance Anomalies
            product_anomalies = self._detect_product_anomalies(df, user_id)
            anomalies.extend(product_anomalies)
            
            # 4. Daily Pattern Anomalies
            pattern_anomalies = self._detect_daily_pattern_anomalies(df, user_id)
            anomalies.extend(pattern_anomalies)
            
            # 5. Trend Deviation Anomalies
            trend_anomalies = self._detect_trend_anomalies(df, user_id)
            anomalies.extend(trend_anomalies)
            
            # Sort by severity and date
            anomalies.sort(key=lambda x: (x.severity.value, x.date), reverse=True)
            
            # Save anomalies to database
            self._save_anomalies(user_id, anomalies)
            
            logging.info(f"Detected {len(anomalies)} anomalies for user {user_id}")
            return anomalies
            
        except Exception as e:
            logging.error(f"Error detecting anomalies: {e}")
            return []
    
    def _get_sales_data(self, user_id: str, days_back: int) -> List[Dict]:
        """Get sales data for anomaly analysis"""
        try:
            from .sales_models import SalesDataManager
            sales_manager = SalesDataManager(self.db_manager)
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            return sales_manager.get_sales_data(user_id, start_date, end_date, limit=1000)
            
        except Exception as e:
            logging.error(f"Error getting sales data: {e}")
            return []
    
    def _prepare_dataframe(self, sales_data: List[Dict]) -> pd.DataFrame:
        """Prepare DataFrame for anomaly analysis"""
        try:
            if not sales_data:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(sales_data)
            
            # Ensure required columns exist
            required_columns = ['date', 'total_amount', 'quantity', 'product_name']
            for col in required_columns:
                if col not in df.columns:
                    logging.warning(f"Missing column {col} in sales data")
                    return pd.DataFrame()
            
            # Convert date column
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            
            # Convert numeric columns
            numeric_columns = ['total_amount', 'quantity', 'unit_price']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Add derived columns
            df['day_of_week'] = df['date'].dt.dayofweek
            df['day_name'] = df['date'].dt.day_name()
            df['hour'] = df['date'].dt.hour
            df['date_only'] = df['date'].dt.date
            
            # Sort by date
            df = df.sort_values('date')
            
            return df
            
        except Exception as e:
            logging.error(f"Error preparing DataFrame: {e}")
            return pd.DataFrame()
    
    def _detect_sales_volume_anomalies(self, df: pd.DataFrame, user_id: str) -> List[Anomaly]:
        """Detect anomalies in daily sales volume using Z-score analysis"""
        anomalies = []
        
        try:
            # Group by date to get daily sales counts
            daily_sales = df.groupby('date_only').agg({
                'total_amount': 'count',  # Number of sales
                'total_amount': 'sum'     # This will be overwritten, but we need both
            }).rename(columns={'total_amount': 'sales_count'})
            
            # Recalculate properly
            daily_stats = df.groupby('date_only').agg({
                'total_amount': ['count', 'sum'],
                'quantity': 'sum'
            }).round(2)
            
            # Flatten column names
            daily_stats.columns = ['sales_count', 'total_revenue', 'total_quantity']
            daily_stats = daily_stats.reset_index()
            
            if len(daily_stats) < self.min_data_points:
                return anomalies
            
            # Z-score analysis for sales count
            sales_count_mean = daily_stats['sales_count'].mean()
            sales_count_std = daily_stats['sales_count'].std()
            
            if sales_count_std == 0:  # No variation
                return anomalies
            
            daily_stats['sales_count_zscore'] = np.abs(
                (daily_stats['sales_count'] - sales_count_mean) / sales_count_std
            )
            
            # Detect anomalies
            for _, row in daily_stats.iterrows():
                zscore = row['sales_count_zscore']
                
                if zscore >= self.z_score_threshold:
                    date = row['date_only']
                    actual_sales = row['sales_count']
                    expected_sales = sales_count_mean
                    
                    # Determine if it's a drop or spike
                    if actual_sales < expected_sales:
                        anomaly_type = AnomalyType.SALES_DROP
                        impact = "negative"
                        description = f"Sales volume dropped to {actual_sales} (expected ~{expected_sales:.1f})"
                    else:
                        anomaly_type = AnomalyType.SALES_SPIKE
                        impact = "positive"
                        description = f"Sales volume spiked to {actual_sales} (expected ~{expected_sales:.1f})"
                    
                    # Determine severity
                    severity = self._calculate_severity(zscore)
                    
                    # Generate suggestions
                    suggestions = self._generate_volume_suggestions(anomaly_type, zscore, date)
                    
                    anomaly = Anomaly(
                        id=f"vol_{user_id}_{date}",
                        type=anomaly_type,
                        severity=severity,
                        date=datetime.combine(date, datetime.min.time()),
                        value=actual_sales,
                        expected_value=expected_sales,
                        deviation_score=zscore,
                        description=description,
                        impact=impact,
                        suggestions=suggestions,
                        confidence=min(0.95, zscore / 4.0),  # Higher z-score = higher confidence
                        metadata={
                            "analysis_type": "z_score",
                            "std_dev": sales_count_std,
                            "mean": sales_count_mean,
                            "total_revenue": row['total_revenue']
                        }
                    )
                    
                    anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logging.error(f"Error detecting sales volume anomalies: {e}")
            return []
    
    def _detect_revenue_anomalies(self, df: pd.DataFrame, user_id: str) -> List[Anomaly]:
        """Detect anomalies in daily revenue using statistical methods"""
        anomalies = []
        
        try:
            # Group by date to get daily revenue
            daily_revenue = df.groupby('date_only').agg({
                'total_amount': 'sum'
            }).rename(columns={'total_amount': 'daily_revenue'}).reset_index()
            
            if len(daily_revenue) < self.min_data_points:
                return anomalies
            
            # Calculate statistics
            revenue_values = daily_revenue['daily_revenue'].values
            mean_revenue = np.mean(revenue_values)
            std_revenue = np.std(revenue_values)
            
            if std_revenue == 0:
                return anomalies
            
            # Z-score analysis
            z_scores = np.abs((revenue_values - mean_revenue) / std_revenue)
            
            # IQR method for additional validation
            q1 = np.percentile(revenue_values, 25)
            q3 = np.percentile(revenue_values, 75)
            iqr = q3 - q1
            iqr_lower = q1 - (self.iqr_multiplier * iqr)
            iqr_upper = q3 + (self.iqr_multiplier * iqr)
            
            for i, (_, row) in enumerate(daily_revenue.iterrows()):
                zscore = z_scores[i]
                revenue = row['daily_revenue']
                date = row['date_only']
                
                # Check if it's an anomaly by either method
                is_zscore_anomaly = zscore >= self.z_score_threshold
                is_iqr_anomaly = revenue < iqr_lower or revenue > iqr_upper
                
                if is_zscore_anomaly or is_iqr_anomaly:
                    # Determine anomaly type
                    if revenue < mean_revenue:
                        anomaly_type = AnomalyType.REVENUE_ANOMALY
                        impact = "negative"
                        description = f"Revenue dropped to ${revenue:.2f} (expected ~${mean_revenue:.2f})"
                    else:
                        anomaly_type = AnomalyType.REVENUE_ANOMALY
                        impact = "positive"
                        description = f"Revenue increased to ${revenue:.2f} (expected ~${mean_revenue:.2f})"
                    
                    severity = self._calculate_severity(zscore)
                    suggestions = self._generate_revenue_suggestions(revenue, mean_revenue, date)
                    
                    anomaly = Anomaly(
                        id=f"rev_{user_id}_{date}",
                        type=anomaly_type,
                        severity=severity,
                        date=datetime.combine(date, datetime.min.time()),
                        value=revenue,
                        expected_value=mean_revenue,
                        deviation_score=zscore,
                        description=description,
                        impact=impact,
                        suggestions=suggestions,
                        confidence=min(0.95, zscore / 4.0),
                        metadata={
                            "analysis_type": "z_score_and_iqr",
                            "iqr_lower": iqr_lower,
                            "iqr_upper": iqr_upper,
                            "method_used": "both" if is_zscore_anomaly and is_iqr_anomaly else "z_score" if is_zscore_anomaly else "iqr"
                        }
                    )
                    
                    anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logging.error(f"Error detecting revenue anomalies: {e}")
            return []
    
    def _detect_product_anomalies(self, df: pd.DataFrame, user_id: str) -> List[Anomaly]:
        """Detect anomalies in product performance"""
        anomalies = []
        
        try:
            # Group by product to analyze performance
            product_stats = df.groupby('product_name').agg({
                'total_amount': ['count', 'sum', 'mean'],
                'quantity': 'sum'
            }).round(2)
            
            # Flatten column names
            product_stats.columns = ['sales_count', 'total_revenue', 'avg_sale_value', 'total_quantity']
            product_stats = product_stats.reset_index()
            
            # Only analyze products with sufficient data
            product_stats = product_stats[product_stats['sales_count'] >= 3]
            
            if len(product_stats) < 2:  # Need at least 2 products to compare
                return anomalies
            
            # Detect products with unusually low/high performance
            metrics = ['total_revenue', 'sales_count', 'avg_sale_value']
            
            for metric in metrics:
                values = product_stats[metric].values
                if len(values) < 3:
                    continue
                    
                mean_val = np.mean(values)
                std_val = np.std(values)
                
                if std_val == 0:
                    continue
                
                z_scores = np.abs((values - mean_val) / std_val)
                
                for i, (_, row) in enumerate(product_stats.iterrows()):
                    zscore = z_scores[i]
                    
                    if zscore >= self.z_score_threshold:
                        product_name = row['product_name']
                        actual_value = row[metric]
                        
                        # Determine impact
                        if actual_value < mean_val:
                            impact = "negative"
                            description = f"Product '{product_name}' underperforming in {metric.replace('_', ' ')}"
                        else:
                            impact = "positive"
                            description = f"Product '{product_name}' excelling in {metric.replace('_', ' ')}"
                        
                        severity = self._calculate_severity(zscore)
                        suggestions = self._generate_product_suggestions(product_name, metric, impact)
                        
                        anomaly = Anomaly(
                            id=f"prod_{user_id}_{product_name}_{metric}",
                            type=AnomalyType.PRODUCT_ANOMALY,
                            severity=severity,
                            date=datetime.utcnow(),
                            value=actual_value,
                            expected_value=mean_val,
                            deviation_score=zscore,
                            description=description,
                            impact=impact,
                            suggestions=suggestions,
                            confidence=min(0.90, zscore / 3.0),
                            metadata={
                                "product_name": product_name,
                                "metric": metric,
                                "total_products_analyzed": len(product_stats)
                            }
                        )
                        
                        anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logging.error(f"Error detecting product anomalies: {e}")
            return []
    
    def _detect_daily_pattern_anomalies(self, df: pd.DataFrame, user_id: str) -> List[Anomaly]:
        """Detect anomalies in day-of-week patterns"""
        anomalies = []
        
        try:
            # Analyze day-of-week patterns
            daily_patterns = df.groupby(['day_of_week', 'day_name']).agg({
                'total_amount': ['count', 'sum', 'mean']
            }).round(2)
            
            # Flatten columns
            daily_patterns.columns = ['sales_count', 'total_revenue', 'avg_revenue']
            daily_patterns = daily_patterns.reset_index()
            
            if len(daily_patterns) < 3:  # Need at least 3 different days
                return anomalies
            
            # Analyze each metric for patterns
            for metric in ['sales_count', 'total_revenue']:
                values = daily_patterns[metric].values
                mean_val = np.mean(values)
                std_val = np.std(values)
                
                if std_val == 0:
                    continue
                
                z_scores = np.abs((values - mean_val) / std_val)
                
                for i, (_, row) in enumerate(daily_patterns.iterrows()):
                    zscore = z_scores[i]
                    
                    if zscore >= self.z_score_threshold:
                        day_name = row['day_name']
                        actual_value = row[metric]
                        
                        if actual_value < mean_val:
                            impact = "negative"
                            description = f"{day_name} consistently underperforms in {metric.replace('_', ' ')}"
                        else:
                            impact = "positive"
                            description = f"{day_name} consistently outperforms in {metric.replace('_', ' ')}"
                        
                        severity = AnomalySeverity.MEDIUM  # Pattern anomalies are usually medium severity
                        suggestions = self._generate_pattern_suggestions(day_name, metric, impact)
                        
                        anomaly = Anomaly(
                            id=f"pattern_{user_id}_{day_name}_{metric}",
                            type=AnomalyType.PATTERN_BREAK,
                            severity=severity,
                            date=datetime.utcnow(),
                            value=actual_value,
                            expected_value=mean_val,
                            deviation_score=zscore,
                            description=description,
                            impact=impact,
                            suggestions=suggestions,
                            confidence=min(0.85, zscore / 3.0),
                            metadata={
                                "day_of_week": row['day_of_week'],
                                "day_name": day_name,
                                "pattern_type": "daily",
                                "metric": metric
                            }
                        )
                        
                        anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logging.error(f"Error detecting daily pattern anomalies: {e}")
            return []
    
    def _detect_trend_anomalies(self, df: pd.DataFrame, user_id: str) -> List[Anomaly]:
        """Detect trend reversals and deviations"""
        anomalies = []
        
        try:
            # Create daily aggregations for trend analysis
            daily_data = df.groupby('date_only').agg({
                'total_amount': ['count', 'sum']
            }).round(2)
            
            daily_data.columns = ['sales_count', 'revenue']
            daily_data = daily_data.reset_index()
            daily_data = daily_data.sort_values('date_only')
            
            if len(daily_data) < 10:  # Need sufficient data for trend analysis
                return anomalies
            
            # Calculate moving averages for trend detection
            window = min(7, len(daily_data) // 3)  # Adaptive window size
            
            for metric in ['sales_count', 'revenue']:
                daily_data[f'{metric}_ma'] = daily_data[metric].rolling(window=window).mean()
                daily_data[f'{metric}_trend'] = daily_data[f'{metric}_ma'].diff()
                
                # Detect significant trend changes
                trend_values = daily_data[f'{metric}_trend'].dropna()
                
                if len(trend_values) < 5:
                    continue
                
                # Calculate trend statistics
                trend_mean = trend_values.mean()
                trend_std = trend_values.std()
                
                if trend_std == 0:
                    continue
                
                # Look for trend reversals (sudden direction changes)
                recent_trends = trend_values.tail(3).tolist()
                
                if len(recent_trends) >= 3:
                    # Check for reversal pattern
                    if (recent_trends[0] > 0 and recent_trends[1] < 0 and recent_trends[2] < 0) or \
                       (recent_trends[0] < 0 and recent_trends[1] > 0 and recent_trends[2] > 0):
                        
                        latest_date = daily_data['date_only'].iloc[-1]
                        latest_value = daily_data[metric].iloc[-1]
                        expected_value = daily_data[f'{metric}_ma'].iloc[-1]
                        
                        if recent_trends[-1] < 0:
                            impact = "negative"
                            description = f"Downward trend detected in {metric.replace('_', ' ')}"
                        else:
                            impact = "positive"
                            description = f"Upward trend detected in {metric.replace('_', ' ')}"
                        
                        # Calculate deviation score
                        deviation_score = abs(recent_trends[-1] / trend_std) if trend_std > 0 else 0
                        severity = self._calculate_severity(deviation_score)
                        suggestions = self._generate_trend_suggestions(impact, metric)
                        
                        anomaly = Anomaly(
                            id=f"trend_{user_id}_{latest_date}_{metric}",
                            type=AnomalyType.TREND_REVERSAL,
                            severity=severity,
                            date=datetime.combine(latest_date, datetime.min.time()),
                            value=latest_value,
                            expected_value=expected_value,
                            deviation_score=deviation_score,
                            description=description,
                            impact=impact,
                            suggestions=suggestions,
                            confidence=0.75,  # Trend analysis has moderate confidence
                            metadata={
                                "trend_window": window,
                                "recent_trend": recent_trends[-1],
                                "trend_direction": "down" if recent_trends[-1] < 0 else "up"
                            }
                        )
                        
                        anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logging.error(f"Error detecting trend anomalies: {e}")
            return []
    
    def _calculate_severity(self, deviation_score: float) -> AnomalySeverity:
        """Calculate severity based on deviation score"""
        if deviation_score >= 4.0:
            return AnomalySeverity.CRITICAL
        elif deviation_score >= 3.0:
            return AnomalySeverity.HIGH
        elif deviation_score >= 2.0:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def _generate_volume_suggestions(self, anomaly_type: AnomalyType, zscore: float, date) -> List[str]:
        """Generate suggestions for volume anomalies"""
        suggestions = []
        
        if anomaly_type == AnomalyType.SALES_DROP:
            suggestions.extend([
                "Check if there were external factors affecting sales",
                "Review marketing activities for that day",
                "Analyze competitor activities",
                "Consider increasing promotional efforts"
            ])
        else:  # SALES_SPIKE
            suggestions.extend([
                "Identify what caused the sales spike",
                "Document successful strategies used",
                "Consider replicating successful conditions",
                "Ensure inventory can handle similar spikes"
            ])
        
        if zscore >= 3.0:
            suggestions.append("This is a significant deviation requiring immediate attention")
        
        return suggestions[:4]  # Limit to 4 suggestions
    
    def _generate_revenue_suggestions(self, actual_revenue: float, expected_revenue: float, date) -> List[str]:
        """Generate suggestions for revenue anomalies"""
        suggestions = []
        
        if actual_revenue < expected_revenue:
            suggestions.extend([
                "Review pricing strategy for that period",
                "Check for any discounts or promotions that may have affected revenue",
                "Analyze customer behavior patterns",
                "Consider implementing revenue recovery strategies"
            ])
        else:
            suggestions.extend([
                "Identify high-revenue drivers from this period",
                "Document successful revenue strategies",
                "Consider scaling successful approaches",
                "Analyze customer segments that contributed most"
            ])
        
        return suggestions[:4]
    
    def _generate_product_suggestions(self, product_name: str, metric: str, impact: str) -> List[str]:
        """Generate suggestions for product anomalies"""
        suggestions = []
        
        if impact == "negative":
            suggestions.extend([
                f"Review marketing strategy for {product_name}",
                f"Consider price adjustments for {product_name}",
                f"Analyze customer feedback for {product_name}",
                f"Evaluate product placement and promotion"
            ])
        else:
            suggestions.extend([
                f"Scale marketing efforts for {product_name}",
                f"Analyze success factors for {product_name}",
                f"Consider expanding {product_name} variants",
                f"Use {product_name} as a promotional anchor"
            ])
        
        return suggestions[:4]
    
    def _generate_pattern_suggestions(self, day_name: str, metric: str, impact: str) -> List[str]:
        """Generate suggestions for pattern anomalies"""
        suggestions = []
        
        if impact == "negative":
            suggestions.extend([
                f"Develop targeted promotions for {day_name}",
                f"Analyze why {day_name} underperforms",
                f"Consider special {day_name} offers",
                f"Review staffing levels for {day_name}"
            ])
        else:
            suggestions.extend([
                f"Leverage {day_name} success patterns",
                f"Analyze what makes {day_name} successful",
                f"Apply {day_name} strategies to other days",
                f"Maximize {day_name} performance further"
            ])
        
        return suggestions[:4]
    
    def _generate_trend_suggestions(self, impact: str, metric: str) -> List[str]:
        """Generate suggestions for trend anomalies"""
        suggestions = []
        
        if impact == "negative":
            suggestions.extend([
                "Implement immediate corrective actions",
                "Review recent business changes",
                "Analyze market conditions",
                "Consider strategic pivots"
            ])
        else:
            suggestions.extend([
                "Capitalize on positive momentum",
                "Scale successful strategies",
                "Document growth factors",
                "Prepare for sustained growth"
            ])
        
        return suggestions[:4]
    
    def _save_anomalies(self, user_id: str, anomalies: List[Anomaly]) -> bool:
        """Save detected anomalies to database"""
        try:
            if not self.db_manager or not self.db_manager.collections:
                return False
            
            for anomaly in anomalies:
                anomaly_doc = {
                    "user_id": user_id,
                    "anomaly_id": anomaly.id,
                    "type": anomaly.type.value,
                    "severity": anomaly.severity.value,
                    "date": anomaly.date,
                    "value": anomaly.value,
                    "expected_value": anomaly.expected_value,
                    "deviation_score": anomaly.deviation_score,
                    "description": anomaly.description,
                    "impact": anomaly.impact,
                    "suggestions": anomaly.suggestions,
                    "confidence": anomaly.confidence,
                    "metadata": anomaly.metadata,
                    "detected_at": datetime.utcnow(),
                    "status": "new"  # new, acknowledged, resolved
                }
                
                # Use upsert to avoid duplicates
                self.db_manager.collections['business_data'].update_one(
                    {"user_id": user_id, "data_type": "anomaly", "data_value.anomaly_id": anomaly.id},
                    {"$set": {
                        "user_id": user_id,
                        "data_type": "anomaly", 
                        "data_value": anomaly_doc,
                        "created_at": datetime.utcnow()
                    }},
                    upsert=True
                )
            
            logging.info(f"Saved {len(anomalies)} anomalies for user {user_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving anomalies: {e}")
            return False
    
    def get_user_anomalies(self, user_id: str, status: str = None, limit: int = 20) -> List[Anomaly]:
        """Get anomalies for a user"""
        try:
            if not self.db_manager or not self.db_manager.collections:
                return []
            
            query = {"user_id": user_id, "data_type": "anomaly"}
            if status:
                query["data_value.status"] = status
            
            anomaly_docs = list(
                self.db_manager.collections['business_data']
                .find(query)
                .sort("data_value.detected_at", -1)
                .limit(limit)
            )
            
            anomalies = []
            for doc in anomaly_docs:
                data = doc.get("data_value", {})
                
                anomaly = Anomaly(
                    id=data.get("anomaly_id", ""),
                    type=AnomalyType(data.get("type", "sales_drop")),
                    severity=AnomalySeverity(data.get("severity", "medium")),
                    date=data.get("date", datetime.utcnow()),
                    value=data.get("value", 0),
                    expected_value=data.get("expected_value", 0),
                    deviation_score=data.get("deviation_score", 0),
                    description=data.get("description", ""),
                    impact=data.get("impact", ""),
                    suggestions=data.get("suggestions", []),
                    confidence=data.get("confidence", 0),
                    metadata=data.get("metadata", {})
                )
                
                anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logging.error(f"Error getting user anomalies: {e}")
            return []

# Initialize anomaly detector
def create_anomaly_detector(db_manager):
    return StatisticalAnomalyDetector(db_manager)