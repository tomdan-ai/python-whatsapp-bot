from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from bson import ObjectId

class SalesDataManager:
    """Manager for sales data operations"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def save_sales_record(self, user_id: str, sales_data: Dict) -> bool:
        """Save individual sales record"""
        try:
            sales_record = {
                "user_id": user_id,
                "date": sales_data.get("date", datetime.utcnow()),
                "product_name": sales_data.get("product_name", ""),
                "quantity": float(sales_data.get("quantity", 0)),
                "unit_price": float(sales_data.get("unit_price", 0)),
                "total_amount": float(sales_data.get("total_amount", 0)),
                "customer_name": sales_data.get("customer_name", ""),
                "category": sales_data.get("category", "general"),
                "payment_method": sales_data.get("payment_method", "cash"),
                "notes": sales_data.get("notes", ""),
                "created_at": datetime.utcnow(),
                "source": sales_data.get("source", "manual")  # manual, csv, api
            }
            
            # Calculate total if not provided
            if not sales_record["total_amount"]:
                sales_record["total_amount"] = sales_record["quantity"] * sales_record["unit_price"]
            
            return self.db_manager.save_business_data(
                user_id, 
                "sales_record", 
                sales_record
            )
            
        except Exception as e:
            logging.error(f"Error saving sales record: {e}")
            return False
    
    def save_bulk_sales_data(self, user_id: str, sales_list: List[Dict]) -> Dict:
        """Save multiple sales records"""
        success_count = 0
        error_count = 0
        errors = []
        
        for i, sales_data in enumerate(sales_list):
            try:
                if self.save_sales_record(user_id, sales_data):
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f"Row {i+1}: Failed to save")
            except Exception as e:
                error_count += 1
                errors.append(f"Row {i+1}: {str(e)}")
        
        return {
            "total_processed": len(sales_list),
            "success_count": success_count,
            "error_count": error_count,
            "errors": errors
        }
    
    def get_sales_data(self, user_id: str, start_date: datetime = None, end_date: datetime = None, limit: int = 100) -> List[Dict]:
        """Get sales data for user within date range"""
        try:
            if not self.db_manager.collections:
                return []
            
            # Build query
            query = {"user_id": user_id, "data_type": "sales_record"}
            
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = start_date
                if end_date:
                    date_filter["$lte"] = end_date
                query["data_value.date"] = date_filter
            
            sales_data = list(
                self.db_manager.collections['business_data']
                .find(query)
                .sort("data_value.date", -1)
                .limit(limit)
            )
            
            # Extract sales records
            sales_records = []
            for record in sales_data:
                sales_record = record.get("data_value", {})
                sales_record["_id"] = str(record["_id"])
                sales_records.append(sales_record)
            
            return sales_records
            
        except Exception as e:
            logging.error(f"Error retrieving sales data: {e}")
            return []
    
    def get_sales_summary(self, user_id: str, days: int = 30) -> Dict:
        """Get sales summary for the last N days"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            sales_data = self.get_sales_data(user_id, start_date, end_date)
            
            if not sales_data:
                return {
                    "total_sales": 0,
                    "total_revenue": 0,
                    "average_order_value": 0,
                    "top_products": [],
                    "daily_breakdown": [],
                    "period": f"Last {days} days"
                }
            
            # Calculate metrics
            total_revenue = sum(float(record.get("total_amount", 0)) for record in sales_data)
            total_sales = len(sales_data)
            average_order_value = total_revenue / total_sales if total_sales > 0 else 0
            
            # Top products
            product_sales = {}
            for record in sales_data:
                product = record.get("product_name", "Unknown")
                if product in product_sales:
                    product_sales[product]["quantity"] += float(record.get("quantity", 0))
                    product_sales[product]["revenue"] += float(record.get("total_amount", 0))
                    product_sales[product]["count"] += 1
                else:
                    product_sales[product] = {
                        "quantity": float(record.get("quantity", 0)),
                        "revenue": float(record.get("total_amount", 0)),
                        "count": 1
                    }
            
            # Sort by revenue
            top_products = sorted(
                product_sales.items(), 
                key=lambda x: x[1]["revenue"], 
                reverse=True
            )[:5]
            
            # Daily breakdown
            daily_sales = {}
            for record in sales_data:
                date_str = record.get("date", datetime.utcnow()).strftime("%Y-%m-%d")
                if date_str in daily_sales:
                    daily_sales[date_str]["revenue"] += float(record.get("total_amount", 0))
                    daily_sales[date_str]["count"] += 1
                else:
                    daily_sales[date_str] = {
                        "revenue": float(record.get("total_amount", 0)),
                        "count": 1
                    }
            
            daily_breakdown = [
                {"date": date, "revenue": data["revenue"], "count": data["count"]}
                for date, data in sorted(daily_sales.items())
            ]
            
            return {
                "total_sales": total_sales,
                "total_revenue": round(total_revenue, 2),
                "average_order_value": round(average_order_value, 2),
                "top_products": [
                    {
                        "name": product, 
                        "revenue": round(data["revenue"], 2),
                        "quantity": data["quantity"],
                        "count": data["count"]
                    }
                    for product, data in top_products
                ],
                "daily_breakdown": daily_breakdown,
                "period": f"Last {days} days"
            }
            
        except Exception as e:
            logging.error(f"Error generating sales summary: {e}")
            return {}
    
    def detect_sales_trends(self, user_id: str) -> Dict:
        """Detect sales trends and patterns"""
        try:
            # Get data for trend analysis (last 60 days)
            current_period = self.get_sales_summary(user_id, 30)
            previous_period = self.get_sales_summary_for_period(
                user_id, 
                datetime.utcnow() - timedelta(days=60),
                datetime.utcnow() - timedelta(days=30)
            )
            
            trends = {}
            
            # Revenue trend
            current_revenue = current_period.get("total_revenue", 0)
            previous_revenue = previous_period.get("total_revenue", 0)
            
            if previous_revenue > 0:
                revenue_change = ((current_revenue - previous_revenue) / previous_revenue) * 100
                trends["revenue_trend"] = {
                    "change_percent": round(revenue_change, 1),
                    "direction": "up" if revenue_change > 0 else "down",
                    "current": current_revenue,
                    "previous": previous_revenue
                }
            
            # Sales count trend
            current_count = current_period.get("total_sales", 0)
            previous_count = previous_period.get("total_sales", 0)
            
            if previous_count > 0:
                count_change = ((current_count - previous_count) / previous_count) * 100
                trends["sales_count_trend"] = {
                    "change_percent": round(count_change, 1),
                    "direction": "up" if count_change > 0 else "down",
                    "current": current_count,
                    "previous": previous_count
                }
            
            # Average order value trend
            current_aov = current_period.get("average_order_value", 0)
            previous_aov = previous_period.get("average_order_value", 0)
            
            if previous_aov > 0:
                aov_change = ((current_aov - previous_aov) / previous_aov) * 100
                trends["aov_trend"] = {
                    "change_percent": round(aov_change, 1),
                    "direction": "up" if aov_change > 0 else "down",
                    "current": current_aov,
                    "previous": previous_aov
                }
            
            return trends
            
        except Exception as e:
            logging.error(f"Error detecting sales trends: {e}")
            return {}
    
    def get_sales_summary_for_period(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict:
        """Get sales summary for specific period"""
        try:
            sales_data = self.get_sales_data(user_id, start_date, end_date)
            
            if not sales_data:
                return {"total_sales": 0, "total_revenue": 0, "average_order_value": 0}
            
            total_revenue = sum(float(record.get("total_amount", 0)) for record in sales_data)
            total_sales = len(sales_data)
            average_order_value = total_revenue / total_sales if total_sales > 0 else 0
            
            return {
                "total_sales": total_sales,
                "total_revenue": round(total_revenue, 2),
                "average_order_value": round(average_order_value, 2)
            }
            
        except Exception as e:
            logging.error(f"Error generating period sales summary: {e}")
            return {}


class ProductManager:
    """Manager for product data operations"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def save_product(self, user_id: str, product_data: Dict) -> bool:
        """Save product information"""
        try:
            product_record = {
                "user_id": user_id,
                "name": product_data.get("name", ""),
                "category": product_data.get("category", "general"),
                "price": float(product_data.get("price", 0)),
                "cost": float(product_data.get("cost", 0)),
                "stock_quantity": int(product_data.get("stock_quantity", 0)),
                "low_stock_threshold": int(product_data.get("low_stock_threshold", 5)),
                "description": product_data.get("description", ""),
                "sku": product_data.get("sku", ""),
                "status": product_data.get("status", "active"),  # active, inactive, discontinued
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            return self.db_manager.save_business_data(
                user_id,
                "product",
                product_record
            )
            
        except Exception as e:
            logging.error(f"Error saving product: {e}")
            return False
    
    def get_products(self, user_id: str) -> List[Dict]:
        """Get all products for user"""
        try:
            products = self.db_manager.get_business_data(user_id, "product")
            return [product.get("data_value", {}) for product in products]
        except Exception as e:
            logging.error(f"Error retrieving products: {e}")
            return []
    
    def get_low_stock_products(self, user_id: str) -> List[Dict]:
        """Get products with low stock"""
        try:
            products = self.get_products(user_id)
            return [
                product for product in products
                if product.get("stock_quantity", 0) <= product.get("low_stock_threshold", 5)
            ]
        except Exception as e:
            logging.error(f"Error retrieving low stock products: {e}")
            return []