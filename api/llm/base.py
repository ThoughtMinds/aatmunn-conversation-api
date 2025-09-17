from api.core.config import settings
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_ollama.chat_models import ChatOllama
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.embeddings import AzureOpenAIEmbeddings
from langchain_community.chat_models import AzureChatOpenAI
from functools import wraps
from langchain_core.embeddings import Embeddings
from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore
from api.core.logging_config import logger
from langchain_community.cache import SQLiteCache
from langchain.globals import set_llm_cache
from typing import Optional

docs_store = LocalFileStore("./static/cache/docs_cache")
query_store = LocalFileStore("./static/cache/query_cache")
set_llm_cache(SQLiteCache(database_path="./static/cache/llm_cache.db"))


def verify_credentials_and_preload():
    """
    Verify credentials for the selected LLM provider and preload Ollama models into memory.

    This function verifies that required credentials are present for the configured LLM provider.
    For Ollama, it preloads all unique chat and embeddings models (including feature-specific models)
    to avoid delays on the first request. It is called during application startup.

    Raises:
        ValueError: If required credentials are missing for the selected LLM provider.
    """
    provider = settings.LLM_PROVIDER.lower()
    logger.info(f"Verifying credentials for LLM provider: {provider}")

    # Verify credentials
    if provider == "ollama":
        if (
            not settings.OLLAMA_BASE_URL
            or not settings.OLLAMA_CHAT_MODEL
            or not settings.OLLAMA_EMBEDDINGS_MODEL
        ):
            logger.error("Missing required Ollama credentials")
            raise ValueError(
                "Missing required Ollama credentials: OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL, or OLLAMA_EMBEDDINGS_MODEL"
            )
    elif provider == "openai":
        if not settings.OPENAI_API_KEY:
            logger.error("Missing required OpenAI credential: OPENAI_API_KEY")
            raise ValueError("Missing required OpenAI credential: OPENAI_API_KEY")
    elif provider == "azure-openai":
        required = [
            settings.AZURE_OPENAI_API_KEY,
            settings.AZURE_OPENAI_API_VERSION,
            settings.AZURE_OPENAI_API_DEPLOYMENT_NAME,
            settings.AZURE_OPENAI_API_EMBEDDINGS_DEPLOYMENT_NAME,
        ]
        if not all(required):
            logger.error("Missing required Azure OpenAI credentials")
            raise ValueError(
                "Missing required Azure OpenAI credentials: AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_API_DEPLOYMENT_NAME, or AZURE_OPENAI_API_EMBEDDINGS_DEPLOYMENT_NAME"
            )
    else:
        logger.error(f"Unsupported LLM provider: {provider}")
        raise ValueError(f"Unsupported LLM provider: {provider}")

    logger.info("Credentials verified successfully")

    # Preload models only for Ollama
    if provider == "ollama":
        logger.info("Preloading Ollama models")

        # Collect unique chat model names
        chat_models = {
            settings.OLLAMA_CHAT_MODEL,
            settings.OLLAMA_SMALL_CHAT_MODEL,
            settings.NAVIGATION_CHAT_MODEL,
            settings.SUMMARIZATION_CHAT_MODEL,
            settings.SUMMARIZATION_SCORE_MODEL,
            settings.CONTENT_VALIDATION_CHAT_MODEL,
            settings.TASK_EXECUTION_CHAT_MODEL,
            settings.CHAINED_TOOL_CALL_CHAT_MODEL,
        }
        chat_models = {model for model in chat_models if model}  # Remove None values

        # Collect unique embedding model names
        embedding_models = {
            settings.OLLAMA_EMBEDDINGS_MODEL,
            settings.NAVIGATION_EMBEDDING_MODEL,
        }
        embedding_models = {
            model for model in embedding_models if model
        }  # Remove None values

        # Preload chat models
        for model in chat_models:
            logger.info(f"Loading chat model: {model}")
            chat_model = get_chat_model(model_name=model, cache=False)
            try:
                chat_model.invoke("Hi")
                logger.info(f"Successfully loaded chat model: {model}")
            except Exception as e:
                logger.error(f"Failed to preload chat model {model}: {str(e)}")

        # Preload embedding models
        for model in embedding_models:
            logger.info(f"Loading embeddings model: {model}")
            embed_model = get_embeddings_model(model_name=model)
            try:
                embed_model.embed_query("Hi")
                logger.info(f"Successfully loaded embeddings model: {model}")
            except Exception as e:
                logger.error(f"Failed to preload embeddings model {model}: {str(e)}")

        logger.info("Completed preloading Ollama models")


