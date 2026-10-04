"""Proves the price fact-check guard works end to end, with a scripted model (no API calls).

Run from backend/:  python test_price_guard.py
"""

import asyncio
import json
import os
import tempfile

# Keep scripted test runs out of the real audit trail.
os.environ.setdefault("AUDIT_TRAIL_PATH", os.path.join(tempfile.gettempdir(), "campus_customs_test_audit.json"))

from pydantic_ai.messages import ModelResponse, RetryPromptPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

import agent
import tools
from models import ChatMessage, ShopDeps

STALE_HISTORY = [
    ChatMessage(id=1, role="user", content="how much is the Branford quarter zip?", created_at=""),
    ChatMessage(id=2, role="assistant", content="The **Branford 1/4 Zip** is **$65**.", created_at=""),
]


def final(message: str) -> ModelResponse:
    args = json.dumps({"message": message, "product_ids": ["branford-1-4-zip"]})
    return ModelResponse(parts=[ToolCallPart(tool_name="final_result", args=args)])


def careless_model(messages, info: AgentInfo) -> ModelResponse:
    """Answers from memory first; after the guard objects, looks the price up properly."""
    last = messages[-1].parts
    if any(isinstance(p, ToolReturnPart) and p.tool_name == "get_product_info" for p in last):
        price = tools.get_product_info("branford-1-4-zip").price
        return final(f"The **Branford 1/4 Zip** is **${price:.0f}**.")
    if any(isinstance(p, RetryPromptPart) for p in last):
        return ModelResponse(parts=[ToolCallPart(tool_name="get_product_info", args={"product": "branford-1-4-zip"})])
    return final("It's still **$65**, same as before!")


async def main() -> None:
    seen = []
    model = FunctionModel(lambda m, i: (seen.append(m[-1]), careless_model(m, i))[1])
    with agent.get_agent().override(model=model):
        reply, cards, _ = await agent.run_chat("remind me what it costs?", ShopDeps(), STALE_HISTORY)

    retries = [p for m in seen for p in m.parts if isinstance(p, RetryPromptPart)]
    assert retries and "$65" in str(retries[0].content), "guard should have rejected the stale $65"
    assert "$72" in reply and "$65" not in reply, reply
    assert cards and cards[0].price == 72.0
    print("PASS: stale $65 was rejected by the guard; final reply:", reply)
    print("Guard feedback sent to the model:", retries[0].content)


if __name__ == "__main__":
    asyncio.run(main())
