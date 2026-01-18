"""
Email client for KonseptiKeiju.

Handles sending delivery emails with attachments.
"""

import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

import httpx
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)


class EmailClient:
    """
    Client for sending emails via SMTP.
    """

    def __init__(self):
        self.host = (settings.smtp_host or "").strip()
        self.port = settings.smtp_port
        self.user = (settings.smtp_user or "").strip()
        self.password = (settings.smtp_password or "").strip()
        self.from_name = (settings.smtp_from_name or "").strip()
        self.sendgrid_api_key = (settings.sendgrid_api_key or "").strip()
        self.sendgrid_from_email = (settings.sendgrid_from_email or "").strip()
        self.resend_api_key = (settings.resend_api_key or "").strip()
        self.resend_from_email = (settings.resend_from_email or "").strip()

    async def send_delivery(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachments: list[Path] | None = None,
    ) -> bool:
        """
        Send a delivery email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (markdown will be rendered as plain text)
            attachments: Optional list of file paths to attach
            
        Returns:
            True if sent successfully
        """
        if not self._is_configured():
            logger.warning("Email not configured, skipping send")
            return False

        if self._use_sendgrid():
            return await self._send_with_sendgrid(
                to_email=to_email,
                subject=subject,
                body=body,
                attachments=attachments,
            )

        if self._use_resend():
            return await self._send_with_resend(
                to_email=to_email,
                subject=subject,
                body=body,
                attachments=attachments,
            )

        try:
            logger.info(
                "Sending email",
                host=self.host,
                port=self.port,
                user=self.user,
                to=to_email,
                subject=subject,
            )
            msg = MIMEMultipart()
            msg["From"] = f"{self.from_name} <{self.user}>"
            msg["To"] = to_email
            msg["Subject"] = subject
            
            # Attach body
            msg.attach(MIMEText(body, "plain"))
            
            # Attach files
            if attachments:
                for file_path in attachments:
                    if file_path.exists():
                        self._attach_file(msg, file_path)
            
            # Send
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)
            
            logger.info(
                "Email sent",
                to=to_email,
                subject=subject,
                attachments=len(attachments) if attachments else 0,
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Email send failed",
                to=to_email,
                error=str(e),
            )
            return False

    def _is_configured(self) -> bool:
        """Check if email is properly configured."""
        if self._use_sendgrid():
            return bool(self.sendgrid_api_key and self.sendgrid_from_email)
        if self._use_resend():
            return bool(self.resend_api_key and self.resend_from_email)
        return bool(
            self.host and
            self.user and
            self.password and
            self.user != "your_email@gmail.com"
        )

    def _use_sendgrid(self) -> bool:
        return bool(self.sendgrid_api_key and self.sendgrid_from_email)

    def _use_resend(self) -> bool:
        return bool(self.resend_api_key and self.resend_from_email)

    async def _send_with_sendgrid(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachments: list[Path] | None = None,
    ) -> bool:
        if attachments:
            logger.warning("SendGrid email does not support attachments in this path")
        message = Mail(
            from_email=self.sendgrid_from_email,
            to_emails=to_email,
            subject=subject,
            plain_text_content=body,
        )

        def _send_sync() -> tuple[int, str]:
            client = SendGridAPIClient(self.sendgrid_api_key)
            response = client.send(message)
            return response.status_code, getattr(response, "body", b"").decode("utf-8", errors="ignore")

        try:
            logger.info("Sending email via SendGrid", to=to_email, subject=subject)
            status, body_text = await asyncio.to_thread(_send_sync)
            if 200 <= status < 300:
                logger.info("SendGrid email sent", to=to_email, status=status)
                return True
            logger.error("SendGrid email failed", to=to_email, status=status, response=body_text)
            return False
        except Exception as exc:
            logger.error("SendGrid email exception", to=to_email, error=str(exc))
            return False

    async def _send_with_resend(
        self,
        to_email: str,
        subject: str,
        body: str,
        attachments: list[Path] | None = None,
    ) -> bool:
        if attachments:
            logger.warning("Resend email does not support attachments in this path")
        payload = {
            "from": f"{self.from_name} <{self.resend_from_email}>"
            if self.from_name
            else self.resend_from_email,
            "to": [to_email],
            "subject": subject,
            "text": body,
        }
        headers = {
            "Authorization": f"Bearer {self.resend_api_key}",
            "Content-Type": "application/json",
        }
        try:
            logger.info("Sending email via Resend", to=to_email, subject=subject)
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post("https://api.resend.com/emails", json=payload, headers=headers)
            if 200 <= response.status_code < 300:
                logger.info("Resend email sent", to=to_email, status=response.status_code)
                return True
            logger.error(
                "Resend email failed",
                to=to_email,
                status=response.status_code,
                response=response.text,
            )
            return False
        except Exception as exc:
            logger.error("Resend email exception", to=to_email, error=str(exc))
            return False

    def _attach_file(self, msg: MIMEMultipart, file_path: Path) -> None:
        """Attach a file to the email."""
        with open(file_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={file_path.name}",
        )
        msg.attach(part)


async def send_concept_delivery(
    to_email: str,
    company_name: str,
    pitch_email_content: str,
    onepager_paths: list[Path],
) -> bool:
    """
    Convenience function to send concept delivery.
    
    Args:
        to_email: Recipient email
        company_name: Company name for subject
        pitch_email_content: The pitch email markdown
        onepager_paths: Paths to one-pager images
        
    Returns:
        True if sent successfully
    """
    client = EmailClient()
    
    # Extract subject from pitch email (first line)
    lines = pitch_email_content.split("\n")
    subject = lines[0].replace("Subject:", "").strip() if lines else f"Concepts for {company_name}"
    
    # Body is everything after the subject line
    body = "\n".join(lines[2:]) if len(lines) > 2 else pitch_email_content
    
    return await client.send_delivery(
        to_email=to_email,
        subject=subject,
        body=body,
        attachments=onepager_paths,
    )
