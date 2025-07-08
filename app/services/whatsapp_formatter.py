import logging
from flask import current_app, jsonify
import json
import requests
import re
from typing import List, Dict, Any

from app.services.korra_chatbot import korra_bot

def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")

def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }

    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"
    
    # Add logging for debugging
    logging.info(f"Sending request to: {url}")
    logging.info(f"Request data: {data}")

    try:
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )
        response.raise_for_status()
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except requests.RequestException as e:
        logging.error(f"Request failed due to: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logging.error(f"Error response status: {e.response.status_code}")
            logging.error(f"Error response body: {e.response.text}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        log_http_response(response)
        return response

def process_text_for_whatsapp(text):
    # Remove brackets and format for WhatsApp
    pattern = r"\【.*?\】"
    text = re.sub(pattern, "", text).strip()
    
    # Convert markdown-style formatting
    pattern = r"\*\*(.*?)\*\*"
    replacement = r"*\1*"
    whatsapp_style_text = re.sub(pattern, replacement, text)
    
    return whatsapp_style_text

def process_whatsapp_message(body):
    """Process incoming WhatsApp message with Korra Chatbot"""
    try:
        wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
        name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]
        
        # Handle different message types
        message_data = body["entry"][0]["changes"][0]["value"]["messages"][0]
        
        if message_data["type"] == "text":
            message_body = message_data["text"]["body"]
        elif message_data["type"] == "interactive":
            # Handle button/list responses
            if "button_reply" in message_data["interactive"]:
                message_body = message_data["interactive"]["button_reply"]["title"]
            elif "list_reply" in message_data["interactive"]:
                message_body = message_data["interactive"]["list_reply"]["title"]
            else:
                message_body = "Interactive message received"
        else:
            message_body = f"Received {message_data['type']} message"
        
        # Process with Korra Chatbot
        response_text, suggestions = korra_bot.process_message(wa_id, message_body, name)
        
        # Format response for WhatsApp
        response_text = process_text_for_whatsapp(response_text)
        
        # Send response with suggestions as buttons if available
        if suggestions and len(suggestions) > 0:
            data = whatsapp_formatter.create_interactive_message(wa_id, response_text, suggestions)
        else:
            data = whatsapp_formatter.create_text_message(wa_id, response_text)
        
        send_message(data)
        
    except Exception as e:
        logging.error(f"Error processing WhatsApp message: {e}")
        # Send fallback message
        fallback_text = "Sorry, I encountered an error. Please try again or type 'help' for assistance."
        data = whatsapp_formatter.create_text_message(wa_id, fallback_text)
        send_message(data)

def is_valid_whatsapp_message(body):
    """Check if the incoming webhook event has a valid WhatsApp message structure."""
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )

class WhatsAppFormatter:
    """Format messages for WhatsApp with buttons and interactive elements"""
    
    @staticmethod
    def create_text_message(recipient: str, text: str) -> str:
        """Create a simple text message"""
        return json.dumps({
            "messaging_product": "whatsapp",
            "recipient_type": "individual", 
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text}
        })
    
    @staticmethod
    def create_interactive_message(recipient: str, text: str, suggestions: List[str]) -> str:
        """Create an interactive message with buttons"""
        
        # WhatsApp allows max 3 buttons, so we'll take first 3 suggestions
        buttons = []
        for i, suggestion in enumerate(suggestions[:3]):
            buttons.append({
                "type": "reply",
                "reply": {
                    "id": f"btn_{i}",
                    "title": suggestion[:20]  # WhatsApp button title limit
                }
            })
        
        if len(buttons) > 0:
            message_data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {"text": text},
                    "action": {"buttons": buttons}
                }
            }
        else:
            # Fallback to text message if no buttons
            message_data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient,
                "type": "text", 
                "text": {"preview_url": False, "body": text}
            }
        
        return json.dumps(message_data)
    
    @staticmethod
    def create_list_message(recipient: str, header: str, body: str, options: List[Dict[str, str]]) -> str:
        """Create a list message for more than 3 options"""
        
        sections = [{
            "title": "Options",
            "rows": []
        }]
        
        for i, option in enumerate(options[:10]):  # WhatsApp allows max 10 rows
            sections[0]["rows"].append({
                "id": f"option_{i}",
                "title": option.get("title", "Option")[:24],  # 24 char limit
                "description": option.get("description", "")[:72]  # 72 char limit
            })
        
        message_data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {"type": "text", "text": header},
                "body": {"text": body},
                "footer": {"text": "Powered by Korra AI"},
                "action": {
                    "button": "View Options",
                    "sections": sections
                }
            }
        }
        
        return json.dumps(message_data)

# Initialize formatter
whatsapp_formatter = WhatsAppFormatter()