from typing import Literal, Optional
from .prompts import (
    CHAINED_TOOL_CALL_TEMPLATE,
    CONTENT_VALIDATION_TEMPLATE,
    ORCHESTRATOR_TEMPLATE,
    RAG_TEMPLATE,
    SUMMARIZE_TEMPLATE,
)
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables.base import Runnable
from pydantic import BaseModel
from langchain_core.output_parsers.base import BaseOutputParser

def create_chain_for_task(
    task: Literal["chained tool call", "content validation", "navigation", "orchestration", "summarization"],
    llm: BaseChatModel,
    output_schema: Optional[BaseModel] = None,
    output_parser: Optional[BaseOutputParser] = None
) -> Runnable:
    if output_schema:
        llm = llm.with_structured_output(output_schema, method="json_schema")
    match task:
        case "content validation":
            template = CONTENT_VALIDATION_TEMPLATE
        case "navigation":
            template = RAG_TEMPLATE
        case "orchestration":
            template = ORCHESTRATOR_TEMPLATE
        case "summarization":
            template = SUMMARIZE_TEMPLATE
        case "chained tool call":
            template = CHAINED_TOOL_CALL_TEMPLATE
        case default:
            raise Exception("Invalid arguments given to chain factory")
    if output_parser:
        return template | llm | output_parser
    else:
        return template | llm