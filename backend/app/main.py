from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.chat import stream_chat
from app.config import get_settings
from app.ingest import create_tables
from app.models import ChatRequest, ChatResponse, HealthResponse


# ---------------------------------------------------------------------------
# Database session factory
# ---------------------------------------------------------------------------
_engine = None
_session_factory = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _engine, _session_factory
    settings = get_settings()
    _engine = create_async_engine(settings.database_url, pool_size=10, max_overflow=20)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    await create_tables(_engine)
    yield
    await _engine.dispose()


async def get_session() -> AsyncSession:
    async with _session_factory() as session:
        yield session


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="Middle East Geopolitics RAG", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
async def health(session: AsyncSession = Depends(get_session)):
    try:
        await session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "unreachable"
    return HealthResponse(status="ok", db=db_status)


@app.post("/chat")
async def chat(
    request: ChatRequest,
    session: AsyncSession = Depends(get_session),
):
    if not request.messages:
        raise HTTPException(status_code=422, detail="messages must not be empty")

    return StreamingResponse(
        stream_chat(request, session),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
