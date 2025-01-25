import os
import logging
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from models import Customer, Subscription

logger = logging.getLogger(__name__)


def send_email(to_email, subject, html_content):
    """Send an email using SMTP"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = os.getenv('SMTP_FROM_EMAIL')
        msg['To'] = to_email
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        with smtplib.SMTP_SSL(
            os.getenv('SMTP_HOST'),
            int(os.getenv('SMTP_PORT', 465))
        ) as server:
            server.login(
                os.getenv('SMTP_USERNAME'),
                os.getenv('SMTP_PASSWORD')
            )
            server.send_message(msg)
        
        return True, None
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False, str(e)


def notify_subscription_created(subscription_id):
    """Send welcome email for new subscription"""
    subscription = Subscription.query.get(subscription_id)
    if not subscription or not subscription.customer:
        return False, "Invalid subscription or customer"
    
    customer = subscription.customer
    if not customer.email:
        return False, "No customer email"
    
    subject = "Welcome to YouTube Search & Clip!"
    html_content = f"""
    <h2>Welcome to YouTube Search & Clip!</h2>
    <p>Your {subscription.plan_type} subscription is now active.</p>
    <ul>
        <li>Search Limit: {subscription.search_limit}</li>
        <li>Expiry Date: {subscription.expiry_date.strftime('%Y-%m-%d')}</li>
        <li>Recurring: {'Yes' if subscription.is_recurring else 'No'}</li>
    </ul>
    <p>Start searching now at <a href="https://{os.getenv('DOMAIN')}">
    {os.getenv('DOMAIN')}</a></p>
    """
    
    return send_email(customer.email, subject, html_content)


def notify_subscription_expiring(subscription_id):
    """Send expiration warning email"""
    subscription = Subscription.query.get(subscription_id)
    if not subscription or not subscription.customer:
        return False, "Invalid subscription or customer"
    
    customer = subscription.customer
    if not customer.email:
        return False, "No customer email"
    
    subject = "Your Subscription is Expiring Soon"
    html_content = f"""
    <h2>Subscription Expiring Soon</h2>
    <p>Your {subscription.plan_type} subscription will expire on 
    {subscription.expiry_date.strftime('%Y-%m-%d')}.</p>
    <p>Searches remaining: {subscription.search_limit - subscription.searches_used}</p>
    """
    
    if subscription.is_recurring:
        html_content += "<p>Your subscription will automatically renew.</p>"
    else:
        html_content += """
        <p>To continue using our service, please renew your subscription at 
        <a href="https://{os.getenv('DOMAIN')}/pricing">our pricing page</a>.</p>
        """
    
    return send_email(customer.email, subject, html_content)


def notify_payment_failed(customer_id, error_message):
    """Send payment failure notification"""
    customer = Customer.query.get(customer_id)
    if not customer or not customer.email:
        return False, "Invalid customer or no email"
    
    subject = "Payment Failed"
    html_content = f"""
    <h2>Payment Failed</h2>
    <p>We were unable to process your payment.</p>
    <p>Error: {error_message}</p>
    <p>Please update your payment information at 
    <a href="https://{os.getenv('DOMAIN')}/billing">your billing page</a>.</p>
    """
    
    return send_email(customer.email, subject, html_content) 