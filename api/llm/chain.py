from langchain_core.prompts import PromptTemplate
from .base import get_ollama_chat_model, get_ollama_chat_fallback_model
from api import schema
from .prompts import ORCHESTRATOR_PROMPT, RAG_PROMPT

llama_32_1b, llama_32_3b = get_ollama_chat_model(), get_ollama_chat_fallback_model()


rag_template = PromptTemplate.from_template(RAG_PROMPT)

rag_model = llama_32_3b.with_structured_output(schema.Navigation, method="json_schema")
rag_chain = rag_template | rag_model


orchestrator_template = PromptTemplate.from_template(ORCHESTRATOR_PROMPT)

orchestrator_chain = orchestrator_template | llama_32_3b
