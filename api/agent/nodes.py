from typing import List
from langchain_core.runnables.base import Runnable


def moderate_summry_content(
    chain: Runnable, query: str, summarized_response: str
) -> List[bool]:
    """
    Moderates the summary content based on the query and summarized response.

    Args:
        chain (Runnable): The moderation chain.
        query (str): The user's query.
        summarized_response (str): The summarized response.

    Returns:
        List[bool]: A list containing a boolean indicating if the content is valid and a boolean indicating if the content was moderated.
    """
    content_validity = chain.invoke({"query": query, "summary": summarized_response})
    content_valid = content_validity["content_valid"]
    is_moderated = not content_valid
    return [content_valid, is_moderated]


__all__ = ["moderate_summry_content"]
