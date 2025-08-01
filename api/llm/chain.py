from langchain_core.prompts import PromptTemplate
from .base import get_ollama_chat_model, get_ollama_chat_fallback_model
from api import schema


llama_32_1b, llama_32_3b = get_ollama_chat_model(), get_ollama_chat_fallback_model()


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

rag_model = llama_32_3b.with_structured_output(schema.Navigation, method="json_schema")
rag_chain = rag_template | rag_model

orchestrator_PROMPT = """
Your task is to analyze the user query and categorize it as belonging to one of the following categories.
1. navigation - The user query is about wanting to be taken to, shown, redirected to a particular screen or view
eg: Take me to user listing, Navigate to product edit, List recent tasks
2. summarization - The user wishes to get a summary of some particular information.
eg: Give me summary of recent performance, Summarize student placement, Tell me about Stock Market trend in 2025
3. task_execution - The user wishes to execute some task or perform an action.
eg: Add a user name mike, Remove John from moderator, Set Gordon age to 45

Respond with only one of the following category: 
navigation, summarization or task_execution
Only return the category and nothing else
Query: {query}

Category:
"""

orchestrator_template = PromptTemplate.from_template(orchestrator_PROMPT)

orchestrator_chain = orchestrator_template | llama_32_3b
