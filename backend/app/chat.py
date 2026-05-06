"""
Chat endpoint logic: retrieval → prompt building → OpenRouter streaming → SSE events.

SSE event types
---------------
  {"type": "token",   "content": "..."}   — one streamed token
  {"type": "sources", "sources": [...]}   — cited sources (sent before "done")
  {"type": "done"}                         — stream finished
  {"type": "error",   "message": "..."}   — recoverable error (LLM/DB down, timeout)
"""

import json
from collections.abc import AsyncGenerator

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import ChatRequest, Source
from app.retriever import retrieve

_TIMEOUT = httpx.Timeout(connect=5.0, read=60.0, write=10.0, pool=5.0)

_SYSTEM_TEMPLATE = """\
You are a knowledgeable assistant specializing in Middle East geopolitics.
Answer the user's question using ONLY the sources provided below.
Cite sources inline using their number, e.g. [1], [2].
If the sources do not contain enough information, say so honestly.

Sources:
{sources_block}
"""


def _sources_block(sources: list[Source]) -> str:
    lines = []
    for i, s in enumerate(sources, 1):
        lines.append(f"[{i}] {s.title} ({s.source})\n{s.excerpt}")
    return "\n\n".join(lines)


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def stream_chat(
    request: ChatRequest,
    session: AsyncSession,
) -> AsyncGenerator[str, None]:
    settings = get_settings()

    # --- retrieve sources ---
    try:
        sources = await retrieve(request.messages[-1].content, session)
    except Exception as e:
        yield _sse({"type": "error", "message": f"Retrieval failed: {type(e).__name__}"})
        return

    # --- build messages for the LLM ---
    system_prompt = _SYSTEM_TEMPLATE.format(sources_block=_sources_block(sources))

    messages = [{"role": "system", "content": system_prompt}]
    for msg in request.messages:
        messages.append({"role": msg.role, "content": msg.content})

    # --- call OpenRouter with streaming ---
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "HTTP-Referer": "https://github.com/Nyries/racine-ai",
        "Content-Type": "application/json",
    }
    body = {
        "model": settings.openrouter_model,
        "messages": messages,
        "stream": True,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            async with client.stream(
                "POST",
                f"{settings.openrouter_base_url}/chat/completions",
                headers=headers,
                json=body,
            ) as response:
                if response.status_code == 429:
                    yield _sse({"type": "error", "message": "LLM rate limit reached — please retry in a moment"})
                    return
                if response.status_code != 200:
                    yield _sse({"type": "error", "message": f"LLM returned HTTP {response.status_code}"})
                    return

                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        token = chunk["choices"][0]["delta"].get("content", "")
                        if token:
                            yield _sse({"type": "token", "content": token})
                    except (KeyError, json.JSONDecodeError):
                        continue

    except httpx.TimeoutException:
        yield _sse({"type": "error", "message": "LLM request timed out — please retry"})
        return
    except httpx.ConnectError:
        yield _sse({"type": "error", "message": "Cannot reach LLM — check your connection"})
        return

    # --- send sources then close ---
    yield _sse({"type": "sources", "sources": [s.model_dump() for s in sources]})
    yield _sse({"type": "done"})


if __name__ == "__main__":
    import argparse
    import asyncio
    import sys

    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from app.models import Message

    async def _test(question: str) -> None:
        engine = create_async_engine(get_settings().database_url)
        request = ChatRequest(messages=[Message(role="user", content=question)])

        async with AsyncSession(engine) as session:
            async for event in stream_chat(request, session):
                data = json.loads(event.removeprefix("data: ").strip())
                if data["type"] == "token":
                    print(data["content"], end="", flush=True)
                elif data["type"] == "sources":
                    print("\n\n--- Sources ---")
                    for i, s in enumerate(data["sources"], 1):
                        print(f"[{i}] {s['title']} — {s['source']}")
                elif data["type"] == "error":
                    print(f"\nError: {data['message']}", file=sys.stderr)
        await engine.dispose()

    parser = argparse.ArgumentParser()
    parser.add_argument("question", help="Question to ask the chatbot")
    args = parser.parse_args()
    asyncio.run(_test(args.question))
