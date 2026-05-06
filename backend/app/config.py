from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Database (pgvector) ---
    database_url: str  # e.g. postgresql+asyncpg://user:pass@host:5432/dbname

    # --- LLM (OpenRouter) ---
    openrouter_api_key: str
    openrouter_model: str = "nvidia/nemotron-3-super-120b-a12b:free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # --- Embedding & reranker models ---
    embed_model: str = "BAAI/bge-m3"
    reranker_model: str = "BAAI/bge-reranker-v2-m3"

    # --- Chunking ---
    chunk_size: int = 512       # tokens
    chunk_overlap: int = 64     # tokens

    # --- Retrieval ---
    retrieval_top_k: int = 20   # candidates before reranking
    rerank_top_n: int = 5       # passages sent to the LLM

    # --- App ---
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
