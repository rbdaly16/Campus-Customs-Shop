"""Append-only audit trail of agent-loop activity: output/audit_trail.json.

The file is always a valid JSON array. New entries are appended by writing just before the
closing bracket, so earlier entries are never rewritten, and nothing here ever truncates or
recreates an existing file. A file lock keeps concurrent requests from interleaving writes.
"""

import fcntl
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    RetryPromptPart,
    ToolCallPart,
    ToolReturnPart,
)

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"
MAX_FIELD = 200  # keep entries short: args/results are summaries, not full payloads

log = logging.getLogger("campus_customs.audit")


def audit_path() -> Path:
    # Overridable so tests don't write into the real trail.
    return Path(os.environ.get("AUDIT_TRAIL_PATH", DEFAULT_PATH))


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def short(value: Any, limit: int = MAX_FIELD) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str, separators=(",", ":"))
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def append_entries(entries: list[dict]) -> None:
    """Append entries to the JSON array on disk without rewriting what's already there."""
    if not entries:
        return
    path = audit_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    body = ",\n".join(json.dumps(e, ensure_ascii=False) for e in entries)
    try:
        with open(path, "a+b") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.seek(0, os.SEEK_END)
                if f.tell() == 0:
                    f.write(f"[\n{body}\n]\n".encode())
                    return
                # Find the closing bracket and write the new entries in front of it.
                tail_len = min(f.tell(), 64)
                f.seek(-tail_len, os.SEEK_END)
                tail = f.read(tail_len)
                close = tail.rfind(b"]")
                if close == -1:
                    raise ValueError("audit trail does not end with ']'")
                empty = tail[:close].rstrip().endswith(b"[")
                f.seek(-(tail_len - close), os.SEEK_END)
                f.truncate()  # removes only the closing "]\n" tail
                f.write(((b"\n" if empty else b",\n") + body.encode() + b"\n]\n"))
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except Exception:
        # Auditing must never break a shopper's chat, but it must never silently wipe data either.
        log.exception("Could not append to audit trail at %s", path)


def run_entries(
    run_id: str,
    who: str,
    page: str,
    message: str,
    started: str,
    messages: list[ModelMessage],
    stop_reason: str,
    usage: dict | None = None,
) -> list[dict]:
    """Turn one agent run into audit entries: start, each tool call/result/retry, and stop."""
    base = {"run_id": run_id, "who": who}
    entries = [{**base, "time": started, "event": "run_start", "page": page, "message": short(message, 120)}]
    calls: dict[str, str] = {}
    for m in messages:
        stamp = getattr(m, "timestamp", None)
        for part in getattr(m, "parts", []):
            t = (getattr(part, "timestamp", None) or stamp or datetime.now(timezone.utc)).isoformat(timespec="milliseconds")
            if isinstance(part, ToolCallPart):
                calls[part.tool_call_id] = part.tool_name
                event = "final_output" if part.tool_name == "final_result" else "tool_call"
                entries.append({**base, "time": t, "event": event, "tool": part.tool_name, "args": short(part.args_as_dict())})
            elif isinstance(part, ToolReturnPart) and part.tool_name != "final_result":
                entries.append({**base, "time": t, "event": "tool_result", "tool": part.tool_name, "result": short(part.model_response_str())})
            elif isinstance(part, RetryPromptPart):
                entries.append({
                    **base, "time": t, "event": "retry", "tool": part.tool_name or calls.get(part.tool_call_id, ""),
                    "reason": short(part.content if isinstance(part.content, str) else part.content),
                })
        if isinstance(m, ModelResponse) and m.finish_reason:
            entries[-1].setdefault("model_finish_reason", m.finish_reason)
    entries.append({**base, "time": now(), "event": "run_end", "stop_reason": stop_reason, **(usage or {})})
    return entries
