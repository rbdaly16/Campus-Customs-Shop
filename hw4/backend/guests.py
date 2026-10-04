"""In-memory chat history for guests: kept while the server runs, never written to the database."""

import secrets
import time
from collections import OrderedDict, deque
from dataclasses import dataclass, field

from fastapi import Request, Response

from models import ChatMessage

GUEST_COOKIE = "cc_guest"
GUEST_TTL_SECONDS = 2 * 60 * 60  # forget a guest after two idle hours
MAX_GUEST_MESSAGES = 20
MAX_GUESTS = 500


@dataclass
class GuestChat:
    last_seen: float = field(default_factory=time.time)
    next_id: int = 1
    messages: deque[ChatMessage] = field(default_factory=lambda: deque(maxlen=MAX_GUEST_MESSAGES))


_chats: OrderedDict[str, GuestChat] = OrderedDict()


def _prune() -> None:
    cutoff = time.time() - GUEST_TTL_SECONDS
    while _chats and (len(_chats) > MAX_GUESTS or next(iter(_chats.values())).last_seen < cutoff):
        _chats.popitem(last=False)


def guest_id(request: Request) -> str | None:
    gid = request.cookies.get(GUEST_COOKIE)
    return gid if gid in _chats else None


def ensure_guest(request: Request, response: Response) -> str:
    """Return this browser's guest id, issuing a random HttpOnly cookie on first chat."""
    _prune()
    gid = guest_id(request)
    if gid is None:
        gid = secrets.token_urlsafe(24)
        _chats[gid] = GuestChat()
        response.set_cookie(GUEST_COOKIE, gid, max_age=GUEST_TTL_SECONDS, httponly=True, samesite="lax")
    _chats[gid].last_seen = time.time()
    _chats.move_to_end(gid)
    return gid


def history(gid: str | None) -> list[ChatMessage]:
    return list(_chats[gid].messages) if gid in _chats else []


def append(gid: str, role: str, content: str, **extra) -> ChatMessage:
    chat = _chats[gid]
    message = ChatMessage(id=chat.next_id, role=role, content=content, created_at=time.strftime("%Y-%m-%d %H:%M:%S"), **extra)
    chat.next_id += 1
    chat.messages.append(message)
    return message
