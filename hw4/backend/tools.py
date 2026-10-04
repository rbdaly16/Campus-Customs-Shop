"""Read-only catalogue tools the shop agent can call."""

import json
import re
import sqlite3
from contextlib import closing

from db import get_db
from models import (
    HISTORY_TURNS,
    MAX_PAGE_RESULTS,
    AccountInfo,
    Customer,
    PageContext,
    PageType,
    PastChatMatches,
    PastMessage,
    ProductCard,
    ProductInfo,
    ProductNotFound,
    ProductSummary,
    SearchResults,
    SimilarProduct,
    SimilarProducts,
    SizeStock,
    StockReport,
    StockStatus,
)

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
# Five or fewer left counts as low stock; the product page uses the same threshold.
LOW_STOCK_THRESHOLD = 5
SIZE_ALIASES = {
    "xsmall": "XS", "extrasmall": "XS",
    "small": "S", "sm": "S",
    "medium": "M", "med": "M", "md": "M",
    "large": "L", "lg": "L",
    "xlarge": "XL", "extralarge": "XL",
    "xxlarge": "XXL", "2xl": "XXL", "2x": "XXL", "xxl": "XXL", "doublexl": "XXL",
}

# garment_type is free text in the database (22 variants); map shopper words onto it.
GARMENT_SYNONYMS = {
    "hoodie": ["hood"],
    "sweatshirt": ["sweatshirt", "crewneck", "hood", "zip"],
    # Not bare "crew": that would match "short-sleeve crew-neck t-shirt".
    "crewneck": ["crewneck"],
    "t-shirt": ["t-shirt", "tee"],
    "tee": ["t-shirt", "tee"],
    "shirt": ["shirt", "tee"],
    "quarter-zip": ["quarter-zip", "1-4", "1/4"],
    "jacket": ["jacket", "fleece", "bomber", "full-zip"],
    "fleece": ["fleece"],
}


def _sort_sizes(stock: list[dict]) -> list[dict]:
    return sorted(stock, key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else 99)


def _stock_by_product(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    stock: dict[str, list[dict]] = {}
    for row in conn.execute("SELECT product_id, size, quantity FROM inventory"):
        stock.setdefault(row["product_id"], []).append({"size": row["size"], "quantity": row["quantity"]})
    return {pid: _sort_sizes(s) for pid, s in stock.items()}


def _matches_garment(garment_type: str, wanted: str) -> bool:
    wanted = wanted.lower().strip().rstrip("s")
    needles = GARMENT_SYNONYMS.get(wanted, [wanted])
    return any(n in garment_type.lower() for n in needles)


def normalize_size(size: str) -> str:
    """Map shopper spellings ("medium", "2XL", "x-large") onto the inventory sizes."""
    key = re.sub(r"[\s\-_.]", "", size.lower())
    return SIZE_ALIASES.get(key, size.strip().upper())


def stock_status(quantity: int) -> StockStatus:
    if quantity <= 0:
        return "sold_out"
    return "low_stock" if quantity <= LOW_STOCK_THRESHOLD else "in_stock"


def _first_sentence(text: str) -> str:
    return re.split(r"(?<=\.)\s", text, maxsplit=1)[0]


def search_products(
    query: str = "",
    garment_type: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    in_stock_size: str | None = None,
    limit: int = 12,
) -> SearchResults:
    """Search the catalogue by keywords and optional filters, best matches first."""
    words = [w for w in re.findall(r"[a-z0-9]+", query.lower()) if len(w) > 1]
    wanted_size = normalize_size(in_stock_size) if in_stock_size else None
    with closing(get_db()) as conn:
        rows = conn.execute("SELECT * FROM catalogue").fetchall()
        stock = _stock_by_product(conn)

    results = []
    for row in rows:
        colors = json.loads(row["colors"])
        tags = json.loads(row["search_tags"])
        sizes = stock.get(row["product_id"], [])
        if garment_type and not _matches_garment(row["garment_type"], garment_type):
            continue
        if color and not any(color.lower() in c.lower() for c in colors):
            continue
        if max_price is not None and row["price"] > max_price:
            continue
        if wanted_size and not any(s["size"] == wanted_size and s["quantity"] > 0 for s in sizes):
            continue
        haystack = " ".join([row["name"], row["garment_type"], row["description"], *colors, *tags]).lower()
        score = sum(haystack.count(w) + 3 * (w in row["name"].lower()) for w in words)
        if words and score == 0:
            continue
        results.append((score, row, colors, sizes))

    results.sort(key=lambda r: (-r[0], r[1]["price"]))
    products = [
        ProductSummary(
            product_id=row["product_id"],
            name=row["name"],
            garment_type=row["garment_type"],
            price=row["price"],
            colors=colors,
            short_description=_first_sentence(row["description"]),
            sizes_in_stock=[s["size"] for s in sizes if s["quantity"] > 0],
        )
        for _, row, colors, sizes in results[: max(1, min(limit, MAX_PAGE_RESULTS))]
    ]
    return SearchResults(total_matches=len(results), returned=len(products), products=products)


def _find_product(conn: sqlite3.Connection, product: str) -> sqlite3.Row | None:
    """Resolve a product_id or an exact product name (any case)."""
    return conn.execute(
        "SELECT * FROM catalogue WHERE product_id = ? OR lower(name) = lower(?) LIMIT 1",
        (product.strip(), product.strip()),
    ).fetchone()


def _not_found(product: str) -> ProductNotFound:
    return ProductNotFound(
        error=f"No product matches {product!r}. Use a product_id from search_products.",
        did_you_mean=search_products(product.replace("-", " "), limit=3).products,
    )


def get_product_info(product: str) -> ProductInfo | ProductNotFound:
    """Description, price, and colors for one product (by product_id or exact name)."""
    with closing(get_db()) as conn:
        row = _find_product(conn, product)
    if row is None:
        return _not_found(product)
    return ProductInfo(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        price=row["price"],
        colors=json.loads(row["colors"]),
        description=row["description"],
    )


def check_stock(product: str, size: str | None = None) -> StockReport | ProductNotFound:
    """Quantity and status per size for one product; optionally highlight one size."""
    with closing(get_db()) as conn:
        row = _find_product(conn, product)
        if row is None:
            return _not_found(product)
        stock = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (row["product_id"],)
        ).fetchall()

    sizes = [
        SizeStock(size=s["size"], quantity=s["quantity"], status=stock_status(s["quantity"]))
        for s in _sort_sizes([dict(s) for s in stock])
    ]
    report = StockReport(
        product_id=row["product_id"],
        name=row["name"],
        price=row["price"],
        sizes=sizes,
        total_quantity=sum(s.quantity for s in sizes),
        sizes_in_stock=[s.size for s in sizes if s.status != "sold_out"],
        sold_out_sizes=[s.size for s in sizes if s.status == "sold_out"],
    )
    if size:
        wanted = normalize_size(size)
        report.requested_size = next((s for s in sizes if s.size == wanted), None)
        if report.requested_size is None:
            offered = ", ".join(s.size for s in sizes)
            report.note = f"Size {size!r} is not offered for this product. Sizes offered: {offered}."
            if wanted not in SIZE_ORDER:
                report.note += " No Campus Customs product comes in this size, so don't offer to find one."
    return report


