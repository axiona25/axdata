"""Stripe payment service."""
import logging
import stripe
from typing import Optional, Dict, Any
from decimal import Decimal
from core.config import settings
from core.api_keys import get_stripe_secret_key

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = get_stripe_secret_key() or settings.stripe_secret_key


def create_checkout_session(
    dataset_request_id: str,
    user_id: str,
    amount: float,
    currency: str = "eur",
    success_url: str = None,
    cancel_url: str = None
) -> Dict[str, Any]:
    """
    Create Stripe Checkout session.
    
    Args:
        dataset_request_id: Dataset request ID
        user_id: User ID
        amount: Payment amount
        currency: Currency code
        success_url: Success redirect URL
        cancel_url: Cancel redirect URL
    
    Returns:
        Stripe Checkout session
    """
    if not success_url:
        success_url = f"{settings.cors_origins_list[0] if settings.cors_origins_list else 'http://localhost:3000'}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
    
    if not cancel_url:
        cancel_url = f"{settings.cors_origins_list[0] if settings.cors_origins_list else 'http://localhost:3000'}/payment/cancel"
    
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card', 'apple_pay', 'google_pay'],  # Enable Apple Pay and Google Pay
            line_items=[{
                'price_data': {
                    'currency': currency,
                    'product_data': {
                        'name': f'Dataset Request',
                        'description': f'Dataset: {dataset_request_id}',
                    },
                    'unit_amount': int(amount * 100),  # Convert to cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'dataset_request_id': dataset_request_id,
                'user_id': user_id,
            },
            client_reference_id=dataset_request_id,
        )
        
        logger.info(f"Created Stripe Checkout session {session.id} for dataset {dataset_request_id}")
        return session
    
    except Exception as e:
        logger.error(f"Error creating Stripe Checkout session: {e}", exc_info=True)
        raise


def verify_webhook_signature(payload: bytes, signature: str) -> Dict[str, Any]:
    """
    Verify Stripe webhook signature.
    
    Args:
        payload: Raw request body
        signature: Stripe signature header
    
    Returns:
        Event object if valid
    """
    webhook_secret = settings.stripe_webhook_secret
    
    if not webhook_secret:
        raise ValueError("Stripe webhook secret not configured")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, signature, webhook_secret
        )
        return event
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        raise


def get_payment_intent(payment_intent_id: str) -> Dict[str, Any]:
    """
    Get Stripe payment intent.
    
    Args:
        payment_intent_id: Payment intent ID
    
    Returns:
        Payment intent object
    """
    try:
        return stripe.PaymentIntent.retrieve(payment_intent_id)
    except Exception as e:
        logger.error(f"Error retrieving payment intent: {e}", exc_info=True)
        raise

