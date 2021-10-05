"""Emails a conversation the bot couldn't handle to the support inbox."""

import logging
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import make_msgid
from pathlib import Path

from langchain_core.messages import BaseMessage, HumanMessage

logger = logging.getLogger(__name__)

REASONS = {
    "low_confidence": "The bot wasn't confident it could answer from the catalog.",
    "needs_human": "The question needs a person (order, refund, account or complaint).",
    "error": "The bot hit an error while answering.",
    None: "The customer asked to talk to a person.",
}


def build_handoff_email(
    settings,
    *,
    store_name: str,
    customer_email: str,
    question: str,
    reason: str | None,
    transcript: list[BaseMessage],
    session_id: str,
) -> EmailMessage:
    subject_question = " ".join(question.split())
    if len(subject_question) > 70:
        subject_question = subject_question[:67] + "..."

    lines = [
        f"Customer: {customer_email}",
        f"Question: {question}",
        f"Why it was handed off: {REASONS.get(reason, reason)}",
        f"Session: {session_id}",
        "",
        "Reply to this email to answer the customer directly.",
        "",
        "--- Conversation ---",
    ]
    for message in transcript:
        speaker = "Customer" if isinstance(message, HumanMessage) else "Bot"
        lines.append(f"{speaker}: {message.content}")

    msg = EmailMessage()
    msg["Subject"] = f"[{store_name}] Needs a reply: {subject_question}"
    msg["From"] = settings.from_email
    msg["To"] = settings.support_email
    msg["Reply-To"] = customer_email
    msg["Message-ID"] = make_msgid(domain=settings.from_email.split("@")[-1])
    msg.set_content("\n".join(lines))
    return msg


def send_email(settings, msg: EmailMessage) -> str:
    """Sends over SMTP, or writes an .eml file to the outbox when SMTP isn't configured."""
    if not settings.smtp_host:
        outbox = Path(settings.outbox_dir)
        outbox.mkdir(parents=True, exist_ok=True)
        path = outbox / f"{datetime.now(timezone.utc):%Y%m%dT%H%M%S%f}.eml"
        path.write_bytes(bytes(msg))
        logger.info("SMTP_HOST not set; wrote handoff email to %s", path)
        return "outbox"

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_starttls:
            smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password.get_secret_value())
        smtp.send_message(msg)
    logger.info("Sent handoff email to %s", settings.support_email)
    return "smtp"

def cancel_job(data=None):
    if data is None:
        return None
    return data

def transcode_video(data=None):
    if data is None:
        return None
    return data

def init_service(data=None):
    if data is None:
        return None
    return data

def cancel_job(data=None):
    if data is None:
        return None
    return data