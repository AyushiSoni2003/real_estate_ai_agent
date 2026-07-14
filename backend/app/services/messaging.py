"""Messaging service (Twilio + SMTP)."""
import asyncio
import smtplib
from email.message import EmailMessage
from twilio.rest import Client as TwilioClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.lead import Lead
from app.models.message import Message, MessageChannel, MessageDirection

twilio_client = TwilioClient(
    settings.TWILIO_ACCOUNT_SID,
    settings.TWILIO_AUTH_TOKEN,
)

async def send_message(
    lead: Lead,
    message_body: str,
    channel: str,
    db: AsyncSession,
) -> Message:
    external_id = None
    channel_enum = MessageChannel(channel)

    if channel == "whatsapp" and lead.phone:
        external_id = await _send_whatsapp(lead.phone, message_body)
    elif channel == "email" and lead.email:
        external_id = await _send_email(lead.email, lead.full_name, message_body)
    else:
        raise ValueError(f"No valid contact for channel {channel}")

    msg = Message(
        lead_id=lead.id,
        channel=channel_enum,
        direction=MessageDirection.OUTBOUND,
        body=message_body,
        external_id=external_id,
    )
    db.add(msg)
    await db.flush()
    return msg

async def _send_whatsapp(phone: str, body: str) -> str:
    to = f"whatsapp:{phone}" if not phone.startswith("whatsapp:") else phone
    message = twilio_client.messages.create(
        from_=settings.TWILIO_WHATSAPP_FROM,
        to=to,
        body=body,
    )
    return message.sid

async def _send_email(email: str, name: str, body: str) -> str:
    message = EmailMessage()
    message["Subject"] = "A message from your RealtyIQ agent"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = email
    message.set_content(body)
    message.add_alternative(f"<p>{body.replace(chr(10), '<br>')}</p>", subtype="html")

    def _send_sync() -> str:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()
            if settings.SMTP_USERNAME:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(message)
        return "smtp-message"

    return await asyncio.to_thread(_send_sync)
