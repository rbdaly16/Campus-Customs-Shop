"""Shop agent wiring: loads the system prompt, model, and tools, and runs one chat turn."""

import logging
import os
import re
import time
import uuid
from functools import cache
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.usage import UsageLimits
from pydantic_ai.providers.openai import OpenAIProvider

import audit
import tools
from models import (
    AgentReply,
    AccountInfo,
    ChatMessage,
    PageContext,
    PageResults,
    PastChatMatches,
    ProductCard,
    ProductInfo,
    ProductNotFound,
    SearchResults,
    SimilarProducts,
    ShopDeps,
    StockReport,
)

BACKEND_DIR = Path(__file__).resolve().parent
PROMPT_PATH = BACKEND_DIR / "prompts" / "prompt.md"
# PORTKEY_API_KEY: read the project's own .env (hw4/.env) first, then fall back to the
# parent folder's .env (the course monorepo keeps one shared key there). Existing values win.
load_dotenv(BACKEND_DIR.parent / ".env")
load_dotenv(BACKEND_DIR.parents[1] / ".env")

log = logging.getLogger("campus_customs.agent")

MODEL_NAME = "gpt5.6-luna"
# How hard the model "thinks" before answering. With tools on /chat/completions this Azure
# deployment only accepts "none" or no setting ("default"). Chosen by bench_agent.py
# (see output/usability.md); override with AGENT_REASONING_EFFORT in .env.
REASONING_EFFORT = os.environ.get("AGENT_REASONING_EFFORT", "default")


def effort_settings(effort: str) -> OpenAIChatModelSettings:
    return OpenAIChatModelSettings() if effort == "default" else OpenAIChatModelSettings(openai_reasoning_effort=effort)
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"


# Hard caps per chat turn so a confused model can't loop forever or run up cost.
LOOP_LIMITS = UsageLimits(request_limit=8, tool_calls_limit=10)


class AgentUnavailable(RuntimeError):
    """Raised when the agent can't be built (e.g. the API key is missing)."""


class MessageBlocked(RuntimeError):
    """Raised when the model provider's content filter rejects the request."""


BLOCKED_REPLY = (
    "Whoa there, friend! I can't help with that one. I'm here for Campus Customs gear: "
    "hoodies, tees, sizes, and stock. What can I find for you?"
)


DOLLARS = re.compile(r"\$\s?(\d{1,4}(?:,\d{3})*(?:\.\d{1,2})?)")
PRICE_FIELDS = re.compile(r'"(?:price|max_price)"\s*:\s*(\d+(?:\.\d+)?)')


def _cents(value: str | float) -> int:
    return round(float(str(value).replace(",", "")) * 100)


def grounded_prices(messages: list[ModelMessage], deps: ShopDeps) -> set[int]:
    """Prices (in cents) the reply may quote: from this run's tool results, the page context,
    and any dollar amounts the shopper typed themselves (e.g. a budget like "under $50")."""
    found: set[int] = set()
    if deps.page.product:
        found.add(_cents(deps.page.product.price))
    for m in messages:
        for part in getattr(m, "parts", []):
            if isinstance(part, ToolReturnPart):
                found |= {_cents(v) for v in PRICE_FIELDS.findall(part.model_response_str())}
            elif isinstance(part, UserPromptPart) and isinstance(part.content, str):
                found |= {_cents(v) for v in DOLLARS.findall(part.content)}
    # Simple totals like "two for $116" are fine when built from real prices.
    found |= {k * c for c in list(found) for k in range(2, 6)}
    return found


def ungrounded_prices(message: str, allowed: set[int]) -> list[str]:
    return [f"${v}" for v in DOLLARS.findall(message) if _cents(v) not in allowed]


