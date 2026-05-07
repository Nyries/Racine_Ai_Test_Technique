"""
Hybrid retriever: dense (pgvector cosine) + sparse (BM25 tsvector) + RRF + BGE reranker.

Flow
----
1. Embed the question with BGE-M3 (dense vector)
2. Run dense search  → top-K chunks by cosine similarity
3. Run sparse search → top-K chunks by BM25 (PostgreSQL full-text)
4. Fuse both lists with RRF (Reciprocal Rank Fusion)
5. Rerank the fused top-K with BGE-reranker-v2-m3
6. Return top-N Sources with title, url, source name, and excerpt
"""

from dataclasses import dataclass

from FlagEmbedding import BGEM3FlagModel, FlagReranker
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Source

# ---------------------------------------------------------------------------
# ML model singletons
# ---------------------------------------------------------------------------
_embed_model: BGEM3FlagModel | None = None
_reranker: FlagReranker | None = None


def _get_embed_model() -> BGEM3FlagModel:
    global _embed_model
    if _embed_model is None:
        settings = get_settings()
        _embed_model = BGEM3FlagModel(settings.embed_model, use_fp16=False)
    return _embed_model


def _get_reranker() -> FlagReranker:
    global _reranker
    if _reranker is None:
        settings = get_settings()
        _reranker = FlagReranker(settings.reranker_model, use_fp16=False)
    return _reranker


# ---------------------------------------------------------------------------
# Internal result type (before reranking)
# ---------------------------------------------------------------------------
@dataclass
class _Candidate:
    id: str
    doc_id: str
    title: str
    url: str
    source: str
    date: str
    content: str


# ---------------------------------------------------------------------------
# Dense search
# ---------------------------------------------------------------------------
async def _dense_search(session: AsyncSession, query_vec: list[float], top_k: int) -> list[_Candidate]:
    sql = text("""
        SELECT id::text, doc_id, title, url, source, date, content
        FROM chunks
        ORDER BY embedding <=> CAST(:vec AS vector)
        LIMIT :k
    """)
    result = await session.execute(sql, {"vec": str(query_vec), "k": top_k})
    return [_Candidate(*row) for row in result.fetchall()]


# ---------------------------------------------------------------------------
# Sparse search (BM25 via PostgreSQL full-text)
# ---------------------------------------------------------------------------
async def _sparse_search(session: AsyncSession, question: str, top_k: int) -> list[_Candidate]:
    sql = text("""
        SELECT id::text, doc_id, title, url, source, date, content
        FROM chunks
        WHERE to_tsvector('english', content) @@ plainto_tsquery('english', :q)
        ORDER BY ts_rank(to_tsvector('english', content), plainto_tsquery('english', :q)) DESC
        LIMIT :k
    """)
    result = await session.execute(sql, {"q": question, "k": top_k})
    return [_Candidate(*row) for row in result.fetchall()]


# ---------------------------------------------------------------------------
# Reciprocal Rank Fusion
# ---------------------------------------------------------------------------
def _rrf(lists: list[list[_Candidate]], k: int = 60) -> list[_Candidate]:
    scores: dict[str, float] = {}
    by_id: dict[str, _Candidate] = {}

    for ranked in lists:
        for rank, candidate in enumerate(ranked):
            scores[candidate.id] = scores.get(candidate.id, 0.0) + 1.0 / (k + rank + 1)
            by_id[candidate.id] = candidate

    ranked_ids = sorted(scores, key=lambda cid: scores[cid], reverse=True)
    return [by_id[cid] for cid in ranked_ids]


# ---------------------------------------------------------------------------
# Reranker
# ---------------------------------------------------------------------------
def _rerank(question: str, candidates: list[_Candidate], top_n: int) -> list[_Candidate]:
    if not candidates:
        return []
    reranker = _get_reranker()
    pairs = [[question, c.content] for c in candidates]
    scores = reranker.compute_score(pairs, normalize=True)
    ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
    return [c for c, _ in ranked[:top_n]]


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------
async def retrieve(question: str, session: AsyncSession, rerank: bool = True) -> list[Source]:
    settings = get_settings()

    # 1. Embed the question
    model = _get_embed_model()
    result = model.encode([question], return_dense=True, return_sparse=False, return_colbert_vecs=False)
    query_vec = result["dense_vecs"][0].tolist()

    # 2. Dense + sparse search
    dense = await _dense_search(session, query_vec, settings.retrieval_top_k)
    sparse = await _sparse_search(session, question, settings.retrieval_top_k)

    # 3. RRF fusion
    fused = _rrf([dense, sparse])

    # 4. Rerank (optional — slow on CPU, fast on GPU)
    if rerank:
        top = _rerank(question, fused, settings.rerank_top_n)
    else:
        top = fused[: settings.rerank_top_n]

    # 5. Build Source objects for the LLM
    return [
        Source(
            title=c.title,
            url=c.url,
            source=c.source,
            excerpt=c.content[:400],
        )
        for c in top
    ]


if __name__ == "__main__":
    import argparse
    import asyncio

    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

    async def _test(question: str) -> None:
        engine = create_async_engine(get_settings().database_url)
        async with AsyncSession(engine) as session:
            sources = await retrieve(question, session)
        await engine.dispose()

        print(f"\nQuestion: {question}\n")
        for i, s in enumerate(sources, 1):
            print(f"[{i}] {s.title} — {s.source}")
            print(f"    {s.url}")
            print(f"    {s.excerpt[:120]}...")
            print()

    parser = argparse.ArgumentParser()
    parser.add_argument("question", help="Question to retrieve sources for")
    args = parser.parse_args()
    asyncio.run(_test(args.question))
