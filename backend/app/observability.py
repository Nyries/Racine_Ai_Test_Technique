import logging
import os
import time
from contextlib import contextmanager

from prometheus_client import Counter, Histogram
from pythonjsonlogger import jsonlogger

# ── Prometheus custom metrics ──────────────────────────────────────────────────

EMBEDDING_LATENCY = Histogram(
    "rag_embedding_seconds",
    "Query embedding latency in seconds",
    buckets=[0.05, 0.1, 0.25, 0.5, 1, 2, 5],
)
RERANKER_LATENCY = Histogram(
    "rag_reranker_seconds",
    "BGE reranker latency in seconds",
    buckets=[1, 5, 10, 20, 30, 60],
)
LLM_FIRST_TOKEN_LATENCY = Histogram(
    "rag_llm_first_token_seconds",
    "Time to first LLM token in seconds",
    buckets=[0.5, 1, 2, 5, 10, 30],
)
RAG_ERRORS = Counter(
    "rag_errors_total",
    "Total RAG pipeline errors by stage",
    ["stage"],
)


@contextmanager
def timed(histogram: Histogram):
    start = time.perf_counter()
    try:
        yield
    finally:
        histogram.observe(time.perf_counter() - start)


# ── JSON structured logging ────────────────────────────────────────────────────

def setup_logging() -> None:
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


# ── OpenTelemetry tracing ──────────────────────────────────────────────────────

def setup_tracing() -> None:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    if not endpoint:
        return

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource({SERVICE_NAME: "rag-backend"})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument()
