"""
Ingestion pipeline: reads cleaned corpus shards, chunks documents,
embeds with BGE-M3, and inserts into PostgreSQL / pgvector.

Usage
-----
    python -m app.ingest              # full corpus
    python -m app.ingest --limit 50   # first 50 docs (for testing)
"""

import argparse
import asyncio
import json
import uuid
from pathlib import Path

from FlagEmbedding import BGEM3FlagModel
from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, mapped_column
from transformers import AutoTokenizer

from app.config import get_settings

CLEAN_DIR = Path(__file__).parent.parent.parent / "data" / "clean"
EMBED_DIM = 1024   # BGE-M3 dense vector size
BATCH_SIZE = 32    # chunks per embedding call


# ---------------------------------------------------------------------------
# ORM model
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


class Chunk(Base):
    __tablename__ = "chunks"

    id = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_id = mapped_column(String(256), nullable=False, index=True)
    title = mapped_column(Text, nullable=False)
    url = mapped_column(Text, nullable=False)
    source = mapped_column(String(128), nullable=False)
    date = mapped_column(String(32))
    content = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(EMBED_DIM), nullable=False)


# ---------------------------------------------------------------------------
# Singletons (loaded once, reused across batches)
# ---------------------------------------------------------------------------
_embed_model: BGEM3FlagModel | None = None
_tokenizer: AutoTokenizer | None = None


def _get_model() -> BGEM3FlagModel:
    global _embed_model
    if _embed_model is None:
        settings = get_settings()
        print(f"Loading embedding model: {settings.embed_model}")
        _embed_model = BGEM3FlagModel(settings.embed_model, use_fp16=True)
    return _embed_model


def _get_tokenizer() -> AutoTokenizer:
    global _tokenizer
    if _tokenizer is None:
        settings = get_settings()
        _tokenizer = AutoTokenizer.from_pretrained(settings.embed_model)
    return _tokenizer


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
def split_into_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into token-accurate chunks with sliding window overlap."""
    tokenizer = _get_tokenizer()
    token_ids = tokenizer.encode(text, add_special_tokens=False)

    chunks = []
    start = 0
    while start < len(token_ids):
        end = min(start + chunk_size, len(token_ids))
        decoded = tokenizer.decode(token_ids[start:end], skip_special_tokens=True).strip()
        if decoded:
            chunks.append(decoded)
        if end == len(token_ids):
            break
        start += chunk_size - overlap

    return chunks


def _body(doc: dict) -> str:
    """Return body text without the prepended title."""
    title = doc.get("title", "")
    text = doc.get("text", "")
    if title and text.startswith(title):
        return text[len(title):].lstrip()
    return text


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
async def create_tables(engine) -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        # GIN index for full-text search (BM25 component of hybrid retrieval)
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS chunks_tsv_idx "
            "ON chunks USING GIN (to_tsvector('english', content))"
        ))


async def create_vector_index(engine) -> None:
    """IVFFlat index — must be created AFTER data is inserted (needs rows to train)."""
    async with engine.begin() as conn:
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS chunks_embedding_idx "
            "ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
        ))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def ingest_all(limit: int | None = None) -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)

    print("Creating tables and indexes...")
    await create_tables(engine)

    model = _get_model()

    shard_paths = sorted(CLEAN_DIR.glob("corpus_*.jsonl"))
    if not shard_paths:
        raise FileNotFoundError(f"No corpus shards found in {CLEAN_DIR}")

    total_chunks = 0
    total_docs = 0

    async with AsyncSession(engine) as session:
        for shard_path in shard_paths:
            if limit is not None and total_docs >= limit:
                break

            print(f"\nShard: {shard_path.name}")

            docs = []
            with open(shard_path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        docs.append(json.loads(line))

            if limit is not None:
                docs = docs[: limit - total_docs]

            total_docs += len(docs)
            print(f"  {len(docs)} docs" + (f" (limit {limit})" if limit else ""))

            # Collect all (doc_meta, chunk_text) pairs for this shard
            pairs: list[tuple[dict, str]] = []
            for doc in docs:
                for chunk in split_into_chunks(_body(doc), settings.chunk_size, settings.chunk_overlap):
                    pairs.append((doc, chunk))
            print(f"  {len(pairs)} chunks — embedding...")

            # Embed and insert in batches
            for i in range(0, len(pairs), BATCH_SIZE):
                batch = pairs[i : i + BATCH_SIZE]
                texts = [chunk for _, chunk in batch]

                result = model.encode(
                    texts,
                    batch_size=BATCH_SIZE,
                    return_dense=True,
                    return_sparse=False,
                    return_colbert_vecs=False,
                )
                embeddings = result["dense_vecs"]

                rows = [
                    Chunk(
                        doc_id=doc["id"],
                        title=doc.get("title", ""),
                        url=doc.get("url", ""),
                        source=doc.get("source", ""),
                        date=doc.get("date", ""),
                        content=chunk,
                        embedding=emb.tolist(),
                    )
                    for (doc, chunk), emb in zip(batch, embeddings)
                ]
                session.add_all(rows)
                await session.commit()

                total_chunks += len(rows)
                if (i // BATCH_SIZE) % 20 == 0:
                    print(f"    {i + len(batch)}/{len(pairs)}")

    print("\nCreating vector index (IVFFlat)...")
    await create_vector_index(engine)

    await engine.dispose()
    print(f"\nDone — {total_chunks} chunks inserted")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Max number of docs to ingest (for testing)")
    args = parser.parse_args()
    asyncio.run(ingest_all(limit=args.limit))
