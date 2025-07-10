"""
File Upload Handler

Handles file uploads from WhatsApp, including spreadsheets and CSV files
for bulk sales data import.
"""

from typing import Dict, List, Tuple
import logging
from .base_handler import BaseHandler


class FileHandler(BaseHandler):
    """Handles file uploads and processing"""
    
    def __init__(self, db_manager=None):
        super().__init__(db_manager)
        self.file_processor = None
        self._initialize_file_processor()
    
    def _initialize_file_processor(self):
        """Initialize the file processor"""
        try:
            from ...file_processor import create_file_processor
            self.file_processor = create_file_processor(self.db_manager)
            self._log_handler_activity("system", "File processor initialized")
        except ImportError as e:
            logging.warning(f"Could not load file processor: {e}")
    
    def handle(self, user_id: str, message: str, user_context: Dict) -> Tuple[str, List[str]]:
        """Handle file upload requests"""
        response = "📤 *File Upload*\n\nI can process spreadsheets and CSV files with your sales data.\n\nSupported formats:\n• Excel (.xlsx, .xls)\n• CSV (.csv)\n• Google Sheets (exported)\n\nPlease upload your file and I'll analyze it!"
        
        suggestions = [
            "💡 File Format Help",
            "📋 Template Download",
            "🔙 Main Menu"
        ]
        
        return response, suggestions
    
    def handle_upload(self, user_id: str, media_id: str, filename: str, user_context: Dict) -> Tuple[str, List[str]]:
        """Handle actual file upload processing"""
        self._log_handler_activity(user_id, "file_upload", {"filename": filename})
        
        if not self.file_processor:
            return self._get_service_unavailable_response()
        
        try:
            result = self.file_processor.process_whatsapp_document(media_id, user_id)
            
            if result["status"] == "success":
                return self._format_success_response(result.get("data", {}))
            elif result["status"] == "warning":
                return self._format_warning_response(result.get("data", {}))
            else:
                return self._format_error_response(result.get("message", "Unknown error"))
                
        except Exception as e:
            logging.error(f"File upload error: {e}")
            return self._get_error_response()
    
    def _format_success_response(self, data: Dict) -> Tuple[str, List[str]]:
        """Format successful file processing response"""
        response = f"✅ *File Processed Successfully*\n\n"
        response += f"📁 File: {data.get('filename', 'Unknown')}\n"
        response += f"📊 Records Processed: {data.get('success_count', 0)}\n"
        
        if data.get("error_count", 0) > 0:
            response += f"⚠️ Errors: {data['error_count']} records had issues\n"
        
        response += f"💰 Total Value: {self._format_currency(data.get('total_value', 0))}\n\n"
        response += "What would you like to do next?"
        
        suggestions = [
            "📈 View Insights",
            "📊 Sales Summary",
            "➕ Add More Data",
            "🔙 Main Menu"
        ]
        
        return response, suggestions
    
    def _format_warning_response(self, data: Dict) -> Tuple[str, List[str]]:
        """Format warning response for partially processed files"""
        response = f"⚠️ *Partial Processing Complete*\n\n"
        response += f"📁 File: {data.get('filename', 'Unknown')}\n"
        response += f"📊 Found: {data.get('row_count', 0)} rows\n"
        response += f"✅ Processed: {data.get('success_count', 0)} records\n"
        
        if data.get('columns'):
            response += f"\nColumns detected: {', '.join(data['columns'][:5])}\n"
        
        response += "\nSome data couldn't be processed automatically. Please check the format."
        
        suggestions = [
            "💡 Format Help",
            "📤 Try Another File",
            "📊 View Processed Data",
            "🔙 Main Menu"
        ]
        
        return response, suggestions
    
    def _format_error_response(self, error_message: str) -> Tuple[str, List[str]]:
        """Format error response"""
        response = f"❌ *File Processing Failed*\n\n{error_message}\n\nPlease check your file format and try again."
        
        suggestions = [
            "💡 Format Help",
            "📤 Try Another File",
            "🔙 Main Menu"
        ]
        
        return response, suggestions
    
    def _get_service_unavailable_response(self) -> Tuple[str, List[str]]:
        """Response when file processing service is unavailable"""
        response = "📤 *File Processing Unavailable*\n\n⚠️ The file processing service is currently unavailable. Please try again later."
        
        suggestions = ["🔄 Try Again", "➕ Manual Entry", "🔙 Main Menu"]
        return response, suggestions