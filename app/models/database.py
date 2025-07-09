import logging
from pymongo import MongoClient
from flask import current_app
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
from bson import ObjectId

class MongoDBManager:
    """MongoDB database manager for Korra Chatbot"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.collections = {}
        
    def initialize_db(self):
        """Initialize MongoDB connection and collections"""
        try:
            # Get MongoDB URI from config
            mongodb_uri = current_app.config.get('MONGODB_URI')
            database_name = current_app.config.get('MONGODB_DATABASE', 'korra_bot')
            
            if not mongodb_uri or mongodb_uri == "mongodb+srv://username:password@cluster.mongodb.net/korra_bot?retryWrites=true&w=majority":
                logging.warning("MongoDB URI not configured, using in-memory storage")
                return False
            
            # Connect to MongoDB
            self.client = MongoClient(mongodb_uri)
            self.db = self.client[database_name]
            
            # Test connection
            self.client.admin.command('ping')
            logging.info("MongoDB connection successful")
            
            # Initialize collections
            self._initialize_collections()
            
            return True
            
        except Exception as e:
            logging.error(f"MongoDB connection failed: {e}")
            return False
    
    def _initialize_collections(self):
        """Initialize MongoDB collections with indexes"""
        
        # User Sessions Collection
        self.collections['user_sessions'] = self.db.user_sessions
        self.collections['user_sessions'].create_index("user_id", unique=True)
        self.collections['user_sessions'].create_index("last_interaction")
        
        # Conversation History Collection
        self.collections['conversations'] = self.db.conversations
        self.collections['conversations'].create_index("user_id")
        self.collections['conversations'].create_index("timestamp")
        self.collections['conversations'].create_index([("user_id", 1), ("timestamp", -1)])
        
        # Business Data Collection
        self.collections['business_data'] = self.db.business_data
        self.collections['business_data'].create_index("user_id")
        self.collections['business_data'].create_index("data_type")
        self.collections['business_data'].create_index("created_at")
        
        # Invoices Collection
        self.collections['invoices'] = self.db.invoices
        self.collections['invoices'].create_index("user_id")
        self.collections['invoices'].create_index("status")
        self.collections['invoices'].create_index("created_at")
        
        # Analytics Collection (for tracking bot performance)
        self.collections['analytics'] = self.db.analytics
        self.collections['analytics'].create_index("date")
        self.collections['analytics'].create_index("event_type")
        
        logging.info("MongoDB collections and indexes created successfully")
    
    # User Session Management
    def save_user_session(self, user_id: str, user_data: Dict) -> bool:
        """Save or update user session"""
        try:
            if not self.collections:
                return False
                
            session_data = {
                "user_id": user_id,
                "name": user_data.get('name', ''),
                "phone_number": user_data.get('phone_number', ''),
                "last_interaction": datetime.utcnow(),
                "context": user_data.get('context', {}),
                "session_count": user_data.get('session_count', 1),
                "created_at": user_data.get('created_at', datetime.utcnow()),
                "updated_at": datetime.utcnow()
            }
            
            # Upsert user session
            result = self.collections['user_sessions'].update_one(
                {"user_id": user_id},
                {"$set": session_data},
                upsert=True
            )
            
            logging.info(f"User session saved for {user_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving user session: {e}")
            return False
    
    def get_user_session(self, user_id: str) -> Optional[Dict]:
        """Get user session data"""
        try:
            if not self.collections:
                return None
                
            session = self.collections['user_sessions'].find_one({"user_id": user_id})
            
            if session:
                # Convert ObjectId to string for JSON serialization
                session['_id'] = str(session['_id'])
                return session
                
            return None
            
        except Exception as e:
            logging.error(f"Error retrieving user session: {e}")
            return None
    
    def update_user_context(self, user_id: str, context_update: Dict) -> bool:
        """Update specific context fields for user"""
        try:
            if not self.collections:
                return False
                
            result = self.collections['user_sessions'].update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "context": context_update,
                        "last_interaction": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logging.error(f"Error updating user context: {e}")
            return False
    
    # Conversation History Management
    def save_conversation(self, user_id: str, message: str, message_type: str, intent: str = None, ai_provider: str = None) -> bool:
        """Save conversation message"""
        try:
            if not self.collections:
                return False
                
            conversation_data = {
                "user_id": user_id,
                "message": message,
                "message_type": message_type,  # 'user' or 'bot'
                "intent": intent,
                "ai_provider": ai_provider,
                "timestamp": datetime.utcnow(),
                "session_id": f"{user_id}_{datetime.utcnow().strftime('%Y%m%d')}"
            }
            
            result = self.collections['conversations'].insert_one(conversation_data)
            
            logging.debug(f"Conversation saved for {user_id}: {message_type}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving conversation: {e}")
            return False
    
    def get_conversation_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get recent conversation history for user"""
        try:
            if not self.collections:
                return []
                
            conversations = list(
                self.collections['conversations']
                .find({"user_id": user_id})
                .sort("timestamp", -1)
                .limit(limit)
            )
            
            # Convert ObjectIds to strings
            for conv in conversations:
                conv['_id'] = str(conv['_id'])
                
            return conversations[::-1]  # Return in chronological order
            
        except Exception as e:
            logging.error(f"Error retrieving conversation history: {e}")
            return []
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get user interaction statistics"""
        try:
            if not self.collections:
                return {}
                
            # Count total messages
            total_messages = self.collections['conversations'].count_documents({"user_id": user_id})
            
            # Count messages by type
            user_messages = self.collections['conversations'].count_documents({
                "user_id": user_id, 
                "message_type": "user"
            })
            
            bot_messages = self.collections['conversations'].count_documents({
                "user_id": user_id, 
                "message_type": "bot"
            })
            
            # Get most recent session
            session = self.get_user_session(user_id)
            
            # Count by intent (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            intent_pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "timestamp": {"$gte": thirty_days_ago},
                        "intent": {"$ne": None}
                    }
                },
                {
                    "$group": {
                        "_id": "$intent",
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            intent_stats = list(self.collections['conversations'].aggregate(intent_pipeline))
            
            return {
                "total_messages": total_messages,
                "user_messages": user_messages,
                "bot_messages": bot_messages,
                "first_interaction": session.get('created_at') if session else None,
                "last_interaction": session.get('last_interaction') if session else None,
                "intent_breakdown": {item['_id']: item['count'] for item in intent_stats}
            }
            
        except Exception as e:
            logging.error(f"Error retrieving user stats: {e}")
            return {}
    
    # Business Data Management
    def save_business_data(self, user_id: str, data_type: str, data_value: Any, metadata: Dict = None) -> bool:
        """Save business-related data"""
        try:
            if not self.collections:
                return False
                
            business_data = {
                "user_id": user_id,
                "data_type": data_type,  # 'sales', 'inventory', 'customer', etc.
                "data_value": data_value,
                "metadata": metadata or {},
                "created_at": datetime.utcnow()
            }
            
            result = self.collections['business_data'].insert_one(business_data)
            
            logging.info(f"Business data saved for {user_id}: {data_type}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving business data: {e}")
            return False
    
    def get_business_data(self, user_id: str, data_type: str = None, limit: int = 100) -> List[Dict]:
        """Get business data for user"""
        try:
            if not self.collections:
                return []
                
            query = {"user_id": user_id}
            if data_type:
                query["data_type"] = data_type
                
            data = list(
                self.collections['business_data']
                .find(query)
                .sort("created_at", -1)
                .limit(limit)
            )
            
            # Convert ObjectIds to strings
            for item in data:
                item['_id'] = str(item['_id'])
                
            return data
            
        except Exception as e:
            logging.error(f"Error retrieving business data: {e}")
            return []
    
    # Analytics and Insights
    def track_event(self, event_type: str, user_id: str = None, data: Dict = None) -> bool:
        """Track analytics events"""
        try:
            if not self.collections:
                return False
                
            event_data = {
                "event_type": event_type,
                "user_id": user_id,
                "data": data or {},
                "timestamp": datetime.utcnow(),
                "date": datetime.utcnow().strftime('%Y-%m-%d')
            }
            
            result = self.collections['analytics'].insert_one(event_data)
            return True
            
        except Exception as e:
            logging.error(f"Error tracking event: {e}")
            return False
    
    def get_daily_stats(self, days: int = 7) -> Dict:
        """Get daily usage statistics"""
        try:
            if not self.collections:
                return {}
                
            start_date = datetime.utcnow() - timedelta(days=days)
            
            pipeline = [
                {
                    "$match": {
                        "timestamp": {"$gte": start_date}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "date": "$date",
                            "event_type": "$event_type"
                        },
                        "count": {"$sum": 1}
                    }
                },
                {
                    "$group": {
                        "_id": "$_id.date",
                        "events": {
                            "$push": {
                                "event_type": "$_id.event_type",
                                "count": "$count"
                            }
                        },
                        "total": {"$sum": "$count"}
                    }
                },
                {
                    "$sort": {"_id": 1}
                }
            ]
            
            stats = list(self.collections['analytics'].aggregate(pipeline))
            return {item['_id']: item for item in stats}
            
        except Exception as e:
            logging.error(f"Error retrieving daily stats: {e}")
            return {}
    
    # Cleanup and Maintenance
    def cleanup_old_data(self, days: int = 90) -> bool:
        """Clean up old conversation data"""
        try:
            if not self.collections:
                return False
                
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Remove old conversations
            result = self.collections['conversations'].delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            
            logging.info(f"Cleaned up {result.deleted_count} old conversation records")
            return True
            
        except Exception as e:
            logging.error(f"Error cleaning up old data: {e}")
            return False

# Initialize database manager
db_manager = MongoDBManager()