def product_cards(product_ids: list[str]) -> list[ProductCard]:
    """Build cards from the database, keeping order and silently dropping unknown ids."""
    if not product_ids:
        return []
    with closing(get_db()) as conn:
        placeholders = ",".join("?" * len(product_ids))
        rows = conn.execute(
            f"SELECT product_id, name, garment_type, price, image_file_path, description FROM catalogue WHERE product_id IN ({placeholders})",
            product_ids,
        ).fetchall()
    by_id = {r["product_id"]: r for r in rows}
    seen: set[str] = set()
    cards = []
    for pid in product_ids:
        if pid in by_id and pid not in seen:
            seen.add(pid)
            r = dict(by_id[pid])
            path = r.pop("image_file_path")
            description = r.pop("description")
            cards.append(
                ProductCard(**r, image_url=f"/images/{path}", short_description=_first_sentence(description))
            )
    return cards


# ---- Similar products ----

# Coarse categories over the 22 free-text garment_type values; first match wins.
CATEGORY_RULES = [
    ("hoodie", ("hood",)),
    ("quarter-zip", ("quarter-zip", "1-4", "1/4")),
    ("jacket", ("jacket", "bomber", "fleece")),
    ("crewneck", ("crewneck", "mockneck")),
    ("t-shirt", ("t-shirt", "tee")),
    ("long-sleeve shirt", ("long-sleeve",)),
]
# Tag words already covered by category/color or too generic to count as a shared motif.
GENERIC_TAG_WORDS = {
    "yale", "campus", "customs", "merch", "college", "apparel", "university", "school", "gear",
    "crewneck", "crew", "neck", "hoodie", "hooded", "hood", "sweatshirt", "shirt", "tee", "pullover",
    "long", "sleeve", "short", "zip", "quarter", "full", "jacket", "fleece", "left", "front",
    "navy", "gray", "grey", "white", "blue", "red", "black", "heather", "green", "maroon",
}


def garment_category(garment_type: str) -> str:
    g = garment_type.lower()
    return next((cat for cat, needles in CATEGORY_RULES if any(n in g for n in needles)), "other")


def _tag_words(tags: list[str]) -> set[str]:
    return {w for t in tags for w in re.findall(r"[a-z]+", t.lower()) if len(w) > 2} - GENERIC_TAG_WORDS


