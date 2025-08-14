ORCHESTRATOR_PROMPT = """
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

SUMMARIZE_PROMPT = """
You are an assistant that has access to the user query and corresponding API/Database response to it.
Create a summary using the available information.
Present it to the user in a short, easy to understand format. Do not add unnecessary formatting.

Query: {query}
Response: {tool_response}

Summary: 
"""

CONTENT_VALIDATION_PROMPT = """
You are an assistant that has access to the user query and machine generated summary.
Your role is to validate whether the summary is a proper response for the given query. 
Ensure that it is not off-topic, out of context or an incorrect response for the given query
Response Schema:
{{
    "content_valid": <true/false>
}}

Query: {query}
Summary: {summary}

Response: 
"""