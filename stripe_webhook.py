from flask import Blueprint, request, jsonify, render_template
import stripe
from datetime import datetime, timedelta
import os
import logging
from models import db, Customer, Subscription, PaymentLog
from app.services.search_manager import SearchManager

# Set up logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'stripe_webhook.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

stripe_bp = Blueprint('stripe_webhook', __name__)

# Domain configuration
DOMAIN = os.getenv('DOMAIN', 'audiosnipt.com')
WEBHOOK_URL = f"https://{DOMAIN}/webhook"
SUCCESS_URL = f"https://{DOMAIN}/success"
CANCEL_URL = f"https://{DOMAIN}/cancel"

# Stripe configuration (Live Mode)
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

# Product IDs (Live Mode)
PRODUCT_PLANS = {
    'youtube_search_day_pass': {
        'id': os.getenv('STRIPE_DAY_PASS_ID'),
        'duration': timedelta(days=1),
        'searches': 50
    },
    'youtube_search_week_pass': {
        'id': os.getenv('STRIPE_WEEK_PASS_ID'),
        'duration': timedelta(days=7),
        'searches': 200
    },
    'youtube_search_month_pass': {
        'id': os.getenv('STRIPE_MONTH_PASS_ID'),
        'duration': timedelta(days=30),
        'searches': 500
    }
}

@stripe_bp.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhook events."""
    logger.info("Received webhook request")
    logger.info(f"Headers: {dict(request.headers)}")
    
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    logger.info(f"Signature header: {sig_header}")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=webhook_secret
        )
        logger.info(f"Successfully constructed event: {event['type']}")
    except ValueError as e:
        logger.error(f"Invalid payload: {str(e)}")
        logger.error(f"Payload received: {payload.decode()}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {str(e)}")
        logger.error(f"Webhook secret used: {webhook_secret[:5]}...")
        return jsonify({'error': 'Invalid signature'}), 400

    try:
        # Log the webhook event
        logger.info(f"Received webhook event: {event['type']}")
        logger.info(f"Event data: {event['data']}")
        
        # Log the payment event
        payment_log = PaymentLog(
            stripe_event_id=event['id'],
            event_type=event['type'],
            status='processing'
        )
        db.session.add(payment_log)
        db.session.commit()

        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            # Log the successful payment
            logger.info(f"Payment successful for session {session['id']}")
            
            # Get the product details
            line_items = stripe.checkout.Session.list_line_items(session['id'])
            price_id = line_items['data'][0]['price']['id']
            product_id = line_items['data'][0]['price']['product']
            
            # Find matching plan
            plan_type = None
            plan_details = None
            for plan_name, plan in PRODUCT_PLANS.items():
                if plan['id'] == product_id:
                    plan_type = plan_name
                    plan_details = plan
                    break
            
            if not plan_details:
                logger.error(f"Unknown product ID: {product_id}")
                payment_log.status = 'failed'
                payment_log.error_message = f"Unknown product ID: {product_id}"
                db.session.commit()
                return jsonify({'error': 'Invalid product'}), 400
            
            # Check if this is a recurring subscription
            price = stripe.Price.retrieve(price_id)
            is_recurring = price.get('recurring') is not None
            
            expiry_date = datetime.now() + plan_details['duration']
            search_limit = plan_details['searches']
            
            # Get or create customer
            customer_id = session.get('customer')
            customer_email = session.get('customer_details', {}).get('email')
            
            customer = Customer.query.filter_by(
                stripe_customer_id=customer_id
            ).first() if customer_id else None
            
            if not customer and customer_id:
                customer = Customer(
                    stripe_customer_id=customer_id,
                    email=customer_email
                )
                db.session.add(customer)
                db.session.commit()
            
            # Create subscription record
            subscription = Subscription(
                customer_id=customer.id if customer else None,
                stripe_subscription_id=session.get('subscription'),
                plan_type=plan_type,
                status='active',
                search_limit=search_limit,
                start_date=datetime.now(),
                expiry_date=expiry_date,
                is_recurring=is_recurring
            )
            db.session.add(subscription)
            
            # Update payment log
            payment_log.customer_id = customer.id if customer else None
            payment_log.status = 'success'
            payment_log.amount = session.get('amount_total')
            
            db.session.commit()
            
            # Generate access token
            search_mgr = SearchManager()
            token = search_mgr.create_subscription_token(plan_type)
            
            logger.info(
                f"Generated token for plan {plan_type} "
                f"({'recurring' if is_recurring else 'one-time'})"
            )
            
            # Return success response
            return jsonify({
                'status': 'success',
                'token': token,
                'redirect_url': f'{SUCCESS_URL}?token={token}'
            })
        
        elif event['type'] == 'payment_intent.payment_failed':
            # Log failed payment
            intent = event['data']['object']
            error_message = intent.get('last_payment_error', {}).get(
                'message', 'Unknown error'
            )
            logger.error(f"Payment failed: {error_message}")
            
            # Update payment log
            payment_log.status = 'failed'
            payment_log.error_message = error_message
            db.session.commit()
            
            return jsonify({
                'status': 'failed',
                'error': error_message,
                'redirect_url': CANCEL_URL
            })
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        
        # Update payment log
        if 'payment_log' in locals():
            payment_log.status = 'error'
            payment_log.error_message = str(e)
            db.session.commit()
        
        return jsonify({'error': 'Internal server error'}), 500
    
    return jsonify({'status': 'success'})

@stripe_bp.route('/success')
def success():
    """Handle successful payments."""
    token = request.args.get('token')
    if token:
        return render_template('success.html', token=token)
    return render_template('success.html')

@stripe_bp.route('/cancel')
def cancel():
    """Handle cancelled payments."""
    return render_template('cancel.html') 