from typing import List
from langchain_core.runnables.base import Runnable


def moderate_summry_content(chain: Runnable, query: str, summarized_response: str) -> List[bool]:
    content_validity = chain.invoke(
        {"query": query, "summary": summarized_response}
    )
    content_valid = content_validity["content_valid"]
    is_moderated = not content_valid
    return [content_valid, is_moderated]


__all__ = ["moderate_summry_content"]
