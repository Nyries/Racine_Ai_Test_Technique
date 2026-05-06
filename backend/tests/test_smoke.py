"""
Smoke tests — end-to-end checks without calling the real LLM.
OpenRouter is mocked to return a fixed streamed response.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _sse_lines(*tokens: str, sources: list[dict] | None = None) -> list[bytes]:
    """Build a fake SSE byte stream as OpenRouter would return it."""
    lines = []
    for token in tokens:
        chunk = {"choices": [{"delta": {"content": token}}]}
        lines.append(f"data: {json.dumps(chunk)}\n\n".encode())
    lines.append(b"data: [DONE]\n\n")
    return lines


def _mock_openrouter(tokens=("Hello", " world")):
    """Context manager that patches httpx to return a fake streaming response."""
    lines = (
        [f"data: {json.dumps({'choices': [{'delta': {'content': t}}]})}" for t in tokens]
        + ["data: [DONE]"]
    )

    async def _aiter_lines():
        for line in lines:
            yield line

    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.aiter_lines = _aiter_lines

    mock_stream = MagicMock()
    mock_stream.__aenter__ = AsyncMock(return_value=fake_response)
    mock_stream.__aexit__ = AsyncMock(return_value=False)

    mock_client = MagicMock()
    mock_client.stream = MagicMock(return_value=mock_stream)

    mock_client_ctx = MagicMock()
    mock_client_ctx.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client_ctx.__aexit__ = AsyncMock(return_value=False)

    return patch("app.chat.httpx.AsyncClient", return_value=mock_client_ctx)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "db" in data


@pytest.mark.asyncio
async def test_chat_returns_sse_stream(client: AsyncClient):
    with _mock_openrouter(tokens=["Iran", " has", " a nuclear", " program."]):
        response = await client.post(
            "/chat",
            json={"messages": [{"role": "user", "content": "What is Iran's nuclear program?"}]},
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    events = [
        json.loads(line[5:].strip())
        for line in response.text.splitlines()
        if line.startswith("data:")
    ]
    types = [e["type"] for e in events]

    assert "token" in types, "Expected at least one token event"
    assert "sources" in types, "Expected a sources event"
    assert "done" in types, "Expected a done event"
    assert types.index("sources") < types.index("done")


@pytest.mark.asyncio
async def test_chat_empty_messages_returns_422(client: AsyncClient):
    response = await client.post("/chat", json={"messages": []})
    assert response.status_code == 422
