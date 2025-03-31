import hmac
import hashlib
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class WebhookHandler:
    """Utilities for handling webhooks from Fireflies.ai."""
    
    @staticmethod
    def verify_signature(request_data, signature):
        """
        Verifies the HMAC signature from Fireflies webhook.
        
        Args:
            request_data (bytes): Raw request body bytes
            signature (str): Signature from X-Hub-Signature header
            
        Returns:
            bool: True if signature is valid or verification is disabled, False otherwise
        """
        # If verification is disabled, return True
        if not current_app.config.get('VERIFY_SIGNATURE', False):
            return True
            
        webhook_secret = current_app.config.get('FIREFLIES_WEBHOOK_SECRET')
        if not webhook_secret:
            logger.warning("Webhook signature verification enabled but no secret configured")
            return False
            
        if not signature:
            logger.warning("Missing X-Hub-Signature header")
            return False
            
        try:
            expected = hmac.new(
                webhook_secret.encode("utf-8"),
                request_data,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected)
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False
