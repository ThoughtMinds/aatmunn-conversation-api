from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Defines the application's configuration settings.

    This class uses pydantic-settings to load configuration from a .env file.
    It defines settings for the Ollama models, database initialization,
    ChromaDB persistence, and project metadata.

    Attributes:
        OLLAMA_BASE_URL (str): The base URL for the Ollama API.
        OLLAMA_CHAT_MODEL (str): The primary chat model to use.
        OLLAMA_CHAT_FALLBACK_MODEL (str): The fallback chat model.
        OLLAMA_EMBEDDINGS_MODEL (str): The model for generating embeddings.
        DATABASE_NAVIGATION_DATA (str): The path to the database navigation data.
        DATABASE_SUMMARIZATION_DATA (str): The path to the database summarization data.
        CHROMA_PERSIST_DIRECTORY (str): The directory for ChromaDB persistence.
        PROJECT_NAME (Optional[str]): The name of the project.
        VERSION (Optional[str]): The version of the project.
    """
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    OLLAMA_BASE_URL: str
    OLLAMA_CHAT_MODEL: str
    OLLAMA_CHAT_FALLBACK_MODEL: str
    OLLAMA_EMBEDDINGS_MODEL: str

    DATABASE_NAVIGATION_DATA: str
    DATABASE_SUMMARIZATION_DATA: str
    CHROMA_PERSIST_DIRECTORY: str

    PROJECT_NAME: str = "Aatmanunn Conversation API"
    VERSION: str = "0.1.0"


settings = Settings()
