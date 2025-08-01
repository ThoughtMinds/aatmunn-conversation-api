from api.core.config import settings
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_ollama.chat_models import ChatOllama
from api import schema
from functools import wraps
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain.embeddings import CacheBackedEmbeddings
from langchain.storage import LocalFileStore


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
        # temperature=0.2
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
