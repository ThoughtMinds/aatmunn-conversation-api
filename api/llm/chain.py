from langchain_core.prompts import PromptTemplate
from .base import get_ollama_chat_model, get_ollama_chat_fallback_model
from api import schema
from typing import List
from .prompts import ORCHESTRATOR_PROMPT, RAG_PROMPT, SUMMARIZE_PROMPT
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables.base import Runnable
from langchain_core.tools.base import BaseTool


llama_32_1b, llama_32_3b = get_ollama_chat_model(), get_ollama_chat_fallback_model()


rag_template = PromptTemplate.from_template(RAG_PROMPT)

rag_model = llama_32_3b.with_structured_output(schema.Navigation, method="json_schema")
rag_chain = rag_template | rag_model


orchestrator_template = PromptTemplate.from_template(ORCHESTRATOR_PROMPT)

orchestrator_chain = orchestrator_template | llama_32_3b


def get_summarize_chain(llm: BaseChatModel, tools: List[BaseTool]) -> List[Runnable, BaseChatModel]:
    llm_with_tools = llm.bind_tools(tools)
    summarize_prompt = PromptTemplate.from_template(SUMMARIZE_PROMPT)
    summarize_chain = summarize_prompt | llm_with_tools
    return summarize_chain
