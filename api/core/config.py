from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Defines the application's configuration settings.

    This class uses pydantic-settings to load configuration from a .env file.
    It defines settings for the LLM provider, Ollama models, OpenAI and Azure OpenAI credentials,
    database initialization, ChromaDB persistence, task execution, and project metadata.

    Attributes:
        LLM_PROVIDER (str): The LLM provider to use (ollama, openai, azure-openai).
        OPENAI_API_KEY (Optional[str]): API key for OpenAI.
        OPENAI_API_BASE (Optional[str]): Base URL for OpenAI API.
        OPENAI_ORGANIZATION (Optional[str]): Organization ID for OpenAI.
        OPENAI_CHAT_MODEL (Optional[str]): Name of the OpenAI Chat Model
        OPENAI_EMBEDDINGS_MODEL (Optional[str]): Name of the OpenAI Embeddings Model
        AZURE_OPENAI_API_KEY (Optional[str]): API key for Azure OpenAI.
        AZURE_OPENAI_API_VERSION (Optional[str]): API version for Azure OpenAI.
        AZURE_OPENAI_API_DEPLOYMENT_NAME (Optional[str]): Deployment name for Azure OpenAI API.
        AZURE_OPENAI_API_EMBEDDINGS_DEPLOYMENT_NAME (Optional[str]): Deployment name for Azure OpenAI embeddings.
        OLLAMA_BASE_URL (str): The base URL for the Ollama API.
        OLLAMA_CHAT_MODEL (str): The primary chat model for Ollama.
        OLLAMA_EMBEDDINGS_MODEL (str): The model for generating embeddings in Ollama.
        NAVIGATION_CHAT_MODEL (Optional[str]): Chat model for navigation tasks.
        NAVIGATION_EMBEDDING_MODEL (Optional[str]): Embedding model for navigation tasks.
        ORCHESTRATOR_CHAT_MODEL (Optional[str]): Chat model for orchestration tasks.
        SUMMARIZATION_CHAT_MODEL (Optional[str]): Chat model for summarization tasks.
        SUMMARIZATION_SCORE_MODEL (Optional[str]): Scoring model for summarization tasks.
        CONTENT_VALIDATION_CHAT_MODEL (Optional[str]): Chat model for content validation.
        TASK_EXECUTION_CHAT_MODEL (Optional[str]): Chat model for task execution.
        CHAINED_TOOL_CALL_CHAT_MODEL (Optional[str]): Chat model for chained tool calls.
        DATABASE_NAVIGATION_DATA (str): The path to the database navigation data.
        CHROMA_PERSIST_DIRECTORY (str): The directory for ChromaDB persistence.
        AATMUNN_USERNAME (str): Aatmunn portal (iiop) username.
        AATMUNN_PASSWORD (str): Aatmunn portal (iiop) password.
        AATMUNN_CLIENT_ID (str): Aatmunn portal (iiop) Client ID.
        AATMUNN_CLIENT_SECRET (str): Aatmunn portal (iiop) Client Secret.
        AATMUNN_ORG_ID (int): Aatmunn portal (iiop) Organization ID.
        TASK_EXECUTION_ENVIRONMENT (str): The environment for task execution.
        TASK_EXECUTION_ORG_ID (str): The organization ID for task execution.
        TASK_EXECUTION_ORG_NAME (str): The organization name for task execution.
        TASK_EXECUTION_USERNAME (str): The username for task execution.
        TASK_EXECUTION_PASSWORD (str): The password for task execution.
        PROJECT_NAME (Optional[str]): The name of the project.
        VERSION (Optional[str]): The version of the project.
        NEXT_PUBLIC_API_URL (str): The public API URL for the application.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    LLM_PROVIDER: str = "ollama"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: Optional[str] = None
    OPENAI_ORGANIZATION: Optional[str] = None
    OPENAI_CHAT_MODEL: Optional[str] = None
    OPENAI_EMBEDDINGS_MODEL: Optional[str] = None
    AZURE_OPENAI_API_KEY: Optional[str] = None
    AZURE_OPENAI_API_VERSION: Optional[str] = None
    AZURE_OPENAI_API_DEPLOYMENT_NAME: Optional[str] = None
    AZURE_OPENAI_API_EMBEDDINGS_DEPLOYMENT_NAME: Optional[str] = None
    OLLAMA_BASE_URL: str = "ollama:11434"
    OLLAMA_CHAT_MODEL: str = "llama3.2:3b"
    OLLAMA_EMBEDDINGS_MODEL: str = "nomic-embed-text:v1.5"
    NAVIGATION_CHAT_MODEL: Optional[str] = None
    NAVIGATION_EMBEDDING_MODEL: Optional[str] = None
    ORCHESTRATOR_CHAT_MODEL: Optional[str] = None
    SUMMARIZATION_CHAT_MODEL: Optional[str] = None
    SUMMARIZATION_SCORE_MODEL: Optional[str] = None
    CONTENT_VALIDATION_CHAT_MODEL: Optional[str] = None
    TASK_EXECUTION_CHAT_MODEL: Optional[str] = None
    CHAINED_TOOL_CALL_CHAT_MODEL: Optional[str] = None
    DATABASE_NAVIGATION_DATA: str = "./static/data/navigation_intents.json"
    CHROMA_PERSIST_DIRECTORY: str = "./static/db/chroma"
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
    PROJECT_NAME: Optional[str] = "REST API"
    VERSION: Optional[str] = "v0.0.1"
    NEXT_PUBLIC_API_URL: str = "http://localhost:8000"


settings = Settings()
