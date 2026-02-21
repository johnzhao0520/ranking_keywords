"""
Payment Integration - Stripe

This module handles payment processing via Stripe
"""
import stripe
from typing import Optional
from app.core.config import settings

# Initialize Stripe (configure in settings)
stripe.api_key = settings.STRIPE_API_KEY if hasattr(settings, 'STRIPE_API_KEY') else None


class PaymentService:
    def __init__(self, api_key: str):
        stripe.api_key = api_key
    
    def create_checkout_session(
        self,
        plan_id: int,
        plan_name: str,
        price: int,  # in cents
        credits: int,
        user_email: str,
        success_url: str,
        cancel_url: str
    ) -> dict:
        """Create a Stripe checkout session"""
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'cny',
                    'product_data': {
                        'name': f'{plan_name} - {credits} Credits',
                        'description': f'KeywordTracker Pro - {plan_name} Plan'
                    },
                    'unit_amount': price,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=user_email,
            metadata={
                'plan_id': str(plan_id),
                'credits': str(credits)
            }
        )
        
        return {
            'session_id': session.id,
            'url': session.url
        }
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> dict:
        """Verify Stripe webhook signature"""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError:
            return None
    
    def create_portal_session(self, customer_id: str, return_url: str) -> dict:
        """Create customer portal session for subscription management"""
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url
        )
        return {'url': session.url}


def create_payment_link(plan_name: str, price: int, credits: int) -> str:
    """Create a simple payment link (no code required)"""
    
    product = stripe.Product.create(name=f"{plan_name} - {credits} Credits")
    
    price_obj = stripe.Price.create(
        unit_amount=price,
        currency='cny',
        product=product.id,
        metadata={
            'credits': str(credits),
            'plan': plan_name
        }
    )
    
    link = stripe.payment_link.create(
        line_items=[{'price': price_obj.id, 'quantity': 1}],
        after_completion={'type': 'redirect', 'redirect': {'url': 'https://yourdomain.com/success'}}
    )
    
    return link.url


# Webhook handler
async def handle_stripe_webhook(payload: bytes, signature: str) -> dict:
    """Handle Stripe webhook events"""
    
    event = stripe.Webhook.construct_event(
        payload, signature, settings.STRIPE_WEBHOOK_SECRET
    )
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # Add credits to user account
        # This would call the user service to add credits
        pass
    
    return {'status': 'success'}


# Usage in API:
"""
from app.services.payment import PaymentService

@router.post("/create-checkout-session")
def create_checkout(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get plan from database
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    
    payment = PaymentService(settings.STRIPE_API_KEY)
    session = payment.create_checkout_session(
        plan_id=plan.id,
        plan_name=plan.name,
        price=int(plan.price * 100),  # Convert to cents
        credits=plan.credits,
        user_email=current_user.email,
        success_url="https://yourdomain.com/payment/success",
        cancel_url="https://yourdomain.com/payment/cancel"
    )
    
    return session
"""
