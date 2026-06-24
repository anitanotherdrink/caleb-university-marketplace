"""Email delivery (PRD §8.2). One external integration: SMTP.

In dev, if SMTP is not configured the message is logged to the console and the
verification URL is returned so the flow can be exercised without a mail
server (the UI surfaces it). In prod, SMTP credentials come from env.
"""
from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage

import config
from services import telemetry


def _verification_url(token: str) -> str:
    return f"{config.APP_BASE_URL}/?page=verify&token={token}"


def send_verification_email(to_email: str, token: str) -> str:
    """Send (or simulate) a verification email. Returns the verification URL."""
    url = _verification_url(token)
    subject = "Verify your Caleb University Marketplace account"
    body = (
        "Welcome to the Caleb University Student Marketplace.\n\n"
        "Confirm your institutional email by opening this link:\n"
        f"{url}\n\n"
        f"The link expires in {config.TOKEN_TTL_HOURS} hours.\n"
        "If you did not create an account you can ignore this message."
    )

    if not config.smtp_configured():
        telemetry.emit("verification_email_sent", to=to_email, transport="console")
        print("\n" + "=" * 60)
        print("[DEV] Verification email (SMTP not configured)")
        print(f"  To: {to_email}")
        print(f"  Link: {url}")
        print("=" * 60 + "\n")
        return url

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config.SMTP_FROM
    msg["To"] = to_email
    msg.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
        server.starttls(context=context)
        server.login(config.SMTP_USER, config.SMTP_PASSWORD)
        server.send_message(msg)
    telemetry.emit("verification_email_sent", to=to_email, transport="smtp")
    return url
