"""Payment routes."""
import os
import stripe
import logging
from flask import Blueprint, request, jsonify
from app.extensions import db

logger = logging.getLogger(__name__)

payment_bp = Blueprint('payment', __name__)


@payment_bp.route('/process', methods=['POST'])
def process_payment():
    """Process a payment"""
    try:
        data = request.get_json()
        logger.info(f"Processing payment request: {data}")
        # Your payment processing code...
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"Payment processing error: {str(e)}")
        return jsonify({'error': str(e)}), 400


@payment_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    logger.info("Received Stripe webhook")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {str(e)}")
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid webhook signature: {str(e)}")
        return "Invalid signature", 400

    # Handle successful payment
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_successful_payment(session)
    
    return jsonify(status='success'), 200


def handle_successful_payment(session):
    """Handle successful payment completion"""
    try:
        # Get customer details from session
        customer_id = session.get('customer')
        subscription_id = session.get('subscription')
        
        if customer_id and subscription_id:
            # Update database with subscription info
            with db.session.begin():
                # Your subscription handling code...
                pass
                
        return True
    except Exception as e:
        logger.error(f"Error handling payment: {str(e)}")
        return False
