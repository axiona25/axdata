"""API Keys validation and configuration checker."""
import os
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from core.api_keys import (
    get_openai_api_key,
    get_stripe_secret_key,
    get_stripe_publishable_key,
    get_stripe_webhook_secret,
    get_paypal_client_id,
    get_paypal_client_secret,
    get_paypal_webhook_id
)


class APIKeyStatus:
    """Status of an API key."""
    VALID = "valid"
    MISSING = "missing"
    PLACEHOLDER = "placeholder"
    INVALID_FORMAT = "invalid_format"


def validate_stripe_secret_key(key: Optional[str]) -> Tuple[APIKeyStatus, str]:
    """Validate Stripe secret key format."""
    if not key:
        return APIKeyStatus.MISSING, "Chiave non configurata"
    
    key_lower = key.lower()
    
    # Check for placeholder
    if "placeholder" in key_lower or "****" in key or len(key) < 20:
        return APIKeyStatus.PLACEHOLDER, "Chiave placeholder o non valida"
    
    # Check format: sk_test_... or sk_live_...
    if not (key.startswith("sk_test_") or key.startswith("sk_live_")):
        return APIKeyStatus.INVALID_FORMAT, "Formato chiave non valido (deve iniziare con sk_test_ o sk_live_)"
    
    return APIKeyStatus.VALID, "Chiave valida"


def validate_stripe_publishable_key(key: Optional[str]) -> Tuple[APIKeyStatus, str]:
    """Validate Stripe publishable key format."""
    if not key:
        return APIKeyStatus.MISSING, "Chiave non configurata"
    
    key_lower = key.lower()
    
    # Check for placeholder
    if "placeholder" in key_lower or "****" in key or len(key) < 20:
        return APIKeyStatus.PLACEHOLDER, "Chiave placeholder o non valida"
    
    # Check format: pk_test_... or pk_live_...
    if not (key.startswith("pk_test_") or key.startswith("pk_live_")):
        return APIKeyStatus.INVALID_FORMAT, "Formato chiave non valido (deve iniziare con pk_test_ o pk_live_)"
    
    return APIKeyStatus.VALID, "Chiave valida"


def validate_stripe_webhook_secret(key: Optional[str]) -> Tuple[APIKeyStatus, str]:
    """Validate Stripe webhook secret format."""
    if not key:
        return APIKeyStatus.MISSING, "Webhook secret non configurato (opzionale)"
    
    key_lower = key.lower()
    
    # Check for placeholder
    if "placeholder" in key_lower or "****" in key:
        return APIKeyStatus.PLACEHOLDER, "Webhook secret placeholder"
    
    # Check format: whsec_...
    if not key.startswith("whsec_"):
        return APIKeyStatus.INVALID_FORMAT, "Formato webhook secret non valido (deve iniziare con whsec_)"
    
    return APIKeyStatus.VALID, "Webhook secret valido"


def validate_paypal_client_id(key: Optional[str]) -> Tuple[APIKeyStatus, str]:
    """Validate PayPal client ID format."""
    if not key:
        return APIKeyStatus.MISSING, "Client ID non configurato"
    
    key_lower = key.lower()
    
    # Check for placeholder
    if "placeholder" in key_lower or "****" in key or len(key) < 10:
        return APIKeyStatus.PLACEHOLDER, "Client ID placeholder o non valido"
    
    return APIKeyStatus.VALID, "Client ID valido"


def validate_paypal_client_secret(key: Optional[str]) -> Tuple[APIKeyStatus, str]:
    """Validate PayPal client secret format."""
    if not key:
        return APIKeyStatus.MISSING, "Client Secret non configurato"
    
    key_lower = key.lower()
    
    # Check for placeholder
    if "placeholder" in key_lower or "****" in key or len(key) < 10:
        return APIKeyStatus.PLACEHOLDER, "Client Secret placeholder o non valido"
    
    return APIKeyStatus.VALID, "Client Secret valido"