def with_cached_embeddings(func):
    """
    Decorator to wrap an embeddings model with caching.

    This decorator takes a function that returns an embeddings model and
    wraps it with CacheBackedEmbeddings to provide caching for both document
    and query embeddings.

    Args:
        func (function): The function that returns an embeddings model.

    Returns:
        function: The wrapped function that returns a cached embeddings model.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        embedding_model: Embeddings = func(*args, **kwargs)
        cached_embedder = CacheBackedEmbeddings.from_bytes_store(
            embedding_model,
            document_embedding_cache=docs_store,
            query_embedding_cache=query_store,
            namespace="embedding_namespace",
            key_encoder="sha256",  # Use SHA-256 instead of SHA-1
        )
        return cached_embedder

    return wrapper


def get_chat_model(model_name: Optional[str] = None, cache: bool = False):
    """
    Initialize a chat model for LLM inference based on the configured provider.

    Args:
        model_name (Optional[str]): Specific model name for feature-specific tasks.
        cache (bool): Whether to enable caching for the chat model.

    Returns:
        Chat model instance (ChatOllama, ChatOpenAI, or AzureChatOpenAI).

    Raises:
        ValueError: If the LLM provider is unsupported or required model name is missing.
    """
    provider = settings.LLM_PROVIDER.lower()
    
    # Set provider-specific default model if model_name is None
    if model_name is None:
        if provider == "ollama":
            model = settings.OLLAMA_CHAT_MODEL
        elif provider == "openai":
            model = settings.OPENAI_CHAT_MODEL
        elif provider == "azure-openai":
            model = settings.AZURE_OPENAI_API_DEPLOYMENT_NAME
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        if model is None:
            raise ValueError(f"No default chat model defined for provider: {provider}")
    else:
        model = model_name

    if provider == "ollama":
        return ChatOllama(
            base_url=settings.OLLAMA_BASE_URL,
            model=model,
            cache=cache,
        )
    elif provider == "openai":
        return ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
            organization=settings.OPENAI_ORGANIZATION,
            model=model,
            cache=cache,
        )
    elif provider == "azure-openai":
        return AzureChatOpenAI(
            azure_endpoint=settings.OPENAI_API_BASE,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            deployment_name=model,
            model=model,
            cache=cache,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


@with_cached_embeddings
def get_embeddings_model(model_name: Optional[str] = None):
    """
    Initialize an embeddings model for LLM inference based on the configured provider.

    Args:
        model_name (Optional[str]): Specific model name for feature-specific tasks.

    Returns:
        Embeddings model instance (OllamaEmbeddings, OpenAIEmbeddings, or AzureOpenAIEmbeddings).

    Raises:
        ValueError: If the LLM provider is unsupported or required model name is missing.
    """
    provider = settings.LLM_PROVIDER.lower()
    
    if model_name is None:
        if provider == "ollama":
            model = settings.OLLAMA_EMBEDDINGS_MODEL
        elif provider == "openai":
            model = settings.OPENAI_EMBEDDINGS_MODEL
        elif provider == "azure-openai":
            model = settings.AZURE_OPENAI_API_EMBEDDINGS_DEPLOYMENT_NAME
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
        if model is None:
            raise ValueError(f"No default embeddings model defined for provider: {provider}")
    else:
        model = model_name

    if provider == "ollama":
        return OllamaEmbeddings(
            base_url=settings.OLLAMA_BASE_URL,
            model=model,
        )
    elif provider == "openai":
        return OpenAIEmbeddings(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
            organization=settings.OPENAI_ORGANIZATION,
            model=model,
        )
    elif provider == "azure-openai":
        return AzureOpenAIEmbeddings(
            azure_endpoint=settings.OPENAI_API_BASE,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            deployment_name=model,
            model=model,
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")