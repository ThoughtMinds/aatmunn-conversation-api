from typing import Literal, Optional
from .prompts import (
    CONTENT_VALIDATION_TEMPLATE,
    ORCHESTRATOR_TEMPLATE,
    RAG_TEMPLATE,
    SUMMARIZE_TEMPLATE,
)
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables.base import Runnable
from langchain_core.tools.base import BaseTool
from pydantic import BaseModel


def create_chain_for_task(
    task: Literal["content validation", "navigation", "orchestration", "summarization"],
    llm: BaseChatModel,
    output_schema: Optional[BaseModel] = None,
) -> Runnable:
    if output_schema:
        llm = llm.with_structured_output(output_schema, method="json_schema")
    match task:
        case "content validation":
            return CONTENT_VALIDATION_TEMPLATE | llm
        case "navigation":
            return RAG_TEMPLATE | llm
        case "orchestration":
            return ORCHESTRATOR_TEMPLATE | llm
        case "summarization":
            return SUMMARIZE_TEMPLATE | llm
        case default:
            raise Exception("Invalid arguments given to chain factory")
