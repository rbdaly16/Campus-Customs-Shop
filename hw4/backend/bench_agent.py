"""Benchmark the shop agent at different reasoning-effort levels, grading answers against the database.

Run from backend/:  python bench_agent.py [--efforts default none] [--repeats 2]
Runs as a guest, so nothing is written to chat_messages. Prints a Markdown table.
"""

import argparse
import asyncio
import re
import statistics

import tools
from agent import effort_settings, run_chat
from models import ShopDeps


def says(*needles: str):
    return lambda reply, page: all(n.lower() in reply.lower() for n in needles)


# Each case: (question, page path, check(reply, page_results) -> bool, what a correct answer contains).
CASES = [
    ("How much is the Branford quarter zip?", "/", says("$72"), "$72"),
    ("How many XL Grace Hopper College Crewnecks are left?", "/", lambda r, p: re.search(r"\b2\b", r) is not None, "2 left"),
    ("do you have this in XS?", "/products/baseball-left-chest-crewneck", says("sold out"), "sold out in XS"),
    ("do you have this in pink?", "/products/baseball-left-chest-crewneck", says("navy", "white"), "only navy/white"),
    ("what hoodies do you have?", "/", lambda r, p: p is not None and len(p.products) == 27, "27 cards on page"),
    ("It's sold out in XL, what's similar in XL?", "/products/baseball-left-chest-crewneck",
     lambda r, p: "XL" in r and not says("no similar")(r, p), "in-stock XL alternatives"),
]


async def run_case(question: str, path: str, effort: str) -> tuple[str, object, dict]:
    stats: dict = {}
    deps = ShopDeps(customer=None, page=tools.build_page_context(path))
    # Bypass Portkey's response cache so every run really reaches the model.
    settings = effort_settings(effort) | {"extra_headers": {"x-portkey-cache-force-refresh": "true"}}
    reply, _, page = await run_chat(question, deps, [], model_settings=settings, stats=stats)
    return reply, page, stats


async def main(efforts: list[str], repeats: int) -> None:
    rows = []
    for effort in efforts:
        secs, tokens, reasoning, cached, correct, total = [], [], [], [], 0, 0
        for _ in range(repeats):
            for question, path, check, _expected in CASES:
                reply, page, stats = await run_case(question, path, effort)
                ok = check(reply, page)
                correct += ok
                total += 1
                secs.append(stats["seconds"])
                tokens.append(stats["input_tokens"] + stats["output_tokens"])
                reasoning.append(stats["reasoning_tokens"])
                cached.append(stats["cached_input_tokens"] / max(1, stats["input_tokens"]))
                print(f"[{effort}] {'PASS' if ok else 'FAIL'} {stats['seconds']:>5.2f}s  {question}")
        rows.append((effort, statistics.mean(secs), statistics.median(secs), statistics.mean(tokens),
                     statistics.mean(reasoning), statistics.mean(cached), correct, total))

    print("\n| Reasoning effort | Avg seconds | Median seconds | Avg tokens / turn | Avg reasoning tokens | Input served from prompt cache | Correct |")
    print("|---|---|---|---|---|---|---|")
    for effort, avg_s, med_s, avg_t, avg_r, avg_c, correct, total in rows:
        print(f"| `{effort}` | {avg_s:.2f} | {med_s:.2f} | {avg_t:,.0f} | {avg_r:,.0f} | {avg_c:.0%} | {correct}/{total} |")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--efforts", nargs="+", default=["default", "none"])
    parser.add_argument("--repeats", type=int, default=2)
    args = parser.parse_args()
    asyncio.run(main(args.efforts, args.repeats))
