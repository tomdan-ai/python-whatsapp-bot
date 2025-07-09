import logging
from flask import current_app, jsonify
import json
import requests
import re

from app.services.korra_chatbot import korra_bot
from app.services.whatsapp_formatter import whatsapp_formatter


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
    logging.debug(f"Request data: {data}")

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
    """Process incoming WhatsApp message with enhanced Korra Chatbot and MongoDB logging"""
    try:
        wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
        name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]
        
        # Extract phone number if available
        phone_number = body["entry"][0]["changes"][0]["value"]["contacts"][0].get("wa_id", wa_id)
        
        # Handle different message types
        message_data = body["entry"][0]["changes"][0]["value"]["messages"][0]
        message_id = message_data.get("id", "unknown")
        
        if message_data["type"] == "text":
            message_body = message_data["text"]["body"]
            message_type = "text"
        elif message_data["type"] == "interactive":
            message_type = "interactive"
            # Handle button/list responses
            if "button_reply" in message_data["interactive"]:
                message_body = message_data["interactive"]["button_reply"]["title"]
                button_id = message_data["interactive"]["button_reply"]["id"]
                logging.info(f"Button clicked: {button_id} - {message_body}")
            elif "list_reply" in message_data["interactive"]:
                message_body = message_data["interactive"]["list_reply"]["title"]
                list_id = message_data["interactive"]["list_reply"]["id"]
                logging.info(f"List item selected: {list_id} - {message_body}")
            else:
                message_body = "Interactive message received"
        elif message_data["type"] == "document":
            message_type = "document"
            message_body = "Document uploaded"
            # Could process document here in future
        elif message_data["type"] == "image":
            message_type = "image"
            message_body = "Image uploaded"
            # Could process image here in future
        else:
            message_type = message_data["type"]
            message_body = f"Received {message_data['type']} message"
        
        logging.info(f"Processing {message_type} message from {name} ({wa_id}): {message_body[:100]}")
        
        # Track message analytics
        if hasattr(korra_bot, '_track_event'):
            korra_bot._track_event("whatsapp_message_received", wa_id, {
                "message_type": message_type,
                "message_id": message_id,
                "user_name": name,
                "message_length": len(message_body)
            })
        
        # Process with enhanced Korra Chatbot (now with MongoDB persistence)
        response_text, suggestions = korra_bot.process_message(wa_id, message_body, name)
        
        # Format response for WhatsApp
        response_text = process_text_for_whatsapp(response_text)
        
        # Send response with suggestions as buttons if available
        if suggestions and len(suggestions) > 0:
            # WhatsApp supports max 3 buttons, use list for more options
            if len(suggestions) <= 3:
                data = whatsapp_formatter.create_interactive_message(wa_id, response_text, suggestions)
            else:
                # Convert to list format for more than 3 options
                list_options = [{"title": suggestion, "description": ""} for suggestion in suggestions[:10]]
                data = whatsapp_formatter.create_list_message(
                    wa_id, 
                    "Korra Assistant", 
                    response_text, 
                    list_options
                )
        else:
            data = whatsapp_formatter.create_text_message(wa_id, response_text)
        
        # Send message
        send_response = send_message(data)
        
        # Track response analytics
        if hasattr(korra_bot, '_track_event'):
            korra_bot._track_event("whatsapp_response_sent", wa_id, {
                "response_type": "interactive" if suggestions else "text",
                "suggestions_count": len(suggestions) if suggestions else 0,
                "response_length": len(response_text),
                "success": True if send_response else False
            })
        
        logging.info(f"Successfully processed message for {name} ({wa_id})")
        
    except KeyError as e:
        logging.error(f"Missing key in WhatsApp message structure: {e}")
        logging.error(f"Message body: {json.dumps(body, indent=2)}")
        
        # Try to extract basic info for fallback
        try:
            wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
            fallback_text = "I'm sorry, I couldn't process your message properly. Please try sending a simple text message."
            data = whatsapp_formatter.create_text_message(wa_id, fallback_text)
            send_message(data)
        except:
            logging.error("Could not send fallback message")
            
    except Exception as e:
        logging.error(f"Error processing WhatsApp message: {e}")
        
        # Try to send fallback message if we can extract user ID
        try:
            wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
            fallback_text = "Sorry, I encountered an error. Please try again or type 'help' for assistance."
            data = whatsapp_formatter.create_text_message(wa_id, fallback_text)
            send_message(data)
            
            # Track error
            if hasattr(korra_bot, '_track_event'):
                korra_bot._track_event("processing_error", wa_id, {
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                })
                
        except:
            logging.error("Could not send fallback message due to structure error")


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


def get_user_analytics(user_id: str) -> dict:
    """Get analytics for a specific user"""
    try:
        if hasattr(korra_bot, 'get_user_stats'):
            return korra_bot.get_user_stats(user_id)
        return {}
    except Exception as e:
        logging.error(f"Error getting user analytics: {e}")
        return {}


def get_conversation_context(user_id: str, limit: int = 5) -> list:
    """Get recent conversation context for a user"""
    try:
        if hasattr(korra_bot, 'get_conversation_history'):
            return korra_bot.get_conversation_history(user_id, limit)
        return []
    except Exception as e:
        logging.error(f"Error getting conversation context: {e}")
        return []
