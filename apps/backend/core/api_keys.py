"""Centralized API keys loader from API_KEYS.md file."""
import os
import re
from pathlib import Path
from typing import Optional

# Path to API_KEYS.md file (in project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
API_KEYS_FILE = PROJECT_ROOT / "API_KEYS.md"


def load_api_key(service_name: str, key_name: str = "API KEY") -> Optional[str]:
    """
    Load API key from API_KEYS.md file.
    
    Args:
        service_name: Name of the service (e.g., "OpenAI", "Stripe")
        key_name: Name of the key field (default: "API KEY")
    
    Returns:
        API key string or None if not found
    """
    if not API_KEYS_FILE.exists():
        return None
    
    try:
        with open(API_KEYS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for the service section - more flexible pattern
        # Match ## Service Name or ## 🤖 Service Name
        service_pattern = rf"##\s+[^\n]*{re.escape(service_name)}[^\n]*\n(.*?)(?=##|\Z)"
        service_match = re.search(service_pattern, content, re.DOTALL | re.IGNORECASE)
        
        if not service_match:
            return None
        
        service_section = service_match.group(1)
        
        # Look for the key - try multiple patterns
        # Pattern 1: **API KEY**: followed by code block
        key_pattern1 = rf"\*\*{re.escape(key_name)}\*\*\s*:?\s*\n```\s*\n(.*?)\n```"
        key_match = re.search(key_pattern1, service_section, re.DOTALL | re.IGNORECASE)
        
        if key_match:
            key = key_match.group(1).strip()
            if key and len(key) > 0:
                return key
        
        # Pattern 2: **API KEY** (no colon) followed by code block
        key_pattern2 = rf"\*\*{re.escape(key_name)}\*\*\s*\n```\s*\n(.*?)\n```"
        key_match2 = re.search(key_pattern2, service_section, re.DOTALL | re.IGNORECASE)
        
        if key_match2:
            key = key_match2.group(1).strip()
            if key and len(key) > 0:
                return key
        
        # Pattern 3: Look for any code block after key name mention
        key_pattern3 = rf".*?{re.escape(key_name)}.*?```\s*\n(.*?)\n```"
        key_match3 = re.search(key_pattern3, service_section, re.DOTALL | re.IGNORECASE)
        
        if key_match3:
            key = key_match3.group(1).strip()
            if key and len(key) > 0:
                return key
        
        return None
    
    except Exception as e:
        # If file can't be read, return None (fallback to env vars)
        import logging
        logging.debug(f"Error loading API key from file: {e}")
        return None


def get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key from API_KEYS.md or environment."""
    # First try API_KEYS.md
    key = load_api_key("OpenAI", "API KEY")
    if key:
        return key
    
    # Fallback to environment variable
    return os.getenv("OPENAI_API_KEY")


def get_stripe_secret_key() -> Optional[str]:
    """Get Stripe secret key from API_KEYS.md or environment."""
    # First try API_KEYS.md
    key = load_api_key("Stripe", "Secret Key")
    if key:
        return key
    
    # Fallback to environment variable
    return os.getenv("STRIPE_SECRET_KEY")


def get_stripe_publishable_key() -> Optional[str]:
    """Get Stripe publishable key from API_KEYS.md or environment."""
    # First try API_KEYS.md
    key = load_api_key("Stripe", "Publishable Key")
    if key:
        return key
    
    # Fallback to environment variable
    return os.getenv("STRIPE_PUBLISHABLE_KEY")


def get_stripe_webhook_secret() -> Optional[str]:
    """Get Stripe webhook secret from API_KEYS.md or environment."""
    # First try API_KEYS.md
    key = load_api_key("Stripe", "Webhook Secret")
    if key:
        return key
    
    # Fallback to environment variable
    return os.getenv("STRIPE_WEBHOOK_SECRET")


def get_paypal_client_id() -> Optional[str]:
    """Get PayPal client ID from API_KEYS.md or environment."""
    # First try API_KEYS.md
    key = load_api_key("PayPal", "Client ID")
    if key:
        return key
    
    # Fallback to environment variable
    return os.getenv("PAYPAL_CLIENT_ID")


def get_paypal_client_secret() -> Optional[str]:
    """Get PayPal client secret from API_KEYS.md or environment."""
    # First try API_KEYS.md
    key = load_api_key("PayPal", "Client Secret")
    if key:
        return key
    
    # Fallback to environment variable
    return os.getenv("PAYPAL_CLIENT_SECRET")


def get_paypal_webhook_id() -> Optional[str]:
    """Get PayPal webhook ID from API_KEYS.md or environment."""
    # First try API_KEYS.md
    key = load_api_key("PayPal", "Webhook ID")
    if key:
        return key
    
    # Fallback to environment variable
    return os.getenv("PAYPAL_WEBHOOK_ID")


def get_sendgrid_api_key() -> Optional[str]:
    """Get SendGrid API key from API_KEYS.md or environment."""
    # First try API_KEYS.md
    key = load_api_key("SendGrid", "API KEY")
    if key:
        return key
    
    # Fallback to environment variable
    return os.getenv("SENDGRID_API_KEY") or os.getenv("EMAIL_SMTP_PASSWORD")

