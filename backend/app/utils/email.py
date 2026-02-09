import json
import smtplib
import urllib.error
import urllib.request
from email.message import EmailMessage

from app.core.config import settings


def send_email(to_email: str, subject: str, body: str) -> None:
    if settings.smtp_suppress_send:
        return
    provider = settings.email_provider.lower()
    if provider == "resend":
        _send_resend(to_email, subject, body)
        return
    if provider != "smtp":
        raise RuntimeError("Email provider is not supported")
    if not settings.smtp_host:
        raise RuntimeError("SMTP is not configured")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from
    message["To"] = to_email
    message.set_content(body)

    if settings.smtp_use_tls:
        server = smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port,
            timeout=settings.smtp_timeout_seconds,
        )
        server.starttls()
    else:
        server = smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port,
            timeout=settings.smtp_timeout_seconds,
        )
    if settings.smtp_username:
        server.login(settings.smtp_username, settings.smtp_password)
    try:
        server.send_message(message)
    finally:
        server.quit()


def _send_resend(to_email: str, subject: str, body: str) -> None:
    if not settings.resend_api_key:
        raise RuntimeError("Resend API key is not configured")
    payload = {
        "from": settings.smtp_from,
        "to": to_email,
        "subject": subject,
        "text": body,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        "https://api.resend.com/emails",
        data=data,
        headers={
            "Authorization": f"Bearer {settings.resend_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=settings.smtp_timeout_seconds) as response:
            if response.status >= 400:
                body_text = response.read().decode("utf-8", errors="ignore")
                raise RuntimeError(f"Resend error: {response.status} {body_text}".strip())
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Resend error: {exc.code} {body_text}".strip()) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Resend connection failed: {exc.reason}") from exc
