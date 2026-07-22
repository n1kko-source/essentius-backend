from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    supabase_url: str = ""
    supabase_key: str = ""
    google_api_key: str = ""
    tavily_api_key: str = ""

    # true = MockEmbedding/MockLLM/MockGraph; false = Gemini
    use_mock_ai: bool = True
    # Free-tier friendly (AI Studio): Flash-Lite = más cuota / día
    gemini_model: str = "gemini-flash-lite-latest"
    gemini_embedding_model: str = "models/gemini-embedding-001"
    # Tavily free: basic + pocos resultados
    tavily_max_results: int = 3
    # true = endpoints requieren Bearer JWT de Supabase
    auth_required: bool = False
    # auto | memory | supabase — auto picks supabase when creds exist
    notes_backend: str = "auto"

    app_name: str = "Essentius API"
    app_version: str = "0.1.0"
    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000,http://192.168.56.1:3000"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
