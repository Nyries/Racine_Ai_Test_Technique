"""
RAG benchmark — measures Recall@5, Recall@10, Faithfulness, Answer Relevancy,
and retrieval latency (p50, p95).

Usage
-----
    python -m benchmark.run_benchmark                  # full benchmark
    python -m benchmark.run_benchmark --no-llm         # skip LLM calls (Recall + latency only)
    python -m benchmark.run_benchmark --llm-subset 10  # LLM on first N questions
"""

import argparse
import asyncio
import json
import time
from statistics import median, quantiles

import numpy as np
from tqdm import tqdm
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import get_settings
from app.models import Message, ChatRequest
from app.retriever import retrieve
from app.chat import stream_chat
from benchmark.questions import QUESTIONS


# ---------------------------------------------------------------------------
# Recall@k
# ---------------------------------------------------------------------------
def _hit(sources, keywords: list[str]) -> bool:
    """Return True if any retrieved source contains at least one expected keyword."""
    combined = " ".join(
        (s.title + " " + s.excerpt).lower() for s in sources
    )
    return any(kw.lower() in combined for kw in keywords)


async def measure_recall(session: AsyncSession) -> dict:
    hits_5 = 0
    hits_10 = 0
    lat_fast_ms = []   # embedding + DB + RRF, no reranker
    lat_full_ms = []   # full pipeline with reranker

    for q in tqdm(QUESTIONS, desc="Recall + latency", unit="q"):
        # Without reranker (latency only)
        t0 = time.monotonic()
        await retrieve(q["question"], session, rerank=False)
        lat_fast_ms.append((time.monotonic() - t0) * 1000)

        # With reranker (reuses cached embedding model)
        t0 = time.monotonic()
        sources_full = await retrieve(q["question"], session, rerank=True)
        lat_full_ms.append((time.monotonic() - t0) * 1000)

        if _hit(sources_full[:5], q["keywords"]):
            hits_5 += 1
        if _hit(sources_full[:10], q["keywords"]):
            hits_10 += 1

    n = len(QUESTIONS)

    def _p50(vals): return round(median(sorted(vals)))
    def _p95(vals): return round(quantiles(sorted(vals), n=20)[18])

    return {
        "recall_at_5": round(hits_5 / n, 3),
        "recall_at_10": round(hits_10 / n, 3),
        "latency_fast_p50_ms": _p50(lat_fast_ms),
        "latency_fast_p95_ms": _p95(lat_fast_ms),
        "latency_rerank_p50_ms": _p50(lat_full_ms),
        "latency_rerank_p95_ms": _p95(lat_full_ms),
    }


# ---------------------------------------------------------------------------
# Faithfulness (custom metric)
# ---------------------------------------------------------------------------
def _sentences(text: str) -> list[str]:
    return [s.strip() for s in text.replace("?", ".").replace("!", ".").split(".") if len(s.strip()) > 20]


def _is_supported(sentence: str, sources) -> bool:
    """Check if a 4-word ngram from the sentence appears in any source excerpt."""
    words = sentence.lower().split()
    if len(words) < 4:
        return False
    combined = " ".join(s.excerpt.lower() for s in sources)
    for i in range(len(words) - 3):
        ngram = " ".join(words[i:i + 4])
        if ngram in combined:
            return True
    return False


# ---------------------------------------------------------------------------
# Answer Relevancy (custom metric)
# ---------------------------------------------------------------------------
def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


async def measure_faithfulness_relevancy(
    session: AsyncSession,
    subset: int,
) -> dict:
    from FlagEmbedding import BGEM3FlagModel
    embed_model = BGEM3FlagModel(get_settings().embed_model, use_fp16=False)

    faith_scores = []
    rel_scores = []

    for q in tqdm(QUESTIONS[:subset], desc="Faithfulness + relevancy", unit="q"):
        request = ChatRequest(messages=[Message(role="user", content=q["question"])])

        answer_parts = []
        sources = []
        async for raw in stream_chat(request, session):
            data = json.loads(raw.removeprefix("data: ").strip())
            if data["type"] == "token":
                answer_parts.append(data["content"])
            elif data["type"] == "sources":
                from app.models import Source
                sources = [Source(**s) for s in data["sources"]]

        answer = "".join(answer_parts).strip()
        if not answer:
            continue

        # Faithfulness
        sentences = _sentences(answer)
        if sentences:
            supported = sum(1 for s in sentences if _is_supported(s, sources))
            faith_scores.append(supported / len(sentences))

        # Answer Relevancy
        vecs = embed_model.encode(
            [q["question"], answer],
            return_dense=True,
            return_sparse=False,
            return_colbert_vecs=False,
        )["dense_vecs"]
        rel_scores.append(_cosine(vecs[0], vecs[1]))

        print(f"  Q{q['id']:02d} faith={faith_scores[-1]:.2f}  rel={rel_scores[-1]:.2f}")

    return {
        "faithfulness": round(sum(faith_scores) / len(faith_scores), 3) if faith_scores else None,
        "answer_relevancy": round(sum(rel_scores) / len(rel_scores), 3) if rel_scores else None,
        "llm_questions": subset,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def run(no_llm: bool, llm_subset: int) -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)

    async with AsyncSession(engine) as session:
        print(f"Running Recall@k and latency on {len(QUESTIONS)} questions...")
        recall_results = await measure_recall(session)

        llm_results = {}
        if not no_llm:
            n = min(llm_subset, len(QUESTIONS))
            print(f"\nRunning Faithfulness + Answer Relevancy on {n} questions (LLM)...")
            llm_results = await measure_faithfulness_relevancy(session, subset=n)

    await engine.dispose()

    results = {**recall_results, **llm_results}

    print("\n" + "=" * 52)
    print(f"{'Metric':<28} {'Value':>10}")
    print("-" * 52)
    print(f"{'Recall@5':<28} {recall_results['recall_at_5']:>10.3f}")
    print(f"{'Recall@10':<28} {recall_results['recall_at_10']:>10.3f}")
    if llm_results:
        print(f"{'Faithfulness (custom)':<28} {llm_results['faithfulness']:>10.3f}")
        print(f"{'Answer Relevancy (custom)':<28} {llm_results['answer_relevancy']:>10.3f}")
    print(f"{'Latency fast p50 (ms)':<28} {recall_results['latency_fast_p50_ms']:>10}")
    print(f"{'Latency fast p95 (ms)':<28} {recall_results['latency_fast_p95_ms']:>10}")
    print(f"{'Latency rerank p50 (ms)':<28} {recall_results['latency_rerank_p50_ms']:>10}")
    print(f"{'Latency rerank p95 (ms)':<28} {recall_results['latency_rerank_p95_ms']:>10}")
    print("=" * 52)

    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to benchmark_results.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM calls, only measure Recall and latency")
    parser.add_argument("--llm-subset", type=int, default=15, help="Number of questions to run through the full LLM pipeline (default: 15)")
    args = parser.parse_args()
    asyncio.run(run(no_llm=args.no_llm, llm_subset=args.llm_subset))
