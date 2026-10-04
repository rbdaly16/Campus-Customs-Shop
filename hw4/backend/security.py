"""Password hashing and signed session tokens (standard library only)."""

import base64
import hashlib
import hmac
import os
import secrets
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

ALGORITHM = "pbkdf2_sha256"
# OWASP's current recommendation for PBKDF2-HMAC-SHA256.
ITERATIONS = 600_000
# Seed users were hashed as pbkdf2_sha256$<salt>$<hex> with this count and no count stored.
LEGACY_ITERATIONS = 120_000

SESSION_COOKIE = "cc_session"
SESSION_TTL_SECONDS = 7 * 24 * 60 * 60
_SECRET = os.environ.get("SESSION_SECRET") or secrets.token_urlsafe(48)


def _pbkdf2(password: str, salt: str, iterations: int) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()


def hash_password(password: str) -> str:
    """Return pbkdf2_sha256$<iterations>$<salt>$<hex digest> with a fresh random salt."""
    salt = secrets.token_hex(16)
    return f"{ALGORITHM}${ITERATIONS}${salt}${_pbkdf2(password, salt, ITERATIONS)}"


def _parse(stored: str) -> tuple[int, str, str] | None:
    parts = stored.split("$")
    if parts[0] != ALGORITHM:
        return None
    if len(parts) == 4 and parts[1].isdigit():
        return int(parts[1]), parts[2], parts[3]
    if len(parts) == 3:
        return LEGACY_ITERATIONS, parts[1], parts[2]
    return None


def verify_password(password: str, stored: str) -> bool:
    parsed = _parse(stored)
    if parsed is None:
        return False
    iterations, salt, digest = parsed
    return hmac.compare_digest(_pbkdf2(password, salt, iterations), digest)


def needs_rehash(stored: str) -> bool:
    parsed = _parse(stored)
    return parsed is None or parsed[0] < ITERATIONS


# Verifying against this when an email is unknown keeps response times the same,
# so attackers can't tell which emails have accounts from how fast login fails.
DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def _sign(payload: str) -> str:
    sig = hmac.new(_SECRET.encode(), payload.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(sig).decode().rstrip("=")


def create_session_token(user_id: int) -> str:
    payload = f"{user_id}.{int(time.time()) + SESSION_TTL_SECONDS}"
    return f"{payload}.{_sign(payload)}"


def read_session_token(token: str | None) -> int | None:
    """Return the user id if the token is authentic and unexpired."""
    if not token or token.count(".") != 2:
        return None
    user_id, expires, sig = token.split(".")
    if not hmac.compare_digest(sig, _sign(f"{user_id}.{expires}")):
        return None
    if not (user_id.isdigit() and expires.isdigit()) or int(expires) < time.time():
        return None
    return int(user_id)
