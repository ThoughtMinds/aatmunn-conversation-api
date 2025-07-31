from langchain_core.prompts import PromptTemplate
from .base import get_ollama_chat_model, get_ollama_chat_fallback_model

RAG_PROMPT = """
Context: {context}
With the provided context, select the most relevant item that matches the query. Always give priority to matching keywords.
If a generic and a more specific match is found, prefer prefer the generic match unless the query has the keywords matching the specific item.
Query: {query}
Schema:
{{

    "id": ID,
    "reasoning": <Reasoning for selecting this ID
}}
Output:
"""

rag_template = PromptTemplate.from_template(RAG_PROMPT)

llama_32_1b, llama_32_3b = get_ollama_chat_model(), get_ollama_chat_fallback_model()
chat_model = llama_32_3b

rag_chain = rag_template | chat_model
