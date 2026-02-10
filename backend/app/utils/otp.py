import hashlib
import hmac
import secrets

from app.core.config import settings


def generate_otp_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(email: str, purpose: str, code: str) -> str:
    payload = f"{email}:{purpose}:{code}".encode("utf-8")
    return hmac.new(settings.otp_secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
