from functools import wraps
from flask import current_app, jsonify, request
import logging
import hashlib
import hmac


def validate_signature(payload, signature):
    """
    Validate the incoming payload's signature against our expected signature
    """
    try:
        # Use the App Secret to hash the payload
        app_secret = current_app.config["APP_SECRET"]
        if not app_secret:
            logging.error("APP_SECRET is not configured!")
            return False
            
        # Create expected signature
        expected_signature = hmac.new(
            bytes(app_secret, "utf-8"),
            msg=payload,
            digestmod=hashlib.sha256,
        ).hexdigest()

        logging.info(f"Expected signature: {expected_signature}")
        logging.info(f"Received signature: {signature}")
        
        # Check if the signature matches
        is_valid = hmac.compare_digest(expected_signature, signature)
        logging.info(f"Signature valid: {is_valid}")
        
        return is_valid
    except Exception as e:
        logging.error(f"Error validating signature: {e}")
        return False


def signature_required(f):
    """
    Decorator to ensure that the incoming requests to our webhook are valid and signed with the correct signature.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the signature from headers
        signature_header = request.headers.get("X-Hub-Signature-256", "")
        logging.info(f"Signature header: {signature_header}")
        
        if not signature_header.startswith("sha256="):
            logging.error("Missing or invalid signature header format")
            return jsonify({"status": "error", "message": "Missing signature"}), 403
            
        # Remove 'sha256=' prefix
        signature = signature_header[7:]
        
        # Get the raw payload
        payload = request.get_data()
        logging.info(f"Payload length: {len(payload)}")
        
        if not validate_signature(payload, signature):
            logging.error("Signature verification failed!")
            return jsonify({"status": "error", "message": "Invalid signature"}), 403
            
        logging.info("Signature verification successful!")
        return f(*args, **kwargs)

    return decorated_function
