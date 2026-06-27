from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración de la aplicación, cargada desde variables de entorno / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # General
    env: str = "development"
    log_level: str = "INFO"

    # Base de datos
    database_url: str = "postgresql+asyncpg://gitinsight:gitinsight@db:5432/gitinsight"

    # Redis / Celery
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost"

    # Capa de IA
    llm_provider: str = "ollama"
    llm_base_url: str = "http://ollama:11434/v1"
    llm_model: str = "qwen2.5-coder:3b"
    llm_api_key: str = ""
    llm_enabled: bool = True
    llm_timeout_seconds: int = 240
    llm_max_retries: int = 2
    # Si una fase de síntesis IA pasa este nº de segundos sin emitir tokens
    # nuevos, se considera colgada: se cancela y el job degrada con elegancia
    # (continúa sin esa pieza de IA en vez de quedarse congelado).
    llm_stall_seconds: int = 150
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384

    # RAG + Chat (Fase 3)
    rag_enabled: bool = True
    rag_max_files: int = 400  # archivos máx. a indexar por repo (controla coste/tiempo)
    rag_max_chunks: int = 1500  # tope duro de fragmentos por repo
    rag_chunk_max_chars: int = 1600  # tamaño objetivo de cada fragmento
    rag_top_k: int = 6  # fragmentos recuperados por pregunta
    chat_max_tokens: int = 700  # tope de tokens de la respuesta del chat

    # Límites de clonado
    clone_max_size_mb: int = 500
    clone_max_files: int = 20000
    clone_timeout_seconds: int = 120
    repos_cache_dir: str = "/data/repos_cache"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
