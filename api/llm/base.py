from api.core.config import settings
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_ollama.chat_models import ChatOllama
from functools import wraps
from langchain_core.embeddings import Embeddings
from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore
from api.core.logging_config import logger


docs_store = LocalFileStore("./static/cache/docs_cache")
query_store = LocalFileStore("./static/cache/query_cache")


def with_cached_embeddings(func):
    """
    Decorator to wrap an OllamaEmbeddings model with caching.

    This decorator takes a function that returns an OllamaEmbeddings model and
    wraps it with CacheBackedEmbeddings to provide caching for both document
    and query embeddings.

    Args:
        func (function): The function that returns an OllamaEmbeddings model.

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


def get_ollama_chat_model():
    """Initialize an Ollama Chat Model for LLM inference

    Returns:
        ChatOllama: Ollam Chat Model
    """
    return ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_CHAT_MODEL,
    )


def get_ollama_chat_fallback_model():
    """Initialize a fallback Ollama Chat Model for LLM inference

    Returns:
        ChatOllama: Ollam Chat Model
    """
    return ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_CHAT_FALLBACK_MODEL,
    )


@with_cached_embeddings
def get_ollama_embeddings_model():
    """Initialize an Ollama Embeddings Model for LLM inference

    Returns:
        OllamaEmbeddings: Ollama Embeddings model
    """
    return OllamaEmbeddings(
        base_url=settings.OLLAMA_BASE_URL, model=settings.OLLAMA_EMBEDDINGS_MODEL
    )


def preload_ollama_models():
    """
    Preload the Ollama models into memory.

    This function preloads the chat and embeddings models to avoid delays
    on the first request. It is called during application startup.
    """
    ollama_model = get_ollama_chat_model()
    embed_model = get_ollama_embeddings_model()

    logger.info("Loading [Chat Model]")
    ollama_model.invoke("Hi")
    logger.info("Loading [Embeddings Model]")
    embed_model.embed_query("Hi")
    logger.info("Loaded Models into memory")
