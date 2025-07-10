"""
Base Handler Abstract Class

Provides common interface and utilities for all specialized handlers.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional
import logging


class BaseHandler(ABC):
    """Abstract base class for all chatbot handlers"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.db_enabled = db_manager is not None and hasattr(db_manager, 'initialize_db')
        
    @abstractmethod
    def handle(self, user_id: str, message: str, user_context: Dict) -> Tuple[str, List[str]]:
        """
        Handle the user request for this specific domain
        
        Args:
            user_id: User ID
            message: User's message
            user_context: User session context
            
        Returns:
            Tuple of (response_text, suggestions_list)
        """
        pass
    
    def _format_currency(self, amount: float) -> str:
        """Format currency values consistently"""
        return f"${amount:,.2f}"
    
    def _format_percentage(self, percentage: float) -> str:
        """Format percentage values consistently"""
        return f"{percentage:.1f}%"
    
    def _get_error_response(self, error_msg: str = None) -> Tuple[str, List[str]]:
        """Generate standardized error response"""
        if error_msg:
            response = f"❌ {error_msg}"
        else:
            response = "❌ Sorry, I encountered an issue. Please try again."
        
        suggestions = ["🔄 Try Again", "🔙 Main Menu", "💡 Get Help"]
        return response, suggestions
    
    def _log_handler_activity(self, user_id: str, action: str, details: Dict = None):
        """Log handler activity for debugging"""
        log_msg = f"Handler {self.__class__.__name__}: {action} for user {user_id}"
        if details:
            log_msg += f" - {details}"
        logging.info(log_msg)