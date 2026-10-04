"""Campus Customs API: catalogue products, stock, product images, accounts, and the shop chatbot.

Run from backend/:  uvicorn main:app --reload --port 8000
"""

import json
import logging
import sqlite3
import time
from collections import defaultdict, deque
from contextlib import closing

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from pydantic_ai.exceptions import UsageLimitExceeded

import guests
import tools
from agent import BLOCKED_REPLY, AgentUnavailable, MessageBlocked, run_chat
from auth import optional_user
from auth import router as auth_router
from db import DATA_DIR, get_db
from models import HISTORY_TURNS, ChatMessage, ChatRequest, Customer, ShopDeps

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
CHAT_LIMIT_PER_WINDOW = 20
CHAT_WINDOW_SECONDS = 5 * 60
_recent_messages: dict[str, deque[float]] = defaultdict(deque)

logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(name)s - %(message)s")
log = logging.getLogger("campus_customs")

app = FastAPI(title="Campus Customs API")
app.include_router(auth_router)

# Reloading a returning customer's history filters chat_messages by user_id; index that lookup.
with closing(get_db(readonly=False)) as _conn:
    _conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages (user_id, id)")
    _conn.commit()
# Mount only the photos folder so the database file itself is never served.
# image_file_path values are relative to data/ (e.g. products/<id>.jpg).
app.mount("/images/products", StaticFiles(directory=DATA_DIR / "products"), name="images")


def product_from_row(row: sqlite3.Row) -> dict:
    product = dict(row)
    product["colors"] = json.loads(product["colors"])
    product["search_tags"] = json.loads(product["search_tags"])
    product["image_url"] = f"/images/{product.pop('image_file_path')}"
    return product


@app.get("/api/products")
def list_products() -> list[dict]:
    with closing(get_db()) as conn:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        in_stock: dict[str, list[str]] = {}
        for r in conn.execute("SELECT product_id, size FROM inventory WHERE quantity > 0"):
            in_stock.setdefault(r["product_id"], []).append(r["size"])
    products = [product_from_row(r) for r in rows]
    for p in products:
        # Lets the Products page filter by "in stock in my size" without a request per product.
        sizes = in_stock.get(p["product_id"], [])
        p["sizes_in_stock"] = sorted(sizes, key=lambda s: SIZE_ORDER.index(s) if s in SIZE_ORDER else 99)
        p["category"] = tools.garment_category(p["garment_type"])
    return products


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict:
    with closing(get_db()) as conn:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        stock = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchall()
    product = product_from_row(row)
    product["inventory"] = sorted(
        ({"size": s["size"], "quantity": s["quantity"]} for s in stock),
        key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else 99,
    )
    return product


def load_messages(conn: sqlite3.Connection, user_id: int, limit: int) -> list[ChatMessage]:
    rows = conn.execute(
        "SELECT * FROM (SELECT * FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?) ORDER BY id",
        (user_id, limit),
    ).fetchall()
    messages = []
    for r in rows:
        # Rebuild cards from the catalogue so stored snapshots never show stale prices or image paths.
        stored = json.loads(r["products_json"]) if r["products_json"] else []
        cards = tools.product_cards([p["product_id"] for p in stored if "product_id" in p])
        messages.append(
            ChatMessage(id=r["id"], role=r["role"], content=r["content"], products=cards, created_at=r["created_at"])
        )
    return messages


def cards_for_db(cards: list) -> str | None:
    return json.dumps([c.model_dump() for c in cards]) if cards else None


def too_many_messages(key: str) -> bool:
    """Sliding-window limit per shopper so one browser can't run up model costs."""
    now = time.time()
    sent = _recent_messages[key]
    while sent and sent[0] < now - CHAT_WINDOW_SECONDS:
        sent.popleft()
    if len(sent) >= CHAT_LIMIT_PER_WINDOW:
        return True
    sent.append(now)
    return False


@app.get("/api/chat/history")
def chat_history(request: Request, user: dict | None = Depends(optional_user)) -> list[ChatMessage]:
    """Logged-in shoppers get their saved history; guests get this server session's messages."""
    if user is None:
        return guests.history(guests.guest_id(request))
    with closing(get_db()) as conn:
        return load_messages(conn, user["id"], limit=100)


@app.post("/api/chat")
async def chat(
    body: ChatRequest, request: Request, response: Response, user: dict | None = Depends(optional_user)
) -> ChatMessage:
    gid = None if user else guests.ensure_guest(request, response)
    if too_many_messages(f"user:{user['id']}" if user else f"guest:{gid}"):
        raise HTTPException(status_code=429, detail="Whoa, slow down a little! Try again in a minute.")

    if user:
        with closing(get_db()) as conn:
            history = load_messages(conn, user["id"], limit=HISTORY_TURNS)
        customer = Customer(
            user_id=user["id"],
            first_name=user["first_name"] or "",
            last_name=user["last_name"] or "",
            email=user["email"],
            member_since=user["member_since"],
        )
    else:
        history, customer = guests.history(gid), None
    deps = ShopDeps(customer=customer, page=tools.build_page_context(body.page_path))

    try:
        reply, cards, page_results = await run_chat(body.message, deps, history)
    except MessageBlocked:
        # Not saved: a blocked message in history would get every later turn blocked too.
        log.warning("Chat message blocked by content filter (%s)", f"user {user['id']}" if user else "guest")
        return ChatMessage(id=0, role="assistant", content=BLOCKED_REPLY, created_at="")
    except UsageLimitExceeded:
        log.warning("Chat turn hit the agent loop limit")
        raise HTTPException(status_code=502, detail="That one took too many steps. Try asking a bit more simply?")
    except AgentUnavailable as e:
        log.error("Chat agent unavailable: %s", e)
        raise HTTPException(status_code=503, detail="The shop assistant isn't set up yet.")
    except Exception:
        log.exception("Chat agent failed")
        raise HTTPException(status_code=502, detail="The shop assistant hit a snag. Please try again.")

    if not user:
        # Guests: kept in memory for this session only, never written to the database.
        guests.append(gid, "user", body.message)
        saved = guests.append(gid, "assistant", reply, products=cards)
        return saved.model_copy(update={"page_results": page_results})

    with closing(get_db(readonly=False)) as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)",
            (user["id"], body.message),
        )
        cur = conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, 'assistant', ?, ?)",
            (user["id"], reply, cards_for_db(cards)),
        )
        conn.commit()
        row = conn.execute("SELECT created_at FROM chat_messages WHERE id = ?", (cur.lastrowid,)).fetchone()
    return ChatMessage(
        id=cur.lastrowid,
        role="assistant",
        content=reply,
        products=cards,
        page_results=page_results,
        created_at=row["created_at"],
    )