def validate_paypal_webhook_id(key: Optional[str]) -> Tuple[APIKeyStatus, str]:
    """Validate PayPal webhook ID format."""
    if not key:
        return APIKeyStatus.MISSING, "Webhook ID non configurato (opzionale)"
    
    key_lower = key.lower()
    
    # Check for placeholder
    if "placeholder" in key_lower or "****" in key:
        return APIKeyStatus.PLACEHOLDER, "Webhook ID placeholder"
    
    return APIKeyStatus.VALID, "Webhook ID valido"


def validate_openai_api_key(key: Optional[str]) -> Tuple[APIKeyStatus, str]:
    """Validate OpenAI API key format."""
    if not key:
        return APIKeyStatus.MISSING, "API key non configurata"
    
    key_lower = key.lower()
    
    # Check for placeholder
    if "placeholder" in key_lower or "****" in key or len(key) < 20:
        return APIKeyStatus.PLACEHOLDER, "API key placeholder o non valida"
    
    # Check format: sk-... or sk-proj-...
    if not (key.startswith("sk-") or key.startswith("sk-proj-")):
        return APIKeyStatus.INVALID_FORMAT, "Formato API key non valido (deve iniziare con sk- o sk-proj-)"
    
    return APIKeyStatus.VALID, "API key valida"


def check_all_api_keys() -> Dict[str, Dict[str, Tuple[APIKeyStatus, str]]]:
    """
    Check all API keys and return their status.
    
    Returns:
        Dictionary with service names as keys and dict of key_name -> (status, message)
    """
    results = {}
    
    # OpenAI
    openai_key = get_openai_api_key()
    results["OpenAI"] = {
        "API KEY": validate_openai_api_key(openai_key)
    }
    
    # Stripe
    stripe_secret = get_stripe_secret_key()
    stripe_publishable = get_stripe_publishable_key()
    stripe_webhook = get_stripe_webhook_secret()
    
    results["Stripe"] = {
        "Secret Key": validate_stripe_secret_key(stripe_secret),
        "Publishable Key": validate_stripe_publishable_key(stripe_publishable),
        "Webhook Secret": validate_stripe_webhook_secret(stripe_webhook)
    }
    
    # PayPal
    paypal_client_id = get_paypal_client_id()
    paypal_client_secret = get_paypal_client_secret()
    paypal_webhook_id = get_paypal_webhook_id()
    
    results["PayPal"] = {
        "Client ID": validate_paypal_client_id(paypal_client_id),
        "Client Secret": validate_paypal_client_secret(paypal_client_secret),
        "Webhook ID": validate_paypal_webhook_id(paypal_webhook_id)
    }
    
    return results


def get_missing_keys() -> List[Tuple[str, str, str]]:
    """
    Get list of missing or placeholder keys.
    
    Returns:
        List of tuples (service_name, key_name, status_message)
    """
    all_keys = check_all_api_keys()
    missing = []
    
    for service, keys in all_keys.items():
        for key_name, (status, message) in keys.items():
            if status in [APIKeyStatus.MISSING, APIKeyStatus.PLACEHOLDER]:
                missing.append((service, key_name, message))
    
    return missing


def get_configuration_status() -> Dict[str, any]:
    """
    Get overall configuration status.
    
    Returns:
        Dictionary with status summary
    """
    all_keys = check_all_api_keys()
    missing = get_missing_keys()
    
    total_keys = sum(len(keys) for keys in all_keys.values())
    valid_keys = sum(
        1 for keys in all_keys.values()
        for status, _ in keys.values()
        if status == APIKeyStatus.VALID
    )
    
    return {
        "total_keys": total_keys,
        "valid_keys": valid_keys,
        "missing_keys": len(missing),
        "completion_percentage": (valid_keys / total_keys * 100) if total_keys > 0 else 0,
        "missing": missing,
        "details": all_keys
    }

