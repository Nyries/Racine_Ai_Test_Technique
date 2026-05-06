from typing import Literal

from pydantic import BaseModel


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class Source(BaseModel):
    title: str
    url: str
    source: str    
    excerpt: str   


class ChatRequest(BaseModel):
    messages: list[Message]        
    session_id: str | None = None  


class ChatResponse(BaseModel):
    """Non-streaming response — used for tests and the benchmark script."""
    answer: str
    sources: list[Source]


class HealthResponse(BaseModel):
    status: str
    db: str
