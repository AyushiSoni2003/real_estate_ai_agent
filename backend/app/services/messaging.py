"""Messaging service (Twilio + SendGrid)."""
from twilio.rest import Client as TwilioClient
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.lead import Lead
from app.models.message import Message, MessageChannel, MessageDirection

twilio_client = TwilioClient(
    settings.TWILIO_ACCOUNT_SID,
    settings.TWILIO_AUTH_TOKEN,
)
sg_client = SendGridAPIClient(settings.SENDGRID_API_KEY)

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
    mail = Mail(
        from_email=settings.SENDGRID_FROM_EMAIL,
        to_emails=email,
        subject="A message from your RealtyIQ agent",
        plain_text_content=body,
        html_content=f"<p>{body.replace(chr(10), '<br>')}</p>",
    )
    response = sg_client.send(mail)
    return response.headers.get("X-Message-Id", "")
