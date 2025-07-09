import requests
import logging
from flask import current_app
from typing import Dict, List, Optional
import json

class OpenRouterService:
    """OpenRouter AI service with free models for business intelligence responses"""
    
    def __init__(self):
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        # Using free models available on OpenRouter
        self.model = "mistralai/mistral-7b-instruct:free"  # Free model
        # Alternative free models:
        # "google/gemma-7b-it:free"
        # "microsoft/phi-3-mini-128k-instruct:free"
    
    def generate_business_response(self, user_message: str, intent: str = "general", context: Dict = None) -> str:
        """Generate contextual business responses using OpenRouter"""
        
        # Custom system prompts based on intent
        system_prompts = {
            "sales_forecast": """You are Korra, an AI sales forecasting expert. Help users understand sales trends and make predictions. 
            Be specific about data requirements and forecasting methods. Keep responses under 150 words and use emojis.""",
            
            "anomaly_detection": """You are Korra, an AI anomaly detection specialist. Help users identify unusual business patterns. 
            Explain what anomalies mean and suggest investigative steps. Keep responses under 150 words and use emojis.""",
            
            "invoice_generation": """You are Korra, an AI invoice and billing assistant. Help users create professional invoices. 
            Guide them through required information and formatting. Keep responses under 150 words and use emojis.""",
            
            "business_insights": """You are Korra, an AI business intelligence analyst. Help users understand their business metrics. 
            Provide actionable insights and recommendations. Keep responses under 150 words and use emojis.""",
            
            "operational_support": """You are Korra, an AI business operations consultant. Help users with growth strategies and operations. 
            Give practical, actionable advice for small businesses. Keep responses under 150 words and use emojis.""",
            
            "general": """You are Korra, an AI business assistant. You help with sales forecasting, anomaly detection, invoices, 
            business insights, and operational guidance. Be friendly, helpful, and concise. Keep responses under 150 words and use emojis."""
        }
        
        system_prompt = system_prompts.get(intent, system_prompts["general"])
        
        try:
            api_key = current_app.config.get('OPENROUTER_API_KEY')
            if not api_key or api_key == "your_openrouter_api_key_here":
                logging.warning("OpenRouter API key not configured")
                return self._get_fallback_response(user_message, intent)
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "https://github.com/your-username/korra-chatbot",  # Required for some free models
                "X-Title": "Korra Business Chatbot"  # Optional
            }
            
            # Prepare context information
            context_info = ""
            if context:
                context_info = f"\nUser Context: {json.dumps(context, default=str)}"
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{user_message}{context_info}"}
                ],
                "max_tokens": 300,
                "temperature": 0.7,
                "stream": False
            }
            
            logging.info(f"Sending request to OpenRouter API for intent: {intent}")
            
            response = requests.post(
                self.base_url, 
                headers=headers, 
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content'].strip()
                logging.info("OpenRouter API response received successfully")
                return ai_response
            else:
                logging.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                return self._get_fallback_response(user_message, intent)
                
        except requests.exceptions.Timeout:
            logging.error("OpenRouter API timeout")
            return "⏱️ I'm taking a moment to think. Please try again in a few seconds."
            
        except requests.exceptions.RequestException as e:
            logging.error(f"OpenRouter API request error: {e}")
            return self._get_fallback_response(user_message, intent)
            
        except Exception as e:
            logging.error(f"OpenRouter API unexpected error: {e}")
            return self._get_fallback_response(user_message, intent)
    
    def _get_fallback_response(self, user_message: str, intent: str) -> str:
        """Provide fallback responses when API is unavailable"""
        
        fallback_responses = {
            "sales_forecast": "📊 *Sales Forecasting*\n\nI'd love to help with sales forecasting! While my AI is temporarily offline, I can guide you through the process:\n\n• Collect your past sales data (3-6 months)\n• Identify seasonal patterns\n• Consider external factors\n\nWhat time period would you like to forecast?",
            
            "anomaly_detection": "🔍 *Anomaly Detection*\n\nI'm here to help spot unusual patterns! While my AI is temporarily offline, I can help you manually check:\n\n• Sudden sales drops/spikes\n• Unusual customer behavior\n• Inventory discrepancies\n\nWhat specific area concerns you?",
            
            "invoice_generation": "📄 *Invoice Generation*\n\nI can help create professional invoices! While my AI is temporarily offline, let's gather the basics:\n\n• Customer information\n• Items/services provided\n• Pricing and quantities\n\nWho is this invoice for?",
            
            "business_insights": "📈 *Business Insights*\n\nI'm ready to analyze your business! While my AI is temporarily offline, I can help you focus on:\n\n• Top-selling products\n• Revenue trends\n• Customer patterns\n\nWhat specific insights do you need?",
            
            "operational_support": "💡 *Business Guidance*\n\nI'm here to help grow your business! While my AI is temporarily offline, here are proven strategies:\n\n• Customer retention programs\n• Marketing automation\n• Operational efficiency\n\nWhat area would you like to improve?",
            
            "general": "🤖 *Korra Assistant*\n\nI'm experiencing some technical difficulties, but I'm still here to help!\n\nI can assist with:\n📊 Sales Forecasting\n📄 Invoice Creation\n📈 Business Insights\n🔍 Anomaly Detection\n💡 Business Strategy\n\nWhat would you like to work on?"
        }
        
        return fallback_responses.get(intent, fallback_responses["general"])

# Initialize the service
openrouter_service = OpenRouterService()