"""Google ADK agent with task-manager tools.

Uses Gemini Flash natively — no LiteLLM or [extensions] extra required.
Set GOOGLE_API_KEY in your .env file.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

_BACKEND = os.getenv("BACKEND_URL", "http://fastapi-app:8000")
APP_NAME = "task_manager_agent"


# ── HTTP helper ───────────────────────────────────────────────────────────────

async def _call(method: str, path: str, **kwargs) -> Any:
    async with httpx.AsyncClient(base_url=_BACKEND, timeout=10.0) as client:
        resp = await getattr(client, method)(path, **kwargs)
        resp.raise_for_status()
        return resp.json()


# ── Tool functions ────────────────────────────────────────────────────────────

async def list_all_lists() -> str:
    """Return a summary of every task list the user has."""
    data = await _call("get", "/api/lists")
    if not data:
        return "You have no task lists yet."
    lines = []
    for lst in data:
        done = sum(1 for i in lst["items"] if i["status"] == "done")
        total = len(lst["items"])
        lines.append(f"• **{lst['name']}** — {total} item(s), {done} done")
    return "\n".join(lines)


async def get_list(list_name: str) -> str:
    """Show all items in a specific task list.

    Args:
        list_name: The exact name of the list to retrieve.
    """
    try:
        data = await _call("get", f"/api/lists/by-name/{list_name}")
    except httpx.HTTPStatusError:
        return f"No list named '{list_name}' found."
    items = data.get("items", [])
    if not items:
        return f"The list **{list_name}** is empty."
    lines = [f"**{data['name']}**:"]
    for i in items:
        tick = "✅" if i["status"] == "done" else "⬜"
        lines.append(f"  {tick} `{i['id'][:8]}` {i['text']}")
    return "\n".join(lines)


async def create_list(list_name: str) -> str:
    """Create a new task list.

    Args:
        list_name: Name for the new list.
    """
    try:
        data = await _call("post", "/api/lists", json={"name": list_name})
        return f"✅ Created list **{data['name']}**."
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 409:
            return f"A list named **{list_name}** already exists."
        raise


async def add_item(list_name: str, item_text: str) -> str:
    """Add an item to an existing task list.

    Args:
        list_name: Name of the target list.
        item_text: Text of the new item to add.
    """
    try:
        lst = await _call("get", f"/api/lists/by-name/{list_name}")
    except httpx.HTTPStatusError:
        return f"No list named '{list_name}' found."
    await _call("post", f"/api/lists/{lst['id']}/items", json={"text": item_text})
    return f"✅ Added '{item_text}' to **{list_name}**."


async def mark_item_done(list_name: str, item_id: str) -> str:
    """Mark a task item as done.

    Args:
        list_name: Name of the list.
        item_id: The short item ID (first 8 chars) shown when listing items.
    """
    try:
        lst = await _call("get", f"/api/lists/by-name/{list_name}")
    except httpx.HTTPStatusError:
        return f"No list named '{list_name}' found."
    full_id = next((i["id"] for i in lst["items"] if i["id"].startswith(item_id)), None)
    if not full_id:
        return f"No item with ID starting with '{item_id}' in **{list_name}**."
    await _call(
        "patch",
        f"/api/lists/{lst['id']}/items/{full_id}",
        json={"status": "done"},
    )
    return f"✅ Marked item `{item_id}` as done in **{list_name}**."


async def remove_item(list_name: str, item_id: str) -> str:
    """Remove an item from a task list.

    Args:
        list_name: Name of the list.
        item_id: The short item ID (first 8 chars) shown when listing items.
    """
    try:
        lst = await _call("get", f"/api/lists/by-name/{list_name}")
    except httpx.HTTPStatusError:
        return f"No list named '{list_name}' found."
    full_id = next((i["id"] for i in lst["items"] if i["id"].startswith(item_id)), None)
    if not full_id:
        return f"No item with ID starting with '{item_id}' in **{list_name}**."
    await _call("delete", f"/api/lists/{lst['id']}/items/{full_id}")
    return f"🗑️ Removed item `{item_id}` from **{list_name}**."


async def delete_list(list_name: str) -> str:
    """Permanently delete a task list and all its items.

    Args:
        list_name: Name of the list to delete.
    """
    try:
        lst = await _call("get", f"/api/lists/by-name/{list_name}")
    except httpx.HTTPStatusError:
        return f"No list named '{list_name}' found."
    await _call("delete", f"/api/lists/{lst['id']}")
    return f"🗑️ Deleted list **{list_name}** and all its items."


# ── Agent + Runner (module-level singletons) ──────────────────────────────────
# Runner and session_service must share the same instance — never recreate
# Runner per request or sessions won't be found.

_SYSTEM_PROMPT = """\
You are a friendly task-manager assistant. You help users manage their task lists
through natural conversation. You have access to tools to create, view, update,
and delete task lists and their items.

Guidelines:
- Always confirm the action you took clearly.
- If the user's intent is ambiguous, ask a clarifying question before acting.
- When listing items, always show the short ID so the user can reference it.
- Be concise but friendly.
"""

_task_agent = LlmAgent(
    name=APP_NAME,
    model="gemini-2.0-flash-lite",
    description="LLM-powered task manager agent",
    instruction=_SYSTEM_PROMPT,
    tools=[
        list_all_lists,
        get_list,
        create_list,
        add_item,
        mark_item_done,
        remove_item,
        delete_list,
    ],
)

_session_service = InMemorySessionService()

_runner = Runner(
    agent=_task_agent,
    app_name=APP_NAME,
    session_service=_session_service,   # same instance used everywhere
)


# ── Public entry point ────────────────────────────────────────────────────────

async def run_agent(user_message: str, session_id: str) -> str:
    """Run one conversational turn and return the agent's text reply."""

    # Create the session the first time we see this session_id
    session = await _session_service.get_session(
        app_name=APP_NAME, user_id="user", session_id=session_id
    )
    if session is None:
        await _session_service.create_session(
            app_name=APP_NAME, user_id="user", session_id=session_id
        )

    content = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=user_message)],
    )

    reply_parts: list[str] = []
    async for event in _runner.run_async(
        user_id="user", session_id=session_id, new_message=content
    ):
        if event.is_final_response() and event.content:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    reply_parts.append(part.text)

    return "\n".join(reply_parts) or "I didn't produce a response. Please try again."

async def run_agent_safe(user_message: str, session_id: str) -> str:
    """Wrapper around run_agent with exponential backoff on 429s."""
    import asyncio
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return await run_agent(user_message, session_id)
        except Exception as e:
            is_rate_limit = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
            if is_rate_limit and attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # 1s, 2s
                continue
            if is_rate_limit:
                return "⚠️ The AI service is busy right now (rate limit). Please wait a moment and try again."
            raise