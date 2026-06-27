from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Central configuration for the entire application.
    Reads values from .env file automatically!
    """

    # Application settings
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # Ollama LLM settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    # Kubernetes settings
    KUBECONFIG_PATH: str = "~/.kube/config"

    # Frontend settings
    STREAMLIT_PORT: int = 8501

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached settings instance.
    So we only read .env file once!
    """
    return Settings()


# Global settings object
settings = get_settings()