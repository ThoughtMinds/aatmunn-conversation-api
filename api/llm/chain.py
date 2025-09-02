from typing import Literal, Optional
from .prompts import (
    CHAINED_TOOL_CALL_TEMPLATE,
    CONTENT_MODERATION_TEMPLATE,
    ORCHESTRATOR_TEMPLATE,
    RAG_TEMPLATE,
    SUMMARY_SCORE_TEMPLATE,
    SUMMARIZE_TEMPLATE,
)
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables.base import Runnable
from pydantic import BaseModel
from langchain_core.output_parsers.base import BaseOutputParser


def create_chain_for_task(
    task: Literal[
        "chained tool call",
        "content validation",
        "navigation",
        "orchestration",
        "summarization",
        "summary score"
    ],
    llm: BaseChatModel,
    output_schema: Optional[BaseModel] = None,
    output_parser: Optional[BaseOutputParser] = None,
) -> Runnable:
    """
    Create a runnable chain for a specific task.

    This function acts as a factory for creating LangChain runnables with
    appropriate prompts and output parsers for different tasks.

    Args:
        task (Literal): The task for which to create the chain.
        llm (BaseChatModel): The language model to use in the chain.
        output_schema (Optional[BaseModel]): The Pydantic schema for structured output.
        output_parser (Optional[BaseOutputParser]): The output parser to use.

    Returns:
        Runnable: The created LangChain runnable.

    Raises:
        Exception: If the task is invalid.
    """
    if output_schema:
        llm = llm.with_structured_output(output_schema, method="json_schema")
    match task:
        case "content moderation":
            template = CONTENT_MODERATION_TEMPLATE
        case "navigation":
            template = RAG_TEMPLATE
        case "orchestration":
            template = ORCHESTRATOR_TEMPLATE
        case "summarization":
            template = SUMMARIZE_TEMPLATE
        case "chained tool call":
            template = CHAINED_TOOL_CALL_TEMPLATE
        case "summary score":
            template = SUMMARY_SCORE_TEMPLATE
        case default:
            raise Exception("Invalid arguments given to chain factory")
    if output_parser:
        return template | llm | output_parser
    else:
        return template | llm
