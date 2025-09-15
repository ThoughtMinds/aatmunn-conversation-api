from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Defines the application's configuration settings.

    This class uses pydantic-settings to load configuration from a .env file.
    It defines settings for the Ollama models, database initialization,
    ChromaDB persistence, task execution, and project metadata.

    Attributes:
        OLLAMA_BASE_URL (str): The base URL for the Ollama API.
        OLLAMA_CHAT_MODEL (str): The primary chat model to use.
        OLLAMA_CHAT_FALLBACK_MODEL (str): The fallback chat model.
        OLLAMA_EMBEDDINGS_MODEL (str): The model for generating embeddings.
        DATABASE_NAVIGATION_DATA (str): The path to the database navigation data.
        DATABASE_SUMMARIZATION_DATA (str): The path to the database summarization data.
        CHROMA_PERSIST_DIRECTORY (str): The directory for ChromaDB persistence.
        AATMUNN_USERNAME (str): Aatmunn portal (iiop) username
        AATMUNN_PASSWORD (str): Aatmunn portal (iiop) password
        AATMUNN_CLIENT_ID (str): Aatmunn portal (iiop) Client ID
        AATMUNN_CLIENT_SECRET (str): Aatmunn portal (iiop) Client Secret
        AATMUNN_ORG_ID (int): Aatmunn portal (iiop) Organization ID
        TASK_EXECUTION_ENVIRONMENT (str): The environment for task execution
        TASK_EXECUTION_ORG_ID (str): The organization ID for task execution
        TASK_EXECUTION_ORG_NAME (str): The organization name for task execution
        TASK_EXECUTION_USERNAME (str): The username for task execution
        TASK_EXECUTION_PASSWORD (str): The password for task execution
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

    AATMUNN_USERNAME: str
    AATMUNN_PASSWORD: str
    AATMUNN_CLIENT_ID: str
    AATMUNN_CLIENT_SECRET: str
    AATMUNN_ORG_ID: int

    TASK_EXECUTION_ENVIRONMENT: str
    TASK_EXECUTION_ORG_ID: str
    TASK_EXECUTION_ORG_NAME: str
    TASK_EXECUTION_USERNAME: str
    TASK_EXECUTION_PASSWORD: str

    PROJECT_NAME: Optional[str] = "Aatmanunn Conversation API"
    VERSION: Optional[str] = "0.1.0"


settings = Settings()
