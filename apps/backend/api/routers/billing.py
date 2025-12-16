"""Billing and payment endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
import uuid
import logging

from db.session import get_db
from db.models.user import User
from db.models.dataset import DatasetRequest, DatasetStatus
from db.models.payment import Payment, PaymentStatus, PaymentProvider
from core.dependencies import get_current_active_user
from schemas.payment import PaymentResponse, CheckoutResponse
from schemas.invoice import InvoiceResponse, InvoiceListResponse
from db.models.invoice import Invoice
from services.stripe_service import create_checkout_session, verify_webhook_signature
from services.paypal_service import create_paypal_order, capture_paypal_order, verify_paypal_webhook
from services.dataset_service import update_dataset_status
from decimal import Decimal
import stripe
from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    user_package_id: Optional[str] = None,
    dataset_request_id: Optional[str] = None,
    provider: str = "stripe",  # "stripe" or "paypal"
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create checkout session (Stripe or PayPal).
    
    Can be used for:
    - Package purchase (user_package_id)
    - Dataset payment (dataset_request_id) - legacy, now datasets are included in packages
    
    Providers:
    - stripe: Stripe Checkout (supports card, Apple Pay, Google Pay)
    - paypal: PayPal Checkout
    """
    from db.models.package import UserPackage
    
    if user_package_id:
        # Package purchase
        user_package = db.query(UserPackage).filter(
            UserPackage.id == uuid.UUID(user_package_id),
            UserPackage.user_id == current_user.id
        ).first()
        
        if not user_package:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Package not found"
            )
        
        # Check if already paid
        if user_package.payment_id:
            existing_payment = db.query(Payment).filter(
                Payment.id == user_package.payment_id,
                Payment.status == PaymentStatus.COMPLETED
            ).first()
            
            if existing_payment:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Package already paid"
                )
        
        amount = float(user_package.package.price)
        currency = user_package.package.currency
        metadata = {
            "user_package_id": str(user_package.id),
            "user_id": str(current_user.id),
            "type": "package"
        }
        description = f"Package: {user_package.package.name} ({user_package.package.dataset_count} datasets)"
        
    elif dataset_request_id:
        # Legacy: Dataset payment (for backward compatibility)
        dataset = db.query(DatasetRequest).filter(
            DatasetRequest.id == uuid.UUID(dataset_request_id),
            DatasetRequest.user_id == current_user.id
        ).first()
        
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        # Check if already paid
        existing_payment = db.query(Payment).filter(
            Payment.dataset_request_id == dataset.id,
            Payment.status == PaymentStatus.COMPLETED
        ).first()
        
        if existing_payment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset already paid"
            )
        
        amount = 9.99  # Default dataset price (legacy)
        currency = "EUR"
        metadata = {
            "dataset_request_id": str(dataset.id),
            "user_id": str(current_user.id),
            "type": "dataset"
        }
        description = f"Dataset: {dataset.title}"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either user_package_id or dataset_request_id must be provided"
        )
    
        # Create Stripe Checkout session
    try:
        # For packages, we need to create a generic checkout session
        # For legacy datasets, use the old method
        if user_package_id:
            # Package checkout - create payment record first
            payment_provider = PaymentProvider.PAYPAL if provider.lower() == "paypal" else PaymentProvider.STRIPE
            
            payment = Payment(
                user_id=current_user.id,
                user_package_id=uuid.UUID(user_package_id),
                dataset_request_id=None,  # Packages don't have dataset_request_id
                amount=Decimal(str(amount)),
                currency=currency.lower(),
                status=PaymentStatus.PENDING,
                provider=payment_provider,
                idempotency_key=f"{user_package_id}-{uuid.uuid4()}",
                payment_metadata={
                    "type": "package",
                    "package_name": user_package.package.name,
                    "package_size": user_package.package.size.value
                }
            )
            db.add(payment)
            db.flush()  # Get payment.id
            
            # Package checkout - Stripe or PayPal
            if provider.lower() == "paypal":
                # PayPal checkout
                from services.paypal_service import create_paypal_order
                
                success_url = f"{settings.cors_origins_list[0] if settings.cors_origins_list else 'http://localhost:3000'}/payment/success?order_id={{ORDER_ID}}"
                cancel_url = f"{settings.cors_origins_list[0] if settings.cors_origins_list else 'http://localhost:3000'}/payment/cancel"
                
                paypal_order = create_paypal_order(
                    amount=amount,
                    currency=currency.upper(),
                    description=description,
                    return_url=success_url,
                    cancel_url=cancel_url,
                    metadata={
                        "user_package_id": str(user_package.id),
                        "user_id": str(current_user.id),
                        "type": "package",
                        "payment_id": str(payment.id)
                    }
                )
                
                # Update payment with PayPal order ID
                payment.provider_checkout_session_id = paypal_order["id"]
                payment.provider_ref = paypal_order["id"]
                db.commit()
                db.refresh(payment)
                
                return CheckoutResponse(
                    checkout_url=paypal_order["approval_url"],
                    session_id=paypal_order["id"]
                )
            else:
                # Stripe checkout (default)
                session = stripe.checkout.Session.create(
                    payment_method_types=['card', 'apple_pay', 'google_pay'],  # Enable Apple Pay and Google Pay
                    line_items=[{
                    'price_data': {
                        'currency': currency.lower(),
                        'product_data': {
                            'name': description,
                        },
                        'unit_amount': int(amount * 100),  # Convert to cents
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f"{settings.cors_origins_list[0] if settings.cors_origins_list else 'http://localhost:3000'}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.cors_origins_list[0] if settings.cors_origins_list else 'http://localhost:3000'}/payment/cancel",
                metadata=metadata,
            )
            
                # Update payment with checkout session ID
                payment.provider_checkout_session_id = session.id
                payment.provider = PaymentProvider.STRIPE
                db.commit()
                db.refresh(payment)
                
                logger.info(f"Created Stripe checkout session {session.id} for package")
                
                return CheckoutResponse(
                    checkout_url=session.url,
                    session_id=session.id
                )
        else:
            # Legacy dataset checkout
            if dataset.status != DatasetStatus.READY_FOR_PAYMENT:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Dataset not ready for payment. Current status: {dataset.status.value}"
                )
            
            # Legacy dataset checkout - Stripe or PayPal
            if provider.lower() == "paypal":
                # PayPal checkout for dataset
                success_url = f"{settings.cors_origins_list[0] if settings.cors_origins_list else 'http://localhost:3000'}/payment/success?order_id={{ORDER_ID}}"
                cancel_url = f"{settings.cors_origins_list[0] if settings.cors_origins_list else 'http://localhost:3000'}/payment/cancel"
                
                paypal_order = create_paypal_order(
                    amount=amount,
                    currency=currency.upper(),
                    description=description,
                    return_url=success_url,
                    cancel_url=cancel_url,
                    metadata={
                        "dataset_request_id": str(dataset.id),
                        "user_id": str(current_user.id),
                        "type": "dataset"
                    }
                )
                
                # Create payment record
                payment = Payment(
                    user_id=current_user.id,
                    dataset_request_id=dataset.id,
                    amount=Decimal(str(amount)),
                    currency=currency.lower(),
                    status=PaymentStatus.PENDING,
                    provider=PaymentProvider.PAYPAL,
                    provider_checkout_session_id=paypal_order["id"],
                    provider_ref=paypal_order["id"],
                    idempotency_key=f"{dataset.id}-{paypal_order['id']}",
                    payment_metadata={
                        "order_id": paypal_order["id"],
                        "dataset_title": dataset.title
                    }
                )
                db.add(payment)
                db.commit()
                db.refresh(payment)
                
                return CheckoutResponse(
                    checkout_url=paypal_order["approval_url"],
                    session_id=paypal_order["id"]
                )
            else:
                # Stripe checkout (default)
                session = create_checkout_session(
                    dataset_request_id=dataset_request_id,
                    user_id=str(current_user.id),
                    amount=float(amount),
                    currency=currency.lower()
                )
                
                # Create payment record for legacy dataset
                payment = Payment(
                    user_id=current_user.id,
                    dataset_request_id=dataset.id,
                    amount=Decimal(str(amount)),
                    currency=currency.lower(),
                    status=PaymentStatus.PENDING,
                    provider=PaymentProvider.STRIPE,
                    provider_checkout_session_id=session.id,
                    idempotency_key=f"{dataset.id}-{session.id}",
                    payment_metadata={
                        "checkout_session_id": session.id,
                        "dataset_title": dataset.title
                    }
                )
                db.add(payment)
                db.commit()
                db.refresh(payment)
                
                logger.info(f"Created Stripe checkout session {session.id} for dataset")
                
                return CheckoutResponse(
                    checkout_url=session.url,
                    session_id=session.id
                )
    
    except Exception as e:
        logger.error(f"Error creating checkout: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating checkout: {str(e)}"
        )


@router.post("/checkout/paypal/capture")
async def capture_paypal_checkout(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Capture PayPal order after user approval.
    
    This endpoint is called after user returns from PayPal approval page.
    """
    try:
        # Capture the order
        captured_order = capture_paypal_order(order_id)
        
        # Find payment by order ID
        payment = db.query(Payment).filter(
            Payment.provider_checkout_session_id == order_id,
            Payment.user_id == current_user.id
        ).first()
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        # Check if already processed
        if payment.status == PaymentStatus.COMPLETED:
            return {"status": "already_completed", "payment_id": str(payment.id)}
        
        # Update payment status
        if captured_order.get("status") == "COMPLETED":
            payment.status = PaymentStatus.COMPLETED
            payment.provider_ref = order_id
            
            # Get capture details
            purchase_units = captured_order.get("purchase_units", [])
            if purchase_units:
                captures = purchase_units[0].get("payments", {}).get("captures", [])
                if captures:
                    payment.provider_ref = captures[0].get("id", order_id)
            
            db.commit()
            
            # Handle package or dataset activation
            await handle_paypal_payment_completed(payment, captured_order, db)
            
            return {
                "status": "completed",
                "payment_id": str(payment.id),
                "order_id": order_id
            }
        else:
            payment.status = PaymentStatus.FAILED
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PayPal order not completed. Status: {captured_order.get('status')}"
            )
    
    except Exception as e:
        logger.error(f"Error capturing PayPal order: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error capturing PayPal order: {str(e)}"
        )


async def handle_paypal_payment_completed(payment: Payment, order_data: Dict[str, Any], db: Session):
    """Handle PayPal payment completion (similar to Stripe webhook)."""
    try:
        # Handle based on payment type
        if payment.user_package_id:
            # Package payment
            from db.models.package import UserPackage, PackageStatus
            
            user_package = db.query(UserPackage).filter(
                UserPackage.id == payment.user_package_id
            ).first()
            
            if user_package:
                user_package.payment_id = payment.id
                user_package.status = PackageStatus.ACTIVE
                user_package.activated_at = datetime.utcnow()
                db.commit()
                
                logger.info(f"Package {payment.user_package_id} activated after PayPal payment {payment.id}")
        
        elif payment.dataset_request_id:
            # Dataset payment
            update_dataset_status(db, payment.dataset_request_id, DatasetStatus.PAID)
            
            # Create invoice
            from services.invoice_service import create_invoice_from_payment
            try:
                create_invoice_from_payment(db, payment)
            except Exception as e:
                logger.error(f"Error creating invoice for PayPal payment: {e}", exc_info=True)
            
            # Update manifest with billing info
            try:
                from db.models.dataset import DatasetStep, StepType, StepStatus
                from services.storage_service import s3_client
                from services.manifest_update_service import update_bundle_manifest
                from core.config import settings
                
                export_step = db.query(DatasetStep).filter(
                    DatasetStep.dataset_request_id == payment.dataset_request_id,
                    DatasetStep.step_type == StepType.EXPORT,
                    DatasetStep.status == StepStatus.SUCCESS
                ).first()
                
                if export_step and export_step.output_data and export_step.output_data.get("bundle_path"):
                    bundle_path = export_step.output_data["bundle_path"]
                    
                    try:
                        response = s3_client.get_object(
                            Bucket=settings.s3_bucket,
                            Key=bundle_path
                        )
                        bundle_data = response['Body'].read()
                        
                        manifest_updates = {
                            "billing": {
                                "payment_provider": "paypal",
                                "payment_status": "paid",
                                "payment_reference": payment.provider_ref or payment.idempotency_key,
                                "amount": float(payment.amount),
                                "currency": payment.currency.upper()
                            }
                        }
                        
                        updated_bundle = update_bundle_manifest(bundle_data, manifest_updates)
                        
                        s3_client.put_object(
                            Bucket=settings.s3_bucket,
                            Key=bundle_path,
                            Body=updated_bundle,
                            ContentType="application/zip"
                        )
                        
                        logger.info(f"Updated manifest with PayPal billing info for dataset {payment.dataset_request_id}")
                    except Exception as e:
                        logger.warning(f"Could not update manifest with PayPal billing info: {e}")
            except Exception as e:
                logger.warning(f"Error updating manifest with PayPal billing: {e}")
    
    except Exception as e:
        logger.error(f"Error handling PayPal payment completion: {e}", exc_info=True)
        db.rollback()
        raise


@router.post("/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db)
):
    """Handle Stripe webhook events."""
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )
    
    # Get raw body
    payload = await request.body()
    
    try:
        # Verify webhook signature
        event = verify_webhook_signature(payload, stripe_signature)
        
        # Handle event
        event_type = event['type']
        event_data = event['data']['object']
        
        logger.info(f"Received Stripe webhook: {event_type}")
        
        if event_type == 'checkout.session.completed':
            await handle_checkout_completed(event_data, db)
        elif event_type == 'payment_intent.succeeded':
            await handle_payment_succeeded(event_data, db)
        elif event_type == 'payment_intent.payment_failed':
            await handle_payment_failed(event_data, db)
        else:
            logger.info(f"Unhandled event type: {event_type}")
        
        return {"status": "success"}
    
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing webhook"
        )


@router.post("/webhooks/paypal")
async def paypal_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle PayPal webhook events."""
    try:
        # Get raw body
        payload = await request.body()
        
        # Get PayPal headers
        headers = {
            "PAYPAL-AUTH-ALGO": request.headers.get("PAYPAL-AUTH-ALGO", ""),
            "PAYPAL-CERT-URL": request.headers.get("PAYPAL-CERT-URL", ""),
            "PAYPAL-TRANSMISSION-ID": request.headers.get("PAYPAL-TRANSMISSION-ID", ""),
            "PAYPAL-TRANSMISSION-SIG": request.headers.get("PAYPAL-TRANSMISSION-SIG", ""),
            "PAYPAL-TRANSMISSION-TIME": request.headers.get("PAYPAL-TRANSMISSION-TIME", "")
        }
        
        # Verify webhook signature
        event = verify_paypal_webhook(payload, headers)
        
        # Handle event
        event_type = event.get("event_type", "")
        resource = event.get("resource", {})
        
        logger.info(f"Received PayPal webhook: {event_type}")
        
        if event_type == "PAYMENT.CAPTURE.COMPLETED":
            await handle_paypal_capture_completed(resource, db)
        elif event_type == "PAYMENT.CAPTURE.DENIED":
            await handle_paypal_capture_denied(resource, db)
        elif event_type == "CHECKOUT.ORDER.COMPLETED":
            await handle_paypal_order_completed(resource, db)
        else:
            logger.info(f"Unhandled PayPal event type: {event_type}")
        
        return {"status": "success"}
    
    except ValueError as e:
        logger.error(f"Invalid PayPal webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    except Exception as e:
        logger.error(f"Error processing PayPal webhook: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing webhook"
        )


async def handle_paypal_capture_completed(capture_data: dict, db: Session):
    """Handle PayPal payment capture completed event."""
    try:
        order_id = capture_data.get("order_id", "")
        capture_id = capture_data.get("id", "")
        
        # Find payment by order ID
        payment = db.query(Payment).filter(
            Payment.provider_checkout_session_id == order_id,
            Payment.provider == PaymentProvider.PAYPAL
        ).first()
        
        if not payment:
            logger.warning(f"Payment not found for PayPal order {order_id}")
            return
        
        # Check idempotency
        if payment.status == PaymentStatus.COMPLETED:
            logger.info(f"Payment {payment.id} already processed (idempotency)")
            return
        
        # Update payment
        payment.provider_ref = capture_id
        payment.status = PaymentStatus.COMPLETED
        db.commit()
        
        # Handle payment completion
        from services.paypal_service import get_paypal_client
        client = get_paypal_client()
        order_data = client.get_order(order_id)
        
        await handle_paypal_payment_completed(payment, order_data, db)
        
        logger.info(f"PayPal payment {payment.id} completed for order {order_id}")
    
    except Exception as e:
        logger.error(f"Error handling PayPal capture completed: {e}", exc_info=True)
        db.rollback()
        raise


async def handle_paypal_capture_denied(capture_data: dict, db: Session):
    """Handle PayPal payment capture denied event."""
    try:
        order_id = capture_data.get("order_id", "")
        
        payment = db.query(Payment).filter(
            Payment.provider_checkout_session_id == order_id,
            Payment.provider == PaymentProvider.PAYPAL
        ).first()
        
        if payment and payment.status == PaymentStatus.PENDING:
            payment.status = PaymentStatus.FAILED
            db.commit()
            logger.warning(f"PayPal payment {payment.id} denied for order {order_id}")
    
    except Exception as e:
        logger.error(f"Error handling PayPal capture denied: {e}", exc_info=True)
        db.rollback()


async def handle_paypal_order_completed(order_data: dict, db: Session):
    """Handle PayPal order completed event."""
    try:
        order_id = order_data.get("id", "")
        
        payment = db.query(Payment).filter(
            Payment.provider_checkout_session_id == order_id,
            Payment.provider == PaymentProvider.PAYPAL
        ).first()
        
        if payment and payment.status == PaymentStatus.PENDING:
            # Order completed, but capture may still be pending
            # Wait for PAYMENT.CAPTURE.COMPLETED event
            logger.info(f"PayPal order {order_id} completed, waiting for capture")
    
    except Exception as e:
        logger.error(f"Error handling PayPal order completed: {e}", exc_info=True)


async def handle_checkout_completed(session_data: dict, db: Session):
    """Handle checkout.session.completed event."""
    try:
        session_id = session_data.get('id')
        metadata = session_data.get('metadata', {})
        dataset_request_id = metadata.get('dataset_request_id')
        user_package_id = metadata.get('user_package_id')
        payment_type = metadata.get('type', 'dataset')  # 'package' or 'dataset'
        payment_intent_id = session_data.get('payment_intent')
        
        # Find payment by checkout session ID
        payment = db.query(Payment).filter(
            Payment.provider_checkout_session_id == session_id
        ).first()
        
        if not payment:
            logger.warning(f"Payment not found for session {session_id}")
            return
        
        # Check idempotency
        if payment.status == PaymentStatus.COMPLETED:
            logger.info(f"Payment {payment.id} already processed (idempotency)")
            return
        
        # Update payment
        payment.provider_ref = payment_intent_id
        payment.status = PaymentStatus.COMPLETED
        db.commit()
        
        # Handle based on payment type
        if payment_type == 'package' and user_package_id:
            # Package payment
            from db.models.package import UserPackage, PackageStatus
            
            user_package = db.query(UserPackage).filter(
                UserPackage.id == uuid.UUID(user_package_id)
            ).first()
            
            if user_package:
                # Link payment to package
                user_package.payment_id = payment.id
                user_package.status = PackageStatus.ACTIVE
                user_package.activated_at = datetime.utcnow()
                db.commit()
                
                logger.info(f"Package {user_package_id} activated after payment {payment.id}")
            else:
                logger.warning(f"UserPackage {user_package_id} not found for payment {payment.id}")
            
            # Create invoice for package
            from services.invoice_service import create_invoice_from_payment
            try:
                create_invoice_from_payment(db, payment)
            except Exception as e:
                logger.error(f"Error creating invoice for package: {e}", exc_info=True)
                # Don't fail payment if invoice creation fails
        
        elif payment_type == 'dataset' and dataset_request_id:
            # Dataset payment (legacy)
            # Update dataset status
            update_dataset_status(db, payment.dataset_request_id, DatasetStatus.PAID)
            
            # Create invoice
            from services.invoice_service import create_invoice_from_payment
            try:
                create_invoice_from_payment(db, payment)
            except Exception as e:
                logger.error(f"Error creating invoice: {e}", exc_info=True)
                # Don't fail payment if invoice creation fails
            
            # Update manifest with billing information if dataset bundle exists
            try:
                from db.models.dataset import DatasetStep, StepType, StepStatus
                from services.storage_service import s3_client
                from services.manifest_update_service import update_bundle_manifest
                from core.config import settings
                
                # Find export step with bundle
                export_step = db.query(DatasetStep).filter(
                    DatasetStep.dataset_request_id == payment.dataset_request_id,
                    DatasetStep.step_type == StepType.EXPORT,
                    DatasetStep.status == StepStatus.SUCCESS
                ).first()
                
                if export_step and export_step.output_data and export_step.output_data.get("bundle_path"):
                    bundle_path = export_step.output_data["bundle_path"]
                    
                    # Download bundle
                    try:
                        response = s3_client.get_object(
                            Bucket=settings.s3_bucket,
                            Key=bundle_path
                        )
                        bundle_data = response['Body'].read()
                        
                        # Update manifest with billing info
                        manifest_updates = {
                            "billing": {
                                "payment_provider": "stripe",
                                "payment_status": "paid",
                                "payment_reference": payment.provider_ref or payment.idempotency_key,
                                "amount": float(payment.amount),
                                "currency": payment.currency.upper()
                            }
                        }
                        
                        # Update bundle
                        updated_bundle = update_bundle_manifest(bundle_data, manifest_updates)
                        
                        # Upload updated bundle
                        s3_client.put_object(
                            Bucket=settings.s3_bucket,
                            Key=bundle_path,
                            Body=updated_bundle,
                            ContentType="application/zip"
                        )
                        
                        logger.info(f"Updated manifest with billing info for dataset {payment.dataset_request_id}")
                    except Exception as e:
                        logger.warning(f"Could not update manifest with billing info: {e}")
            except Exception as e:
                logger.warning(f"Error updating manifest with billing: {e}")
                # Don't fail payment if manifest update fails
            
            logger.info(f"Payment {payment.id} completed for dataset {payment.dataset_request_id}")
        else:
            logger.warning(f"Unknown payment type or missing IDs: type={payment_type}, dataset_id={dataset_request_id}, package_id={user_package_id}")
    
    except Exception as e:
        logger.error(f"Error handling checkout completed: {e}", exc_info=True)
        db.rollback()
        raise


async def handle_payment_succeeded(payment_intent_data: dict, db: Session):
    """Handle payment_intent.succeeded event."""
    try:
        payment_intent_id = payment_intent_data.get('id')
        
        # Find payment by provider_ref
        payment = db.query(Payment).filter(
            Payment.provider_ref == payment_intent_id
        ).first()
        
        if payment and payment.status != PaymentStatus.COMPLETED:
            payment.status = PaymentStatus.COMPLETED
            db.commit()
            
            # Update dataset status only if it's a dataset payment
            if payment.dataset_request_id:
                update_dataset_status(db, payment.dataset_request_id, DatasetStatus.PAID)
            elif payment.user_package_id:
                # Package payment - already handled in handle_checkout_completed
                from db.models.package import UserPackage, PackageStatus
                user_package = db.query(UserPackage).filter(
                    UserPackage.id == payment.user_package_id
                ).first()
                if user_package and user_package.status != PackageStatus.ACTIVE:
                    user_package.payment_id = payment.id
                    user_package.status = PackageStatus.ACTIVE
                    user_package.activated_at = datetime.utcnow()
                    db.commit()
            
            logger.info(f"Payment {payment.id} succeeded")
    except Exception as e:
        logger.error(f"Error handling payment succeeded: {e}", exc_info=True)
        db.rollback()
        raise


async def handle_payment_failed(payment_intent_data: dict, db: Session):
    """Handle payment_intent.payment_failed event."""
    try:
        payment_intent_id = payment_intent_data.get('id')
        
        # Find payment
        payment = db.query(Payment).filter(
            Payment.provider_ref == payment_intent_id
        ).first()
        
        if payment and payment.status == PaymentStatus.PENDING:
            payment.status = PaymentStatus.FAILED
            db.commit()
            logger.warning(f"Payment {payment.id} failed")
    except Exception as e:
        logger.error(f"Error handling payment failed: {e}", exc_info=True)
        db.rollback()
        raise


@router.get("/payments", response_model=list[PaymentResponse])
async def list_payments(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List user's payments."""
    payments = db.query(Payment).filter(
        Payment.user_id == current_user.id
    ).order_by(Payment.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        PaymentResponse(
            id=str(p.id),
            user_id=str(p.user_id),
            dataset_request_id=str(p.dataset_request_id) if p.dataset_request_id else None,
            user_package_id=str(p.user_package_id) if p.user_package_id else None,
            amount=str(p.amount),
            currency=p.currency,
            status=p.status.value,
            provider=p.provider.value,
            provider_checkout_session_id=p.provider_checkout_session_id,
            created_at=p.created_at,
            updated_at=p.updated_at
        )
        for p in payments
    ]


@router.get("/invoices", response_model=InvoiceListResponse)
async def list_invoices(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List user's invoices."""
    invoices = db.query(Invoice).filter(
        Invoice.user_id == current_user.id
    ).order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()
    
    total = db.query(Invoice).filter(
        Invoice.user_id == current_user.id
    ).count()
    
    return InvoiceListResponse(
        invoices=[
            InvoiceResponse(
                id=str(inv.id),
                invoice_number=inv.invoice_number,
                user_id=str(inv.user_id),
                payment_id=str(inv.payment_id),
                dataset_request_id=str(inv.dataset_request_id),
                amount=str(inv.amount),
                tax_amount=str(inv.tax_amount) if inv.tax_amount else None,
                total_amount=str(inv.total_amount),
                currency=inv.currency,
                invoice_date=inv.invoice_date,
                due_date=inv.due_date,
                status=inv.status.value,
                storage_path=inv.storage_path,
                created_at=inv.created_at,
                updated_at=inv.updated_at
            )
            for inv in invoices
        ],
        total=total
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get invoice details."""
    invoice = db.query(Invoice).filter(
        Invoice.id == uuid.UUID(invoice_id),
        Invoice.user_id == current_user.id
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    return InvoiceResponse(
        id=str(invoice.id),
        invoice_number=invoice.invoice_number,
        user_id=str(invoice.user_id),
        payment_id=str(invoice.payment_id),
        dataset_request_id=str(invoice.dataset_request_id),
        amount=str(invoice.amount),
        tax_amount=str(invoice.tax_amount) if invoice.tax_amount else None,
        total_amount=str(invoice.total_amount),
        currency=invoice.currency,
        invoice_date=invoice.invoice_date,
        due_date=invoice.due_date,
        status=invoice.status.value,
        storage_path=invoice.storage_path,
        created_at=invoice.created_at,
        updated_at=invoice.updated_at
    )


@router.get("/invoices/{invoice_id}/download")
async def download_invoice(
    invoice_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Download invoice PDF."""
    invoice = db.query(Invoice).filter(
        Invoice.id == uuid.UUID(invoice_id),
        Invoice.user_id == current_user.id
    ).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    if not invoice.storage_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice PDF not found"
        )
    
    # Generate signed URL
    from services.storage_service import generate_signed_url
    from core.config import settings
    from db.models.audit_log import AuditLog, AuditAction
    
    try:
        signed_url = generate_signed_url(
            s3_key=invoice.storage_path,
            expiration=settings.signed_url_ttl
        )
        
        # Log audit
        trace_id = request.headers.get("X-Trace-Id") or str(uuid.uuid4())
        audit = AuditLog(
            user_id=current_user.id,
            action=AuditAction.INVOICE_DOWNLOAD,
            resource_type="invoice",
            resource_id=invoice.id,
            trace_id=trace_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            extra_metadata={
                "invoice_number": invoice.invoice_number,
                "payment_id": str(invoice.payment_id)
            }
        )
        db.add(audit)
        db.commit()
        
        return {
            "download_url": signed_url,
            "expires_in": settings.signed_url_ttl,
            "invoice_number": invoice.invoice_number,
            "trace_id": trace_id
        }
    
    except Exception as e:
        logger.error(f"Error generating invoice download URL: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating download URL"
        )


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get payment details."""
    payment = db.query(Payment).filter(
        Payment.id == uuid.UUID(payment_id),
        Payment.user_id == current_user.id
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    return PaymentResponse(
        id=str(payment.id),
        user_id=str(payment.user_id),
        dataset_request_id=str(payment.dataset_request_id) if payment.dataset_request_id else None,
        user_package_id=str(payment.user_package_id) if payment.user_package_id else None,
        amount=str(payment.amount),
        currency=payment.currency,
        status=payment.status.value,
        provider=payment.provider.value,
        provider_checkout_session_id=payment.provider_checkout_session_id,
        created_at=payment.created_at,
        updated_at=payment.updated_at
    )

