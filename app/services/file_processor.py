import pandas as pd
import requests
import logging
from flask import current_app
from typing import Dict, List, Any, Optional
import io
import json
from datetime import datetime

class FileProcessor:
    """Process uploaded files from WhatsApp"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.supported_formats = ['csv', 'xlsx', 'xls']
    
    def process_whatsapp_document(self, media_id: str, user_id: str) -> Dict:
        """Process document uploaded via WhatsApp"""
        try:
            # Download file from WhatsApp
            file_data = self._download_whatsapp_media(media_id)
            
            if not file_data:
                return {"status": "error", "message": "Could not download file"}
            
            # Determine file type and process
            filename = file_data.get('filename', '').lower()
            mime_type = file_data.get('mime_type', '').lower()
            
            if filename.endswith('.csv') or 'csv' in mime_type:
                return self._process_csv_data(file_data['content'], user_id, filename)
            elif filename.endswith(('.xlsx', '.xls')) or 'excel' in mime_type or 'spreadsheet' in mime_type:
                return self._process_excel_data(file_data['content'], user_id, filename)
            else:
                return {
                    "status": "error", 
                    "message": f"Unsupported file type. Please upload CSV or Excel files."
                }
                
        except Exception as e:
            logging.error(f"File processing error: {e}")
            return {"status": "error", "message": f"Error processing file: {str(e)}"}
    
    def _download_whatsapp_media(self, media_id: str) -> Optional[Dict]:
        """Download media file from WhatsApp"""
        try:
            headers = {
                "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}"
            }
            
            # Get media URL
            url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{media_id}"
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                logging.error(f"Failed to get media info: {response.status_code}")
                return None
            
            media_info = response.json()
            media_url = media_info.get('url')
            
            if not media_url:
                logging.error("No media URL in response")
                return None
            
            # Download actual file
            file_response = requests.get(media_url, headers=headers, timeout=60)
            
            if file_response.status_code != 200:
                logging.error(f"Failed to download file: {file_response.status_code}")
                return None
            
            return {
                'content': file_response.content,
                'mime_type': media_info.get('mime_type', ''),
                'filename': media_info.get('filename', 'uploaded_file'),
                'size': len(file_response.content)
            }
            
        except Exception as e:
            logging.error(f"Error downloading WhatsApp media: {e}")
            return None
    
    def _process_csv_data(self, file_content: bytes, user_id: str, filename: str) -> Dict:
        """Process CSV file data"""
        try:
            # Read CSV data
            csv_string = file_content.decode('utf-8')
            df = pd.read_csv(io.StringIO(csv_string))
            
            return self._process_dataframe(df, user_id, filename, 'csv')
            
        except UnicodeDecodeError:
            try:
                # Try different encoding
                csv_string = file_content.decode('latin-1')
                df = pd.read_csv(io.StringIO(csv_string))
                return self._process_dataframe(df, user_id, filename, 'csv')
            except Exception as e:
                logging.error(f"CSV encoding error: {e}")
                return {"status": "error", "message": "Could not read CSV file. Please check file encoding."}
        except Exception as e:
            logging.error(f"CSV processing error: {e}")
            return {"status": "error", "message": f"Error reading CSV: {str(e)}"}
    
    def _process_excel_data(self, file_content: bytes, user_id: str, filename: str) -> Dict:
        """Process Excel file data"""
        try:
            # Read Excel data
            df = pd.read_excel(io.BytesIO(file_content))
            return self._process_dataframe(df, user_id, filename, 'excel')
            
        except Exception as e:
            logging.error(f"Excel processing error: {e}")
            return {"status": "error", "message": f"Error reading Excel file: {str(e)}"}
    
    def _process_dataframe(self, df: pd.DataFrame, user_id: str, filename: str, file_type: str) -> Dict:
        """Process pandas DataFrame and extract sales data"""
        try:
            # Clean column names
            df.columns = df.columns.str.strip().str.lower()
            
            # Log DataFrame info
            logging.info(f"Processing {file_type} file: {filename}")
            logging.info(f"Columns: {list(df.columns)}")
            logging.info(f"Rows: {len(df)}")
            
            # Detect data type based on columns
            if self._is_sales_data(df.columns):
                return self._process_sales_data(df, user_id, filename)
            elif self._is_product_data(df.columns):
                return self._process_product_data(df, user_id, filename)
            else:
                return self._attempt_generic_processing(df, user_id, filename)
                
        except Exception as e:
            logging.error(f"DataFrame processing error: {e}")
            return {"status": "error", "message": f"Error processing data: {str(e)}"}
    
    def _is_sales_data(self, columns: List[str]) -> bool:
        """Check if DataFrame contains sales data"""
        sales_indicators = [
            'date', 'product', 'quantity', 'price', 'amount', 'total', 
            'customer', 'sale', 'revenue', 'item'
        ]
        
        column_str = ' '.join(columns)
        matches = sum(1 for indicator in sales_indicators if indicator in column_str)
        return matches >= 2
    
    def _is_product_data(self, columns: List[str]) -> bool:
        """Check if DataFrame contains product data"""
        product_indicators = [
            'product', 'name', 'price', 'cost', 'stock', 'inventory', 
            'category', 'sku', 'description'
        ]
        
        column_str = ' '.join(columns)
        matches = sum(1 for indicator in product_indicators if indicator in column_str)
        return matches >= 2
    
    def _process_sales_data(self, df: pd.DataFrame, user_id: str, filename: str) -> Dict:
        """Process sales data from DataFrame"""
        try:
            from .sales_models import SalesDataManager
            sales_manager = SalesDataManager(self.db_manager)
            
            # Map columns to expected fields
            column_mapping = self._create_sales_column_mapping(df.columns)
            
            sales_records = []
            errors = []
            
            for index, row in df.iterrows():
                try:
                    sales_record = self._extract_sales_record(row, column_mapping)
                    if sales_record:
                        sales_records.append(sales_record)
                    else:
                        errors.append(f"Row {index + 1}: Could not extract valid sales data")
                        
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            if not sales_records:
                return {
                    "status": "error",
                    "message": "No valid sales records found in file",
                    "errors": errors[:10]  # Show first 10 errors
                }
            
            # Save sales records
            result = sales_manager.save_bulk_sales_data(user_id, sales_records)
            
            # Track file upload event
            if hasattr(self.db_manager, 'track_event'):
                self.db_manager.track_event("file_upload", user_id, {
                    "filename": filename,
                    "type": "sales_data",
                    "records_processed": len(sales_records),
                    "success_count": result.get("success_count", 0),
                    "error_count": result.get("error_count", 0)
                })
            
            return {
                "status": "success",
                "message": f"Processed {result['success_count']} sales records from {filename}",
                "data": {
                    "filename": filename,
                    "type": "sales_data",
                    "total_processed": result["total_processed"],
                    "success_count": result["success_count"],
                    "error_count": result["error_count"],
                    "errors": result["errors"][:5] if result["errors"] else []
                }
            }
            
        except Exception as e:
            logging.error(f"Sales data processing error: {e}")
            return {"status": "error", "message": f"Error processing sales data: {str(e)}"}
    
    def _create_sales_column_mapping(self, columns: List[str]) -> Dict:
        """Create mapping from DataFrame columns to sales record fields"""
        mapping = {}
        
        # Common column name variations
        date_cols = ['date', 'sale_date', 'transaction_date', 'order_date']
        product_cols = ['product', 'product_name', 'item', 'item_name', 'name']
        quantity_cols = ['quantity', 'qty', 'amount', 'units']
        price_cols = ['price', 'unit_price', 'cost', 'rate']
        total_cols = ['total', 'total_amount', 'revenue', 'sales', 'value']
        customer_cols = ['customer', 'customer_name', 'client', 'buyer']
        
        for col in columns:
            if any(date_col in col for date_col in date_cols):
                mapping['date'] = col
            elif any(product_col in col for product_col in product_cols):
                mapping['product_name'] = col
            elif any(qty_col in col for qty_col in quantity_cols):
                mapping['quantity'] = col
            elif any(price_col in col for price_col in price_cols):
                mapping['unit_price'] = col
            elif any(total_col in col for total_col in total_cols):
                mapping['total_amount'] = col
            elif any(customer_col in col for customer_col in customer_cols):
                mapping['customer_name'] = col
        
        return mapping
    
    def _extract_sales_record(self, row: pd.Series, column_mapping: Dict) -> Optional[Dict]:
        """Extract sales record from DataFrame row"""
        try:
            record = {}
            
            # Extract date
            if 'date' in column_mapping:
                date_value = row[column_mapping['date']]
                if pd.notna(date_value):
                    if isinstance(date_value, str):
                        record['date'] = pd.to_datetime(date_value).to_pydatetime()
                    else:
                        record['date'] = date_value
                else:
                    record['date'] = datetime.utcnow()
            else:
                record['date'] = datetime.utcnow()
            
            # Extract product name
            if 'product_name' in column_mapping:
                product = row[column_mapping['product_name']]
                record['product_name'] = str(product) if pd.notna(product) else ""
            else:
                record['product_name'] = "Unknown Product"
            
            # Extract quantity
            if 'quantity' in column_mapping:
                qty = row[column_mapping['quantity']]
                record['quantity'] = float(qty) if pd.notna(qty) and qty != "" else 1.0
            else:
                record['quantity'] = 1.0
            
            # Extract unit price
            if 'unit_price' in column_mapping:
                price = row[column_mapping['unit_price']]
                record['unit_price'] = float(price) if pd.notna(price) and price != "" else 0.0
            else:
                record['unit_price'] = 0.0
            
            # Extract total amount
            if 'total_amount' in column_mapping:
                total = row[column_mapping['total_amount']]
                record['total_amount'] = float(total) if pd.notna(total) and total != "" else 0.0
            else:
                record['total_amount'] = record['quantity'] * record['unit_price']
            
            # Extract customer name
            if 'customer_name' in column_mapping:
                customer = row[column_mapping['customer_name']]
                record['customer_name'] = str(customer) if pd.notna(customer) else ""
            else:
                record['customer_name'] = ""
            
            # Additional fields
            record['source'] = 'csv_upload'
            record['category'] = 'general'
            record['payment_method'] = 'unknown'
            record['notes'] = f"Imported from file"
            
            # Validate record
            if record['total_amount'] <= 0 and record['unit_price'] <= 0:
                return None
            
            return record
            
        except Exception as e:
            logging.error(f"Error extracting sales record: {e}")
            return None
    
    def _process_product_data(self, df: pd.DataFrame, user_id: str, filename: str) -> Dict:
        """Process product data from DataFrame"""
        try:
            from .sales_models import ProductManager
            product_manager = ProductManager(self.db_manager)
            
            # Implementation for product data processing
            return {
                "status": "success",
                "message": f"Product data processing not yet implemented for {filename}",
                "data": {"filename": filename, "type": "product_data"}
            }
            
        except Exception as e:
            logging.error(f"Product data processing error: {e}")
            return {"status": "error", "message": f"Error processing product data: {str(e)}"}
    
    def _attempt_generic_processing(self, df: pd.DataFrame, user_id: str, filename: str) -> Dict:
        """Attempt to process unknown data format"""
        try:
            # Analyze the data and provide suggestions
            suggestions = []
            
            # Check if it might be sales data with different column names
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            date_cols = []
            text_cols = df.select_dtypes(include=['object']).columns.tolist()
            
            # Try to find date columns
            for col in text_cols:
                try:
                    pd.to_datetime(df[col].dropna().iloc[0])
                    date_cols.append(col)
                except:
                    pass
            
            if len(numeric_cols) >= 2 and len(text_cols) >= 1:
                suggestions.append("This might be sales data. Expected columns: date, product_name, quantity, unit_price, total_amount")
            
            return {
                "status": "warning",
                "message": f"Could not automatically detect data type in {filename}",
                "data": {
                    "filename": filename,
                    "columns": list(df.columns),
                    "numeric_columns": numeric_cols,
                    "date_columns": date_cols,
                    "text_columns": text_cols,
                    "row_count": len(df),
                    "suggestions": suggestions
                }
            }
            
        except Exception as e:
            logging.error(f"Generic processing error: {e}")
            return {"status": "error", "message": f"Error analyzing file: {str(e)}"}

# Initialize file processor
def create_file_processor(db_manager):
    return FileProcessor(db_manager)