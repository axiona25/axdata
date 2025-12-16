"""Email service using SendGrid SMTP."""
import smtplib
import logging
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import Optional
from core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Email service for sending emails via SendGrid SMTP."""
    
    def __init__(self):
        self.smtp_host = getattr(settings, 'email_smtp_host', 'smtp.sendgrid.net')
        self.smtp_port = getattr(settings, 'email_smtp_port', 587)
        self.smtp_user = getattr(settings, 'email_smtp_user', 'apikey')
        self.smtp_password = getattr(settings, 'email_smtp_password', None)
        self.from_email = getattr(settings, 'email_from', 'no-reply@axdata.eu')
        self.use_tls = getattr(settings, 'email_use_tls', True)
        self.enabled = getattr(settings, 'email_enabled', True) and self.smtp_password is not None
        
        # Log configuration status
        if not self.enabled:
            if not getattr(settings, 'email_enabled', True):
                logger.warning("⚠️ Email service is disabled in settings (email_enabled=False)")
            elif not self.smtp_password:
                logger.warning("⚠️ Email service disabled: SendGrid API key not configured. Add it to API_KEYS.md or set EMAIL_SMTP_PASSWORD env var")
            else:
                logger.warning("⚠️ Email service disabled for unknown reason")
        else:
            logger.info(f"✅ Email service enabled. SMTP: {self.smtp_host}:{self.smtp_port}, From: {self.from_email}")
    
    def _get_logo_data(self) -> tuple[Optional[bytes], Optional[str]]:
        """Get logo from database and return as (bytes, content_type)."""
        try:
            from db.session import SessionLocal
            from sqlalchemy import text
            
            db = SessionLocal()
            try:
                # Use raw SQL to avoid SQLAlchemy model initialization issues
                result = db.execute(
                    text("SELECT content_type, data FROM app_assets WHERE key = :key"),
                    {"key": "logo"}
                ).fetchone()
                
                if result and result.data:
                    content_type = result.content_type or "image/png"
                    logger.info(f"✅ Logo loaded from database: {len(result.data)} bytes, type: {content_type}")
                    return (result.data, content_type)
                else:
                    logger.warning("⚠️ Logo not found in database or data is empty")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"❌ Could not load logo from database: {e}", exc_info=True)
        return (None, None)
    
    def _get_logo_base64(self) -> Optional[str]:
        """Get logo from database and return as base64 data URI (fallback for compatibility)."""
        logo_data, content_type = self._get_logo_data()
        if logo_data and content_type:
            logo_base64 = base64.b64encode(logo_data).decode('utf-8')
            return f"data:{content_type};base64,{logo_base64}"
        return None
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        logo_data: Optional[bytes] = None,
        logo_content_type: Optional[str] = None
    ) -> bool:
        """
        Send an email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body (optional)
            logo_data: Logo image data as bytes (optional, for inline attachment)
            logo_content_type: Logo content type (optional, e.g., 'image/png')
        
        Returns:
            True if email was sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning(f"Email service disabled. Would send to {to_email}: {subject}")
            return False
        
        if not self.smtp_password:
            logger.error("Email SMTP password not configured. Cannot send email.")
            return False
        
        try:
            # Create message as 'related' to support inline images
            msg = MIMEMultipart('related')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Create alternative part for text and HTML
            msg_alternative = MIMEMultipart('alternative')
            msg.attach(msg_alternative)
            
            # Add text part
            if text_body:
                text_part = MIMEText(text_body, 'plain', 'utf-8')
                msg_alternative.attach(text_part)
            
            # Add HTML part
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg_alternative.attach(html_part)
            
            # Attach logo as inline image if provided
            if logo_data and logo_content_type:
                # Convert memoryview to bytes if necessary (PostgreSQL returns memoryview)
                if isinstance(logo_data, memoryview):
                    logo_data = bytes(logo_data)
                elif not isinstance(logo_data, bytes):
                    logo_data = bytes(logo_data)
                
                logo_image = MIMEImage(logo_data, _subtype=logo_content_type.split('/')[-1] if '/' in logo_content_type else 'png')
                logo_image.add_header('Content-ID', '<logo>')
                logo_image.add_header('Content-Disposition', 'inline', filename='logo.png')
                msg.attach(logo_image)
                logger.info("✅ Logo attached as inline image")
            
            # Send email via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}: {subject}")
            return True
        
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}", exc_info=True)
            return False
    
    def send_verification_email(self, to_email: str, verification_url: str) -> bool:
        """Send email verification email."""
        subject = "Conferma il tuo account AXDATA"
        
        # Get logo data for inline attachment
        logo_bytes, logo_content_type = self._get_logo_data()
        if logo_bytes and logo_content_type:
            # Use Content-ID for inline image (better email client support)
            logo_html = '<img src="cid:logo" alt="AXDATA" style="max-width: 200px; height: auto; display: block; margin: 0 auto;" />'
            logger.info("✅ Using logo as inline attachment (cid:logo)")
        else:
            # Fallback to base64 if logo not available
            logo_base64 = self._get_logo_base64()
            if logo_base64:
                logo_html = f'<img src="{logo_base64}" alt="AXDATA" style="max-width: 200px; height: auto; display: block; margin: 0 auto;" />'
                logger.info("✅ Using logo as base64 data URI")
            else:
                logo_html = '<h1 style="margin: 0; color: white; font-size: 24px;">AXDATA</h1>'
                logger.warning("⚠️ Logo not available, using text fallback")
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #2B3644;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 8px 8px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 8px 8px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #3B82F6;
                    color: #FFFFFF !important;
                    text-decoration: none;
                    border-radius: 8px;
                    margin: 20px 0;
                    font-weight: bold;
                }}
                .footer {{
                    margin-top: 20px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    {logo_html}
                </div>
                <div class="content">
                    <h2>Conferma il tuo account</h2>
                    <p>Ciao,</p>
                    <p>Grazie per esserti registrato su AXDATA. Per completare la registrazione, clicca sul pulsante qui sotto per verificare il tuo indirizzo email:</p>
                    <p style="text-align: center;">
                        <a href="{verification_url}" class="button" style="color: #FFFFFF !important;">Verifica Email</a>
                    </p>
                    <p>Oppure copia e incolla questo link nel tuo browser:</p>
                    <p style="word-break: break-all; color: #3B82F6;">{verification_url}</p>
                    <p>Questo link scadrà tra 24 ore.</p>
                    <p>Se non hai richiesto questa registrazione, puoi ignorare questa email.</p>
                    <div class="footer">
                        <p>Powered by AXDATA Srl</p>
                        <p>Se hai domande, contattaci a support@axdata.eu</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Conferma il tuo account AXDATA
        
        Ciao,
        
        Grazie per esserti registrato su AXDATA. Per completare la registrazione, clicca sul link qui sotto per verificare il tuo indirizzo email:
        
        {verification_url}
        
        Questo link scadrà tra 24 ore.
        
        Se non hai richiesto questa registrazione, puoi ignorare questa email.
        
        Powered by AXDATA Srl
        """
        
        return self.send_email(to_email, subject, html_body, text_body, logo_bytes, logo_content_type)
    
    def send_password_reset_email(self, to_email: str, reset_url: str) -> bool:
        """Send password reset email."""
        subject = "Reimposta la tua password AXDATA"
        
        # Get logo data for inline attachment
        logo_bytes, logo_content_type = self._get_logo_data()
        if logo_bytes and logo_content_type:
            # Use Content-ID for inline image (better email client support)
            logo_html = '<img src="cid:logo" alt="AXDATA" style="max-width: 200px; height: auto; display: block; margin: 0 auto;" />'
            logger.info("✅ Using logo as inline attachment (cid:logo)")
        else:
            # Fallback to base64 if logo not available
            logo_base64 = self._get_logo_base64()
            if logo_base64:
                logo_html = f'<img src="{logo_base64}" alt="AXDATA" style="max-width: 200px; height: auto; display: block; margin: 0 auto;" />'
                logger.info("✅ Using logo as base64 data URI")
            else:
                logo_html = '<h1 style="margin: 0; color: white; font-size: 24px;">AXDATA</h1>'
                logger.warning("⚠️ Logo not available, using text fallback")
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #2B3644;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 8px 8px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 8px 8px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #F59E0B;
                    color: #FFFFFF !important;
                    text-decoration: none;
                    border-radius: 8px;
                    margin: 20px 0;
                    font-weight: bold;
                }}
                .footer {{
                    margin-top: 20px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border-left: 4px solid #F59E0B;
                    padding: 15px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    {logo_html}
                </div>
                <div class="content">
                    <h2>Reimposta la tua password</h2>
                    <p>Ciao,</p>
                    <p>Abbiamo ricevuto una richiesta per reimpostare la password del tuo account AXDATA.</p>
                    <p style="text-align: center;">
                        <a href="{reset_url}" class="button" style="color: #FFFFFF !important;">Reimposta Password</a>
                    </p>
                    <p>Oppure copia e incolla questo link nel tuo browser:</p>
                    <p style="word-break: break-all; color: #F59E0B;">{reset_url}</p>
                    <div class="warning">
                        <strong>⚠️ Attenzione:</strong> Questo link scadrà tra 1 ora. Se non hai richiesto il reset della password, ignora questa email e la tua password rimarrà invariata.
                    </div>
                    <div class="footer">
                        <p>Powered by AXDATA Srl</p>
                        <p>Se hai domande, contattaci a support@axdata.eu</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        Reimposta la tua password AXDATA
        
        Ciao,
        
        Abbiamo ricevuto una richiesta per reimpostare la password del tuo account AXDATA.
        
        Clicca sul link qui sotto per reimpostare la password:
        
        {reset_url}
        
        ⚠️ Attenzione: Questo link scadrà tra 1 ora. Se non hai richiesto il reset della password, ignora questa email e la tua password rimarrà invariata.
        
        Powered by AXDATA Srl
        """
        
        return self.send_email(to_email, subject, html_body, text_body, logo_bytes, logo_content_type)


# Global email service instance
email_service = EmailService()