def find_similar_products(product: str, size: str | None = None, limit: int = 6) -> SimilarProducts | ProductNotFound:
    """In-stock alternatives: same garment category first, then shared colors/motifs, then close price."""
    wanted = normalize_size(size) if size else None
    with closing(get_db()) as conn:
        base = _find_product(conn, product)
        if base is None:
            return _not_found(product)
        rows = conn.execute("SELECT * FROM catalogue WHERE product_id != ?", (base["product_id"],)).fetchall()
        stock = _stock_by_product(conn)

    category = garment_category(base["garment_type"])
    base_colors = {c.lower() for c in json.loads(base["colors"])}
    base_words = _tag_words(json.loads(base["search_tags"]))
    scored = []
    for row in rows:
        in_stock = [s["size"] for s in stock.get(row["product_id"], []) if s["quantity"] > 0]
        if (wanted and wanted not in in_stock) or not in_stock:
            continue
        colors = json.loads(row["colors"])
        same_cat = garment_category(row["garment_type"]) == category
        shared_colors = sorted(base_colors & {c.lower() for c in colors})
        shared_words = sorted(base_words & _tag_words(json.loads(row["search_tags"])))
        score = 5 * same_cat + 1.5 * len(shared_colors) + len(shared_words) - abs(row["price"] - base["price"]) / 20
        reasons = [f"also a {category}"] if same_cat else []
        if shared_colors:
            reasons.append("shares " + ", ".join(shared_colors))
        if shared_words:
            reasons.append("similar: " + ", ".join(shared_words[:3]))
        scored.append((score, row, colors, in_stock, "; ".join(reasons) or "close in price"))

    scored.sort(key=lambda x: -x[0])
    products = [
        SimilarProduct(
            product_id=row["product_id"],
            name=row["name"],
            garment_type=row["garment_type"],
            price=row["price"],
            colors=colors,
            short_description=_first_sentence(row["description"]),
            sizes_in_stock=in_stock,
            why_similar=why,
        )
        for _, row, colors, in_stock, why in scored[: max(1, min(limit, 12))]
    ]
    return SimilarProducts(
        based_on=base["name"],
        category=category,
        size=wanted,
        products=products,
        note=None if products else f"Nothing similar is in stock{f' in {wanted}' if wanted else ''}.",
    )


# ---- Customer memory and page context ----

PRODUCT_PATH = re.compile(r"^/products/([A-Za-z0-9][A-Za-z0-9-]{0,150})/?$")
STATIC_PAGES: dict[str, PageType] = {
    "/": "home",
    "/products": "products",
    "/about": "about",
    "/login": "login",
    "/create-account": "create_account",
}


def build_page_context(path: str | None) -> PageContext:
    """Turn the browser's page path into trusted context. Only a real product_id ever gets through."""
    if not path:
        return PageContext(page_type="other")
    path = path.split("?")[0].split("#")[0]
    if match := PRODUCT_PATH.match(path):
        info = get_product_info(match.group(1))
        if isinstance(info, ProductInfo):
            return PageContext(page_type="product", product=info)
        return PageContext(page_type="other")
    return PageContext(page_type=STATIC_PAGES.get(path.rstrip("/") or "/", "other"))


def get_account(customer: Customer | None) -> AccountInfo:
    if customer is None:
        return AccountInfo(logged_in=False, note="The shopper is a guest. Nothing about them is known or saved.")
    with closing(get_db()) as conn:
        (saved,) = conn.execute(
            "SELECT COUNT(*) FROM chat_messages WHERE user_id = ?", (customer.user_id,)
        ).fetchone()
    return AccountInfo(
        logged_in=True,
        first_name=customer.first_name,
        last_name=customer.last_name,
        email=customer.email,
        member_since=customer.member_since,
        saved_messages=saved,
    )


def search_past_chats(customer: Customer | None, query: str, limit: int = 6) -> PastChatMatches:
    """Keyword search over this customer's older saved messages (user_id comes from deps, not the model)."""
    if customer is None:
        return PastChatMatches(available=False, note="Guests have no saved history.")
    # Keep 2-letter words: sizes like "xl" are often the whole point of the question.
    words = [w for w in dict.fromkeys(re.findall(r"[a-z0-9]+", query.lower())) if len(w) > 1][:8]
    if not words:
        return PastChatMatches(available=True, note="Give a keyword to search for.")
    # Rank by how many keywords a message contains, newest first on ties, so one strong
    # older match isn't crowded out by many recent messages that share a single common word.
    score = " + ".join("(lower(content) LIKE ?)" for _ in words)
    patterns = [f"%{w}%" for w in words]
    with closing(get_db()) as conn:
        rows = conn.execute(
            f"SELECT role, content, created_at, ({score}) AS score FROM chat_messages"
            " WHERE user_id = ? AND score > 0"
            # Skip the recent messages already loaded into the agent's conversation history.
            " AND id NOT IN (SELECT id FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?)"
            " ORDER BY score DESC, id DESC LIMIT ?",
            (*patterns, customer.user_id, customer.user_id, HISTORY_TURNS, max(1, min(limit, 10))),
        ).fetchall()
    return PastChatMatches(
        available=True,
        matches=[PastMessage(role=r["role"], content=r["content"][:500], created_at=r["created_at"]) for r in rows],
    )
