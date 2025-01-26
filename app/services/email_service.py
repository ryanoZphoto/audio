"""Email service module."""
import os
import logging
from flask import current_app, render_template
from flask_mail import Message, Mail

logger = logging.getLogger(__name__)
mail = Mail()


def send_email(to_email, subject, template, context=None):
    """Send an email using Flask-Mail.
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        template (str): Template name
        context (dict): Template context variables
    """
    if current_app.config.get('TESTING'):
        logger.info(f"Test mode - not sending email to {to_email}")
        return
        
    try:
        msg = Message(
            subject=subject,
            recipients=[to_email],
            sender=current_app.config.get('MAIL_DEFAULT_SENDER')
        )
        
        # Render template with context
        msg.html = render_template(template, **context or {})
        
        mail.send(msg)
        logger.info(f"Email sent to {to_email}: {subject}")
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        raise 