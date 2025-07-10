"""
Session Management Module

Handles user session persistence, conversation history,
and analytics tracking with MongoDB integration.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime


class SessionManager:
    """Manages user sessions and conversation history"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.db_enabled = False
        self.user_sessions = {}  # In-memory fallback
        
        # Initialize database connection
        if self.db_manager:
            self.initialize_database()
    
    def initialize_database(self):
        """Initialize database connection when available"""
        if self.db_manager:
            # Check if we have an application context before trying to initialize
            try:
                from flask import current_app
                if not current_app:
                    logging.warning("No Flask app context available, skipping DB initialization")
                    self.db_enabled = False
                    return False
            except (ImportError, RuntimeError):
                logging.warning("No Flask app context available, skipping DB initialization")
                self.db_enabled = False
                return False
            
            # Now try to initialize the database
            try:
                self.db_enabled = self.db_manager.initialize_db()
                if self.db_enabled:
                    logging.info("SessionManager: MongoDB initialized successfully")
                else:
                    logging.warning("SessionManager: MongoDB failed, using memory storage")
            except Exception as e:
                logging.error(f"Database initialization error: {e}")
                self.db_enabled = False
    
        return self.db_enabled
    
    def load_user_session(self, user_id: str, user_name: str) -> Dict:
        """
        Load user session from database or create new one
        
        Args:
            user_id: WhatsApp user ID
            user_name: User's display name
            
        Returns:
            User session dictionary
        """
        # Try to load from database first
        if self.db_enabled and self.db_manager:
            session = self.db_manager.get_user_session(user_id)
            if session:
                # Update name if changed
                if session.get('name') != user_name:
                    session['name'] = user_name
                    self.save_user_session(user_id, session)
                return session
        
        # Fallback to memory storage or create new session
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = self._create_new_session(user_id, user_name)
        
        return self.user_sessions[user_id]
    
    def _create_new_session(self, user_id: str, user_name: str) -> Dict:
        """Create a new user session"""
        return {
            'user_id': user_id,
            'name': user_name,
            'created_at': datetime.utcnow(),
            'last_interaction': datetime.utcnow(),
            'last_action': None,
            'context': {},
            'session_count': 1,
            'preferences': {},
            'business_context': {}
        }
    
    def save_user_session(self, user_id: str, session_data: Dict) -> bool:
        """
        Save user session to database
        
        Args:
            user_id: User ID
            session_data: Session data to save
            
        Returns:
            Success status
        """
        # Update timestamp
        session_data['last_interaction'] = datetime.utcnow()
        
        # Save to database if available
        if self.db_enabled and self.db_manager:
            success = self.db_manager.save_user_session(user_id, session_data)
            if success:
                return True
        
        # Fallback to memory storage
        self.user_sessions[user_id] = session_data
        return True
    
    def update_session_context(self, user_id: str, context_updates: Dict) -> bool:
        """
        Update specific context fields in user session
        
        Args:
            user_id: User ID
            context_updates: Context fields to update
            
        Returns:
            Success status
        """
        session = self.load_user_session(user_id, context_updates.get('name', ''))
        session['context'].update(context_updates)
        return self.save_user_session(user_id, session)
    
    def save_conversation(
        self, 
        user_id: str, 
        message: str, 
        message_type: str, 
        intent: str = None, 
        ai_provider: str = None,
        metadata: Dict = None
    ) -> bool:
        """
        Save conversation message to database
        
        Args:
            user_id: User ID
            message: Message content
            message_type: 'user' or 'bot'
            intent: Detected intent (for user messages)
            ai_provider: AI service used (for bot messages)
            metadata: Additional message metadata
            
        Returns:
            Success status
        """
        if self.db_enabled and self.db_manager:
            return self.db_manager.save_conversation(
                user_id, message, message_type, intent, ai_provider, metadata
            )
        
        # Fallback: log conversation
        logging.debug(f"Conversation {message_type} for {user_id}: {message[:50]}...")
        return True
    
    def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Get recent conversation history
        
        Args:
            user_id: User ID
            limit: Maximum number of messages to return
            
        Returns:
            List of conversation messages
        """
        if self.db_enabled and self.db_manager:
            return self.db_manager.get_conversation_history(user_id, limit)
        
        # Fallback: return empty history
        return []
    
    def get_user_stats(self, user_id: str) -> Dict:
        """
        Get user interaction statistics
        
        Args:
            user_id: User ID
            
        Returns:
            User statistics dictionary
        """
        if self.db_enabled and self.db_manager:
            return self.db_manager.get_user_stats(user_id)
        
        # Fallback: basic stats from memory
        session = self.user_sessions.get(user_id, {})
        return {
            "total_messages": 0,
            "user_messages": 0,
            "bot_messages": 0,
            "first_interaction": session.get('created_at'),
            "last_interaction": session.get('last_interaction'),
            "intent_breakdown": {},
            "common_intents": [],
            "session_count": session.get('session_count', 0)
        }
    
    def track_event(self, event_type: str, user_id: str = None, data: Dict = None) -> bool:
        """
        Track analytics events
        
        Args:
            event_type: Type of event
            user_id: User ID (optional)
            data: Event data (optional)
            
        Returns:
            Success status
        """
        if self.db_enabled and self.db_manager:
            return self.db_manager.track_event(event_type, user_id, data)
        
        # Fallback: log event
        logging.info(f"Event: {event_type} for user {user_id}: {data}")
        return True
    
    def get_user_preferences(self, user_id: str) -> Dict:
        """Get user preferences and settings"""
        session = self.load_user_session(user_id, '')
        return session.get('preferences', {})
    
    def update_user_preferences(self, user_id: str, preferences: Dict) -> bool:
        """Update user preferences"""
        session = self.load_user_session(user_id, '')
        session['preferences'].update(preferences)
        return self.save_user_session(user_id, session)
    
    def clear_user_session(self, user_id: str) -> bool:
        """Clear user session data"""
        if self.db_enabled and self.db_manager:
            # Clear database session
            success = self.db_manager.clear_user_session(user_id)
        
        # Clear memory session
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
        
        return True
    
    def get_active_users_count(self, hours: int = 24) -> int:
        """Get count of active users in the last N hours"""
        if self.db_enabled and self.db_manager:
            return self.db_manager.get_active_users_count(hours)
        
        # Fallback: count memory sessions
        return len(self.user_sessions)
