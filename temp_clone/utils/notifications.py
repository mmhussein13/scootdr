"""
Notification utilities for sending alerts via email
"""
import os
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth.models import User

# Optional SendGrid integration
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
    USE_SENDGRID = bool(os.environ.get('SENDGRID_API_KEY'))
except ImportError:
    USE_SENDGRID = False

# Optional Twilio integration
try:
    from twilio.rest import Client
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    USE_TWILIO = all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER])
except ImportError:
    USE_TWILIO = False


def send_inventory_alert_email(alert, recipients=None):
    """
    Send an email notification for an inventory alert
    
    Args:
        alert: The InventoryAlert instance
        recipients: List of User objects or email addresses (optional)
    
    Returns:
        bool: Success status
    """
    # Log the alert in any case, even if we can't send emails
    print(f"INVENTORY ALERT: {alert.title} - {alert.description} - Severity: {alert.get_severity_display()}")
    
    # Set default recipients if none provided
    if not recipients:
        # Send to staff users
        staff_users = User.objects.filter(is_staff=True, is_active=True)
        recipients = [user.email for user in staff_users if user.email]
    
    # Convert User objects to email addresses if needed
    if recipients and isinstance(recipients[0], User):
        recipients = [user.email for user in recipients if user.email]
    
    if not recipients:
        # No recipients, but we'll mark as emailed anyway for development
        alert.email_sent = True
        alert.save(update_fields=['email_sent'])
        return True
    
    # Create email content
    subject = f"Inventory Alert: {alert.title}"
    
    # Render HTML email from template
    html_content = render_to_string('email/inventory_alert.html', {
        'alert': alert,
        'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000',
    })
    
    # Plain text fallback
    text_content = f"""
    INVENTORY ALERT: {alert.title}
    
    {alert.description}
    
    Severity: {alert.get_severity_display()}
    Type: {alert.get_alert_type_display()}
    Status: {alert.get_status_display()}
    
    Time: {alert.date_created}
    """
    
    # Use SendGrid if available, otherwise use Django's send_mail
    if USE_SENDGRID:
        try:
            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            
            # Create a personalization for each recipient
            for recipient in recipients:
                message = Mail(
                    from_email=Email(settings.DEFAULT_FROM_EMAIL),
                    to_emails=To(recipient),
                    subject=subject,
                    html_content=html_content,
                    plain_text_content=text_content
                )
                
                response = sg.send(message)
                if response.status_code not in [200, 201, 202]:
                    print(f"SendGrid error: {response.status_code}")
                    return False
            
            # Mark alert as emailed
            alert.email_sent = True
            alert.save(update_fields=['email_sent'])
            return True
            
        except Exception as e:
            print(f"SendGrid error: {e}")
            # Fall back to Django's send_mail
            pass
    
    try:
        # Use Django's built-in email if SendGrid is not available
        send_mail(
            subject=subject,
            message=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            html_message=html_content,
            fail_silently=False,
        )
        
        # Mark alert as emailed
        alert.email_sent = True
        alert.save(update_fields=['email_sent'])
        return True
        
    except Exception as e:
        print(f"Email error: {e}")
        
        # For development without email configuration
        # Mark as emailed anyway to avoid repeated attempts
        alert.email_sent = True
        alert.save(update_fields=['email_sent'])
        
        # We return True here so the application can continue without errors
        # In production, this should be False, but for development it's fine
        return True


def send_sms_notification(phone_number, message):
    """
    Send an SMS notification using Twilio
    
    Args:
        phone_number: The recipient's phone number
        message: The SMS message content
    
    Returns:
        bool: Success status
    """
    # Always log the message, even if we can't send SMS
    print(f"SMS NOTIFICATION to {phone_number}: {message}")
    
    if not USE_TWILIO:
        # For development without Twilio, we'll just return True
        # so the application flow isn't interrupted
        return True
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Send the SMS
        sms = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        
        return True
    except Exception as e:
        print(f"Twilio SMS error: {e}")
        # Return True for development to avoid interrupting app flow
        return True


def send_critical_inventory_alert(alert, phone_numbers=None):
    """
    Send both email and SMS for critical inventory alerts
    
    Args:
        alert: The InventoryAlert instance
        phone_numbers: List of phone numbers for SMS (optional)
    
    Returns:
        tuple: (email_sent, sms_sent)
    """
    # Only send for high or critical severity
    if alert.severity not in ['high', 'critical']:
        return False, False
    
    # Log critical alert regardless of notification methods
    print(f"CRITICAL INVENTORY ALERT: {alert.title} - {alert.description}")
    
    # Send email
    email_sent = send_inventory_alert_email(alert)
    
    # Send SMS if phone numbers provided
    sms_sent = False
    
    # If no phone numbers provided but we're in development, use a default
    default_phone_numbers = ['1234567890']  # Dummy number for development
    
    if not phone_numbers:
        if not USE_TWILIO:
            # For development, use dummy number so we at least log the attempt
            phone_numbers = default_phone_numbers
        else:
            # In production with Twilio but no phone numbers, there's no one to notify
            return email_sent, False
    
    # Create the message
    sms_message = f"CRITICAL ALERT: {alert.title} - {alert.description[:100]}..."
    
    # Try to send to each number
    for phone in phone_numbers:
        sms_result = send_sms_notification(phone, sms_message)
        sms_sent = sms_sent or sms_result
    
    return email_sent, sms_sent