@cache
def get_agent() -> Agent[ShopDeps, AgentReply]:
    api_key = os.environ.get("PORTKEY_API_KEY")
    if not api_key:
        raise AgentUnavailable("PORTKEY_API_KEY is missing from the project root .env")
    client = AsyncOpenAI(api_key=api_key, base_url=PORTKEY_BASE_URL, timeout=60, max_retries=2)
    model = OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))

    agent = Agent(
        model,
        deps_type=ShopDeps,
        output_type=AgentReply,
        instructions=PROMPT_PATH.read_text(),
        model_settings=effort_settings(REASONING_EFFORT),
        retries=2,
    )

    @agent.instructions
    def who_and_where(ctx: RunContext[ShopDeps]) -> str:
        """Built in code from server-side deps on every turn; nothing here comes from chat text."""
        c = ctx.deps.customer
        if c:
            who = (
                f"You're chatting with {c.first_name} {c.last_name}, a logged-in Campus Customs customer"
                f" (member since {c.member_since[:10]}). Their conversation is saved and reloads next visit."
                " Call get_my_account for their email or account details, and search_my_past_chats to"
                " recall older conversations."
            )
        else:
            who = (
                "You're chatting with a guest who isn't logged in. You don't know their name, and this"
                " chat isn't saved. Don't ask for personal details. If they want to be remembered,"
                " suggest logging in or creating an account."
            )
        page = ctx.deps.page
        where = {
            "home": "They're on the home page.",
            "products": "They're on the Products page (the full catalogue grid).",
            "product": "They're on a product page; see the [Page context] note on their message.",
            "about": "They're on the About Us page.",
            "login": "They're on the log-in page.",
            "create_account": "They're on the create-account page.",
            "other": "",
        }[page.page_type]
        return f"{who}\n{where}".strip()

    @agent.tool_plain
    def find_similar_products(product: str, size: str | None = None) -> SimilarProducts | ProductNotFound:
        """Find in-stock alternatives to one product, best match first, each with a why_similar reason.

        Use when the shopper's size is sold out, when they ask for "something like this", or for
        alternatives in another color. Pass their size so every suggestion is actually available in it.

        Args:
            product: The product_id (preferred) or exact name to find alternatives for.
            size: Optional size every suggestion must have in stock, e.g. "XL".
        """
        return tools.find_similar_products(product, size)

    @agent.tool
    def get_my_account(ctx: RunContext[ShopDeps]) -> AccountInfo:
        """Get the current shopper's own account: name, email, member-since date, saved message count.

        Only returns the shopper who is chatting right now; there is no way to look up anyone else.
        """
        return tools.get_account(ctx.deps.customer)

    @agent.tool
    def search_my_past_chats(ctx: RunContext[ShopDeps], query: str) -> PastChatMatches:
        """Search this shopper's own older saved chat messages by keyword (e.g. "Branford", "XL").

        Use when they refer to an earlier conversation that isn't in the recent messages.

        Args:
            query: Keywords to look for in their past messages.
        """
        return tools.search_past_chats(ctx.deps.customer, query)

    @agent.tool_plain
    def search_products(
        query: str = "",
        garment_type: str | None = None,
        color: str | None = None,
        max_price: float | None = None,
        in_stock_size: str | None = None,
        limit: int = 12,
    ) -> SearchResults:
        """Find products in the Campus Customs catalogue. Use this to discover product_ids.

        Returns total_matches (the exact number of matching products) and the products themselves.

        Args:
            query: Keywords such as a college, sport, motif, or style (e.g. "Branford", "bulldog vintage").
            garment_type: Optional type filter, e.g. hoodie, crewneck, t-shirt, quarter-zip, jacket, fleece.
            color: Optional color filter, e.g. "navy" or "gray".
            max_price: Optional maximum price in dollars.
            in_stock_size: Optional size that must be in stock, e.g. "M" or "medium".
            limit: Maximum results to return (1-48). Use 48 when the shopper wants to browse a whole type.
        """
        return tools.search_products(query, garment_type, color, max_price, in_stock_size, limit)

    @agent.tool_plain
    def get_product_info(product: str) -> ProductInfo | ProductNotFound:
        """Look up the full description, price, and colors of one product.

        Call this before quoting a price or describing a product in detail.

        Args:
            product: The product_id (preferred) or the exact product name.
        """
        return tools.get_product_info(product)

    @agent.tool_plain
    def check_stock(product: str, size: str | None = None) -> StockReport | ProductNotFound:
        """Look up how many units are in stock for one product, per size.

        Call this for any question about availability, sizes, or quantities.
        Each size has a status: in_stock, low_stock (5 or fewer), or sold_out (0).

        Args:
            product: The product_id (preferred) or the exact product name.
            size: Optional size the shopper asked about, e.g. "XL", "medium", "2XL".
        """
        return tools.check_stock(product, size)

    @agent.output_validator
    def prices_must_be_grounded(ctx: RunContext[ShopDeps], output: AgentReply) -> AgentReply:
        """Fact-check guard: every $ amount in the reply must come from this turn's data.

        Prices remembered from older chats or guessed are sent back to the model to fix,
        before the shopper ever sees them.
        """
        bad = ungrounded_prices(output.message, grounded_prices(ctx.messages, ctx.deps))
        if bad:
            log.warning("Price guard: reply quoted %s with no matching price this turn; asking model to fix", bad)
            raise ModelRetry(
                f"Your reply quotes {', '.join(bad)}, but no tool result or page context in this turn"
                " has that price. Prices may have changed since earlier messages. Look the product up"
                " with get_product_info (or another tool) and quote only prices from those results."
            )
        return output

    return agent


