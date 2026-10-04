"""Create-account, log-in, log-out, and current-user routes."""

import os
import sqlite3
import time
from collections import defaultdict, deque
from contextlib import closing

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field

from db import get_db
from security import (
    DUMMY_HASH,
    SESSION_COOKIE,
    SESSION_TTL_SECONDS,
    create_session_token,
    hash_password,
    needs_rehash,
    read_session_token,
    verify_password,
)

router = APIRouter(prefix="/api/auth")

# Set COOKIE_SECURE=1 when serving over HTTPS so the cookie never travels in plain text.
COOKIE_SECURE = os.environ.get("COOKIE_SECURE") == "1"
MAX_FAILED_LOGINS = 5
LOCKOUT_WINDOW_SECONDS = 15 * 60
_failed_logins: dict[str, deque[float]] = defaultdict(deque)


class RegisterIn(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


def public_user(row: sqlite3.Row) -> dict:
    # Never include password_hash in anything sent to the browser or the chatbot.
    first, last = row["first_name"], row["last_name"]
    if not first:
        first, _, last = row["name"].partition(" ")
    return {
        "id": row["id"],
        "first_name": first,
        "last_name": last,
        "email": row["email"],
        "member_since": row["created_at"],
    }


def start_session(response: Response, user_id: int) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        create_session_token(user_id),
        max_age=SESSION_TTL_SECONDS,
        httponly=True,  # page scripts (and any injected script) can't read it
        samesite="lax",  # not sent on cross-site POSTs, which blocks CSRF
        secure=COOKIE_SECURE,
    )


def too_many_failures(key: str) -> bool:
    attempts = _failed_logins[key]
    while attempts and attempts[0] < time.time() - LOCKOUT_WINDOW_SECONDS:
        attempts.popleft()
    return len(attempts) >= MAX_FAILED_LOGINS


@router.post("/register", status_code=201)
def register(body: RegisterIn, response: Response) -> dict:
    first, last = body.first_name.strip(), body.last_name.strip()
    if not first or not last:
        raise HTTPException(status_code=422, detail="First and last name are required.")
    email = body.email.lower()
    with closing(get_db(readonly=False)) as conn:
        try:
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash, first_name, last_name)"
                " VALUES (?, ?, ?, ?, ?)",
                (f"{first} {last}", email, hash_password(body.password), first, last),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="An account with that email already exists.")
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
    start_session(response, row["id"])
    return public_user(row)


@router.post("/login")
def login(body: LoginIn, request: Request, response: Response) -> dict:
    email = body.email.lower()
    throttle_key = f"{email}|{request.client.host if request.client else ''}"
    if too_many_failures(throttle_key):
        raise HTTPException(status_code=429, detail="Too many attempts. Try again in a few minutes.")
    with closing(get_db(readonly=False)) as conn:
        row = conn.execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()
        valid = verify_password(body.password, row["password_hash"] if row else DUMMY_HASH)
        if not (row and valid):
            _failed_logins[throttle_key].append(time.time())
            # Same message whether the email or the password was wrong.
            raise HTTPException(status_code=401, detail="Incorrect email or password.")
        if needs_rehash(row["password_hash"]):
            # Upgrade older, weaker hashes now that we know the plain password.
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (hash_password(body.password), row["id"]),
            )
            conn.commit()
    _failed_logins.pop(throttle_key, None)
    start_session(response, row["id"])
    return public_user(row)


@router.post("/logout", status_code=204)
def logout(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, httponly=True, samesite="lax", secure=COOKIE_SECURE)


def optional_user(cc_session: str | None = Cookie(default=None)) -> dict | None:
    """FastAPI dependency: the logged-in user from the session cookie, or None for guests."""
    user_id = read_session_token(cc_session)
    if user_id is None:
        return None
    with closing(get_db()) as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return public_user(row) if row else None


@router.get("/me")
def me(user: dict | None = Depends(optional_user)) -> dict | None:
    """The logged-in user, or null for guests (200 either way, so guests see no console errors)."""
    return user
