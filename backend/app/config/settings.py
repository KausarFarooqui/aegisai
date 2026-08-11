"""
Centralized configuration.

Every environment-dependent value lives here and nowhere else — no hard-coded
DB URLs, API keys, or thresholds anywhere else in the codebase. This is the
first thing to point to in an interview when asked "how do you handle secrets."
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Database ---
    database_url: str

    # --- LLM providers ---
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    llm_primary_provider: str = "groq"  # "groq" | "ollama"

    # --- Embeddings ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimensions: int = 384

    # --- App ---
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:5173"

    # --- Matching / scoring thresholds ---
    entity_similarity_threshold: float = 0.86
    evidence_relevance_threshold: float = 0.72

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached singleton — settings are read from env once per process."""
    return Settings()