def page_context_note(page: PageContext) -> str:
    """Server-written product facts attached to this turn, so "this" beats older chat topics.

    Built from the catalogue row for a validated product_id. The browser only sends a path,
    so no client text reaches the prompt this way. Only the shopper's own words are stored.
    """
    p = page.product
    if p is None:
        return ""
    return (
        "\n\n[Page context, added by the Campus Customs server: the shopper is viewing"
        f" {p.name} (product_id: {p.product_id}). Garment: {p.garment_type}. Price: ${p.price:.2f}."
        f" Colors: {', '.join(p.colors)}. \"This\" or \"it\" means this product unless they name"
        " another one. Stock is not included: call check_stock for sizes or availability.]"
    )


def to_model_history(messages: list[ChatMessage]) -> list[ModelMessage]:
    """Turn stored chat rows into PydanticAI message history."""
    history: list[ModelMessage] = []
    for m in messages:
        if m.role == "user":
            history.append(ModelRequest(parts=[UserPromptPart(content=m.content)]))
        else:
            history.append(ModelResponse(parts=[TextPart(content=m.content)]))
    return history


async def run_chat(
    message: str,
    deps: ShopDeps,
    history: list[ChatMessage],
    model_settings: OpenAIChatModelSettings | None = None,
    stats: dict | None = None,
) -> tuple[str, list[ProductCard], PageResults | None]:
    # Defuse look-alike notes typed by the shopper so only the server's note reads as page context.
    prompt = message.replace("[Page context", "(quoted: Page context") + page_context_note(deps.page)
    started = time.perf_counter()
    run_id = uuid.uuid4().hex[:12]
    who = f"user:{deps.customer.user_id}" if deps.customer else "guest"
    page = deps.page.page_type + (f":{deps.page.product.product_id}" if deps.page.product else "")
    started_at = audit.now()

    def record(stop_reason: str, messages: list[ModelMessage] | None = None, usage: dict | None = None) -> None:
        audit.append_entries(
            audit.run_entries(run_id, who, page, message, started_at, messages or [], stop_reason, usage)
        )

    try:
        result = await get_agent().run(
            prompt,
            deps=deps,
            message_history=to_model_history(history),
            model_settings=model_settings,
            usage_limits=LOOP_LIMITS,
        )
    except ModelHTTPError as e:
        # Azure (behind Portkey) rejects jailbreak-style prompts with a content_filter error.
        if isinstance(e.body, dict) and e.body.get("code") == "content_filter":
            record("blocked_by_content_filter")
            raise MessageBlocked from e
        record(f"model_error:{e.status_code}")
        raise
    except UsageLimitExceeded as e:
        record(f"loop_limit:{audit.short(str(e), 80)}")
        raise
    except Exception as e:
        record(f"error:{type(e).__name__}")
        raise
    calls = [
        f"{p.tool_name}({p.args_as_json_str()})"
        for m in result.new_messages()
        for p in getattr(m, "parts", [])
        if isinstance(p, ToolCallPart)
    ]
    log.info("Tool calls: %s", "; ".join(calls) or "none")
    usage = result.usage
    turn = {
        "seconds": round(time.perf_counter() - started, 2),
        "model_requests": usage.requests,
        "tool_calls": usage.tool_calls,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "reasoning_tokens": usage.details.get("reasoning_tokens", 0),
        "cached_input_tokens": usage.cache_read_tokens,
        "tools": [c.split("(")[0] for c in calls if not c.startswith("final_result")],
    }
    log.info(
        "Usage: %.2fs, %d model calls, %d tools, %d in (%d cached) / %d out (%d reasoning) tokens",
        turn["seconds"], turn["model_requests"], turn["tool_calls"], turn["input_tokens"],
        turn["cached_input_tokens"], turn["output_tokens"], turn["reasoning_tokens"],
    )
    if stats is not None:
        stats.update(turn)
    record(
        "final_result",
        result.new_messages(),
        {k: turn[k] for k in ("seconds", "model_requests", "tool_calls", "input_tokens", "output_tokens")},
    )
    # Cards come from the database, not the model, so names, prices, and images are always real.
    output = result.output
    page_results = None
    if output.page_results:
        page_cards = tools.product_cards(output.page_results.product_ids)
        if page_cards:
            page_results = PageResults(title=output.page_results.title, products=page_cards)
    return output.message, tools.product_cards(output.product_ids), page_results
