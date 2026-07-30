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
        
    def get_html_template(title: str, message: str, code: str, footer_text: str) -> str:
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                    background-color: #f4f4f5;
                    margin: 0;
                    padding: 0;
                    -webkit-font-smoothing: antialiased;
                }}
                .container {{
                    max-width: 600px;
                    margin: 40px auto;
                    background-color: #ffffff;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                    overflow: hidden;
                }}
                .header {{
                    background-color: #0f172a;
                    padding: 30px 40px;
                    text-align: center;
                }}
                .header h1 {{
                    color: #ffffff;
                    margin: 0;
                    font-size: 24px;
                    font-weight: 600;
                    letter-spacing: -0.5px;
                }}
                .content {{
                    padding: 40px;
                    text-align: center;
                }}
                .message {{
                    color: #334155;
                    font-size: 16px;
                    line-height: 1.6;
                    margin-bottom: 30px;
                }}
                .otp-box {{
                    background-color: #f8fafc;
                    border: 2px dashed #cbd5e1;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 0 auto 30px auto;
                    max-width: 300px;
                }}
                .otp-code {{
                    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                    font-size: 32px;
                    font-weight: 700;
                    color: #2563eb;
                    letter-spacing: 8px;
                    margin: 0;
                }}
                .footer {{
                    background-color: #f8fafc;
                    padding: 20px 40px;
                    text-align: center;
                    border-top: 1px solid #e2e8f0;
                }}
                .footer p {{
                    color: #64748b;
                    font-size: 13px;
                    margin: 0;
                    line-height: 1.5;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Hushh Tunnel</h1>
                </div>
                <div class="content">
                    <p class="message">{message}</p>
                    <div class="otp-box">
                        <p class="otp-code">{code}</p>
                    </div>
                    <p class="message" style="font-size: 14px; color: #64748b; margin-bottom: 0;">
                        This code will expire in 10 minutes.
                    </p>
                </div>
                <div class="footer">
                    <p>{footer_text}</p>
                </div>
            </div>
        </body>
        </html>
        """

    if purpose == "register":
        subject = "Hushh Tunnel - Verification Code"
        html_content = get_html_template(
            title="Verify your email",
            message="Welcome to Hushh Tunnel! Please use the verification code below to complete your registration.",
            code=otp_code,
            footer_text="If you didn't attempt to register for an account, you can safely ignore this email."
        )
    elif purpose == "reset_password":
        subject = "Hushh Tunnel - Password Reset Code"
        html_content = get_html_template(
            title="Reset your password",
            message="We received a request to reset your password. Use the verification code below to set up a new password.",
            code=otp_code,
            footer_text="If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged."
        )
    else:
        subject = "Hushh Tunnel - Verification Code"
        html_content = get_html_template(
            title="Verification Code",
            message="Please use the verification code below to proceed.",
            code=otp_code,
            footer_text="If you didn't request this code, you can safely ignore this email."
        )

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
