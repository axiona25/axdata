"""PayPal payment service."""
import logging
import httpx
import base64
import json
from typing import Optional, Dict, Any
from decimal import Decimal
from core.config import settings
from core.api_keys import get_paypal_client_id, get_paypal_client_secret

logger = logging.getLogger(__name__)

# PayPal API endpoints
PAYPAL_BASE_URL_SANDBOX = "https://api-m.sandbox.paypal.com"
PAYPAL_BASE_URL_LIVE = "https://api-m.paypal.com"

# Get PayPal base URL based on environment
def get_paypal_base_url() -> str:
    """Get PayPal base URL based on environment."""
    if settings.environment == "production":
        return PAYPAL_BASE_URL_LIVE
    return PAYPAL_BASE_URL_SANDBOX


class PayPalClient:
    """PayPal API client."""
    
    def __init__(self):
        self.client_id = get_paypal_client_id() or settings.paypal_client_id
        self.client_secret = get_paypal_client_secret() or settings.paypal_client_secret
        self.base_url = get_paypal_base_url()
        self.access_token = None
        self.token_expires_at = None
        self.http_client = httpx.Client(timeout=30.0)
    
    def get_access_token(self) -> str:
        """Get PayPal access token (with caching)."""
        import time
        
        # Check if token is still valid
        if self.access_token and self.token_expires_at:
            if time.time() < self.token_expires_at:
                return self.access_token
        
        # Get new token
        if not self.client_id or not self.client_secret:
            raise ValueError("PayPal client ID and secret must be configured")
        
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        url = f"{self.base_url}/v1/oauth2/token"
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}
        
        try:
            response = self.http_client.post(url, headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 32400)  # Default 9 hours
            self.token_expires_at = time.time() + expires_in - 300  # Refresh 5 min before expiry
            
            return self.access_token
        except Exception as e:
            logger.error(f"Error getting PayPal access token: {e}", exc_info=True)
            raise
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with access token."""
        token = self.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def create_order(
        self,
        amount: float,
        currency: str,
        description: str,
        return_url: str,
        cancel_url: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create PayPal order.
        
        Args:
            amount: Payment amount
            currency: Currency code (e.g., "EUR", "USD")
            description: Order description
            return_url: Return URL after payment
            cancel_url: Cancel URL
            metadata: Custom metadata
        
        Returns:
            PayPal order object
        """
        url = f"{self.base_url}/v2/checkout/orders"
        headers = self._get_headers()
        
        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "description": description,
                "amount": {
                    "currency_code": currency.upper(),
                    "value": f"{amount:.2f}"
                }
            }],
            "application_context": {
                "return_url": return_url,
                "cancel_url": cancel_url,
                "brand_name": "Dataset On-Demand Portal",
                "user_action": "PAY_NOW"
            }
        }
        
        # Add metadata if provided
        if metadata:
            order_data["purchase_units"][0]["custom_id"] = metadata.get("custom_id", "")
            if "invoice_id" in metadata:
                order_data["purchase_units"][0]["invoice_id"] = metadata["invoice_id"]
        
        try:
            response = self.http_client.post(url, headers=headers, json=order_data)
            response.raise_for_status()
            order = response.json()
            
            logger.info(f"Created PayPal order {order['id']}")
            return order
        except Exception as e:
            logger.error(f"Error creating PayPal order: {e}", exc_info=True)
            raise
    
    def capture_order(self, order_id: str) -> Dict[str, Any]:
        """
        Capture PayPal order.
        
        Args:
            order_id: PayPal order ID
        
        Returns:
            Captured order object
        """
        url = f"{self.base_url}/v2/checkout/orders/{order_id}/capture"
        headers = self._get_headers()
        
        try:
            response = self.http_client.post(url, headers=headers, json={})
            response.raise_for_status()
            order = response.json()
            
            logger.info(f"Captured PayPal order {order_id}")
            return order
        except Exception as e:
            logger.error(f"Error capturing PayPal order: {e}", exc_info=True)
            raise
    
    def get_order(self, order_id: str) -> Dict[str, Any]:
        """
        Get PayPal order details.
        
        Args:
            order_id: PayPal order ID
        
        Returns:
            Order object
        """
        url = f"{self.base_url}/v2/checkout/orders/{order_id}"
        headers = self._get_headers()
        
        try:
            response = self.http_client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting PayPal order: {e}", exc_info=True)
            raise
    
    def verify_webhook_signature(
        self,
        payload: bytes,
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Verify PayPal webhook signature.
        
        Args:
            payload: Raw request body
            headers: Request headers (must include PayPal headers)
        
        Returns:
            Webhook event object if valid
        
        Raises:
            ValueError: If signature is invalid
        """
        webhook_id = settings.paypal_webhook_id
        
        if not webhook_id:
            raise ValueError("PayPal webhook ID not configured")
        
        # PayPal webhook verification
        url = f"{self.base_url}/v1/notifications/verify-webhook-signature"
        headers_paypal = self._get_headers()
        
        # Get PayPal headers
        auth_algo = headers.get("PAYPAL-AUTH-ALGO", "")
        cert_url = headers.get("PAYPAL-CERT-URL", "")
        transmission_id = headers.get("PAYPAL-TRANSMISSION-ID", "")
        transmission_sig = headers.get("PAYPAL-TRANSMISSION-SIG", "")
        transmission_time = headers.get("PAYPAL-TRANSMISSION-TIME", "")
        
        verification_data = {
            "auth_algo": auth_algo,
            "cert_url": cert_url,
            "transmission_id": transmission_id,
            "transmission_sig": transmission_sig,
            "transmission_time": transmission_time,
            "webhook_id": webhook_id,
            "webhook_event": json.loads(payload.decode('utf-8'))
        }
        
        try:
            response = self.http_client.post(url, headers=headers_paypal, json=verification_data)
            response.raise_for_status()
            verification_result = response.json()
            
            if verification_result.get("verification_status") != "SUCCESS":
                raise ValueError("PayPal webhook signature verification failed")
            
            return verification_data["webhook_event"]
        except Exception as e:
            logger.error(f"Error verifying PayPal webhook signature: {e}", exc_info=True)
            raise


# Global PayPal client instance
_paypal_client: Optional[PayPalClient] = None


def get_paypal_client() -> PayPalClient:
    """Get or create PayPal client instance."""
    global _paypal_client
    if _paypal_client is None:
        _paypal_client = PayPalClient()
    return _paypal_client


def create_paypal_order(
    amount: float,
    currency: str,
    description: str,
    return_url: str,
    cancel_url: str,
    metadata: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create PayPal order.
    
    Args:
        amount: Payment amount
        currency: Currency code
        description: Order description
        return_url: Return URL after payment
        cancel_url: Cancel URL
        metadata: Custom metadata
    
    Returns:
        PayPal order object with approval URL
    """
    client = get_paypal_client()
    order = client.create_order(amount, currency, description, return_url, cancel_url, metadata)
    
    # Extract approval URL
    approval_url = None
    for link in order.get("links", []):
        if link.get("rel") == "approve":
            approval_url = link.get("href")
            break
    
    return {
        "id": order["id"],
        "status": order["status"],
        "approval_url": approval_url,
        "order": order
    }


def capture_paypal_order(order_id: str) -> Dict[str, Any]:
    """
    Capture PayPal order.
    
    Args:
        order_id: PayPal order ID
    
    Returns:
        Captured order object
    """
    client = get_paypal_client()
    return client.capture_order(order_id)


def verify_paypal_webhook(payload: bytes, headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Verify PayPal webhook signature.
    
    Args:
        payload: Raw request body
        headers: Request headers
    
    Returns:
        Webhook event object if valid
    """
    client = get_paypal_client()
    return client.verify_webhook_signature(payload, headers)

