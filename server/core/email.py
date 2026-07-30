"""
Email service using SendGrid.
"""
import structlog
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from server.config import get_settings

logger = structlog.get_logger(__name__)

def send_otp_email(to_email: str, otp_code: str, purpose: str) -> None:
    """Send an OTP email using SendGrid."""
    settings = get_settings()
    
    if not settings.sendgrid_api_key or not settings.sendgrid_from_email:
        logger.warning("email.sendgrid_not_configured", to_email=to_email, otp_code=otp_code)
        return
        
    if purpose == "register":
        subject = "Hushh Tunnel - Verification Code"
        html_content = f"""
        <h2>Welcome to Hushh Tunnel</h2>
        <p>Your verification code is: <strong>{otp_code}</strong></p>
        <p>This code will expire in 10 minutes.</p>
        """
    elif purpose == "reset_password":
        subject = "Hushh Tunnel - Password Reset Code"
        html_content = f"""
        <h2>Password Reset</h2>
        <p>Your password reset code is: <strong>{otp_code}</strong></p>
        <p>This code will expire in 10 minutes. If you did not request a password reset, you can safely ignore this email.</p>
        """
    else:
        subject = "Hushh Tunnel - Verification Code"
        html_content = f"<p>Your code is: <strong>{otp_code}</strong></p>"

    message = Mail(
        from_email=settings.sendgrid_from_email,
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )
    
    try:
        sg = SendGridAPIClient(settings.sendgrid_api_key)
        response = sg.send(message)
        logger.info("email.sent", to_email=to_email, status_code=response.status_code)
    except Exception as e:
        logger.error("email.send_failed", to_email=to_email, error=str(e))
        raise
