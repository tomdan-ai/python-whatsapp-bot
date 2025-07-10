"""
Intent Detection Module

Handles classification of user messages into business intents
for appropriate response routing.
"""

import logging
from typing import Dict, List, Optional
import re


class IntentDetector:
    """Detects user intent from messages"""
    
    def __init__(self):
        self.intent_patterns = self._initialize_intent_patterns()
    
    def _initialize_intent_patterns(self) -> Dict[str, List[str]]:
        """Initialize intent detection patterns"""
        return {
            # Sales Forecasting (Enhanced)
            'sales_forecast': [
                'forecast', 'predict', 'prediction', 'future sales', 
                'projection', 'what if', 'scenario'
            ],
            
            # Forecast Comparison
            'forecast_comparison': [
                'accuracy', 'compare forecast', 'actual vs predicted', 
                'how accurate'
            ],
            
            # Scenario Analysis  
            'scenario_analysis': [
                'scenario', 'what if', 'optimistic', 'pessimistic', 
                'best case', 'worst case'
            ],
            
            # Anomaly Detection
            'anomaly_detection': [
                'anomaly', 'unusual', 'strange', 'drop', 'spike', 
                'alert', 'issue'
            ],
            
            # Invoice Generation
            'invoice_generation': [
                'invoice', 'receipt', 'bill', 'generate invoice', 
                'create invoice'
            ],
            
            # Business Insights
            'business_insights': [
                'insights', 'report', 'top products', 'best selling', 
                'revenue', 'profit', 'analytics'
            ],
            
            # Sales Data Input
            'sales_input': [
                'sold', 'sale', 'add sale', 'record sale', 'sold for'
            ],
            
            # File Upload
            'file_upload': [
                'upload', 'spreadsheet', 'csv', 'excel', 'file'
            ],
            
            # Operational Support
            'operational_support': [
                'help', 'how to', 'strategy', 'customers', 'marketing', 
                'grow', 'advice'
            ],
            
            # Greeting
            'greeting': [
                'hi', 'hello', 'hey', 'start', 'begin', 'menu'
            ]
        }
    
    def detect_intent(self, message: str) -> str:
        """
        Detect user intent from message
        
        Args:
            message: User's message text
            
        Returns:
            Detected intent string
        """
        message_lower = message.lower().strip()
        
        # Check for sales data input patterns first (most specific)
        if self._is_sales_input(message_lower):
            return 'sales_input'
        
        # Check other intents
        for intent, keywords in self.intent_patterns.items():
            if any(keyword in message_lower for keyword in keywords):
                return intent
        
        return 'general'
    
    def _is_sales_input(self, message: str) -> bool:
        """Check if message contains sales data input"""
        # Check for common sales input patterns
        sales_patterns = [
            r'([^,]+),\s*(\d+(?:\.\d+)?),\s*\$?(\d+(?:\.\d+)?)',  # Product, qty, price
            r'([^,]+?)\s+(?:for|sold for|\$)\s*\$?(\d+(?:\.\d+)?)',  # Product for $amount
            r'(\d+(?:\.\d+)?)\s+([^,]+?)\s+(?:at|@|\$)\s*\$?(\d+(?:\.\d+)?)',  # Qty Product at $price
            r'^(sold|sale|add sale|record sale):\s*',  # Explicit sale prefixes
        ]
        
        for pattern in sales_patterns:
            if re.search(pattern, message):
                return True
        
        return False
    
    def get_intent_confidence(self, message: str, intent: str) -> float:
        """
        Get confidence score for detected intent
        
        Args:
            message: User's message
            intent: Detected intent
            
        Returns:
            Confidence score between 0 and 1
        """
        if intent == 'general':
            return 0.3  # Low confidence for general intent
        
        message_lower = message.lower()
        keywords = self.intent_patterns.get(intent, [])
        
        if not keywords:
            return 0.5
        
        # Count matching keywords
        matches = sum(1 for keyword in keywords if keyword in message_lower)
        confidence = min(matches / len(keywords) * 2, 1.0)  # Scale to 0-1
        
        return max(confidence, 0.6)  # Minimum confidence for matched intents
    
    def get_suggested_intents(self, message: str, top_n: int = 3) -> List[Dict[str, float]]:
        """
        Get top N suggested intents with confidence scores
        
        Args:
            message: User's message
            top_n: Number of top intents to return
            
        Returns:
            List of intent-confidence pairs
        """
        suggestions = []
        
        for intent in self.intent_patterns.keys():
            confidence = self.get_intent_confidence(message, intent)
            if confidence > 0.3:  # Only include reasonable matches
                suggestions.append({
                    'intent': intent,
                    'confidence': confidence
                })
        
        # Sort by confidence and return top N
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        return suggestions[:top_n]