"""Pydantic types shared by the chat API and the shop agent."""

from typing import Literal

from pydantic import BaseModel, Field

# ---- Tool results: what the agent sees when it looks something up in the database ----

StockStatus = Literal["in_stock", "low_stock", "sold_out"]


class ProductSummary(BaseModel):
    """One search hit: enough to pick a product, not enough to quote stock."""

    product_id: str
    name: str
    garment_type: str
    price: float
    colors: list[str]
    short_description: str
    sizes_in_stock: list[str]


class SearchResults(BaseModel):
    """search_products result: exact counts so the agent never has to count a list."""

    total_matches: int = Field(description="How many catalogue products match, even if more than were returned.")
    returned: int
    products: list[ProductSummary]


class ProductInfo(BaseModel):
    """Catalogue facts for one product, from get_product_info."""

    product_id: str
    name: str
    garment_type: str
    price: float
    colors: list[str]
    description: str


class SizeStock(BaseModel):
    size: str
    quantity: int
    status: StockStatus


class StockReport(BaseModel):
    """Stock for one product, from check_stock. Status is computed in code, not by the model."""

    product_id: str
    name: str
    price: float
    sizes: list[SizeStock]
    total_quantity: int
    sizes_in_stock: list[str]
    sold_out_sizes: list[str]
    requested_size: SizeStock | None = None
    note: str | None = None


class SimilarProduct(ProductSummary):
    why_similar: str


class SimilarProducts(BaseModel):
    """find_similar_products result: in-stock alternatives to one product, best match first."""

    based_on: str
    category: str
    size: str | None = None
    products: list[SimilarProduct]
    note: str | None = None


class ProductNotFound(BaseModel):
    error: str
    did_you_mean: list[ProductSummary] = Field(default_factory=list)


# ---- Chat API and agent output ----


MAX_PAGE_RESULTS = 48
# Most recent saved messages loaded into the agent as conversation history each turn.
HISTORY_TURNS = 20


class ProductCard(BaseModel):
    """What the site needs to render a clickable product card (chat or page)."""

    product_id: str
    name: str
    garment_type: str
    price: float
    image_url: str
    short_description: str


class PageResultsPick(BaseModel):
    """The agent's choice of search matches to show on the website itself."""

    title: str = Field(max_length=60, description='Short heading for the results, e.g. "Hoodies" or "Navy tees under $40".')
    product_ids: list[str] = Field(
        max_length=MAX_PAGE_RESULTS,
        description="Every product_id returned by search_products for this request, in the order returned.",
    )


class AgentReply(BaseModel):
    """Structured output the agent must return on every turn."""

    message: str = Field(description="Reply to the shopper in Markdown, in the Campus Customs voice.")
    product_ids: list[str] = Field(
        default_factory=list,
        max_length=6,
        description="product_id values (from tool results only) to show as cards in the chat, most relevant first.",
    )
    page_results: PageResultsPick | None = Field(
        default=None,
        description="Set when the shopper asks to browse a type or group of items; the site shows these on the page.",
    )


class PageResults(BaseModel):
    """Search matches sent to the website, built from the database."""

    title: str
    products: list[ProductCard]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    # The site path the shopper is on (e.g. /products/basic-hoodie-big-yale). The server
    # parses and validates it; nothing else about the page is taken from the browser.
    page_path: str | None = Field(default=None, max_length=300)


class ChatMessage(BaseModel):
    id: int
    role: str
    content: str
    products: list[ProductCard] = Field(default_factory=list)
    # Only on live replies; the page results aren't stored in chat_messages.
    page_results: PageResults | None = None
    created_at: str


# ---- Who is chatting and where they are (built server-side, handed to the agent as deps) ----

PageType = Literal["home", "products", "product", "about", "login", "create_account", "other"]


class Customer(BaseModel):
    """The logged-in shopper, loaded from the session cookie, never from anything typed in chat."""

    user_id: int
    first_name: str
    last_name: str
    email: str
    member_since: str


class PageContext(BaseModel):
    """Where the shopper is, built from the validated page path plus the catalogue."""

    page_type: PageType
    product: ProductInfo | None = None


class ShopDeps(BaseModel):
    """Per-request context handed to the agent's instructions and tools."""

    customer: Customer | None = None  # None means a guest
    page: PageContext = Field(default_factory=lambda: PageContext(page_type="other"))


class AccountInfo(BaseModel):
    """get_my_account result: the current shopper's own account details."""

    logged_in: bool
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    member_since: str | None = None
    saved_messages: int = 0
    note: str | None = None


class PastMessage(BaseModel):
    role: str
    content: str
    created_at: str


class PastChatMatches(BaseModel):
    """search_my_past_chats result: older messages from this shopper's own saved history."""

    available: bool
    matches: list[PastMessage] = Field(default_factory=list)
    note: str | None = None
