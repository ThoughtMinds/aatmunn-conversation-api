from langchain_core.prompts import PromptTemplate

ORCHESTRATOR_PROMPT = """
Your task is to analyze the user query and categorize it as belonging to one of the following Categories.

1. navigation - User query is about wanting to see or be taken to a particular page, screen, view etc
eg: User list screen, navigate to task list, take me to entity list, show me settings page

2. summarization - User is requesting information. This could be a query asking for summarizing some data
eg: List all users, list issues after x date, show all active issues

3. task_execution - User wants to execute an action. This does not include naviation. Such as adding, deleting a record
eg: Add new user, delet issue number 3, edit user firstname

Respond with only one of the following category: 
navigation, summarization or task_execution
Only return the category and nothing else
Query: {query}

Category:
"""

ORCHESTRATOR_TEMPLATE = PromptTemplate.from_template(ORCHESTRATOR_PROMPT)

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

RAG_TEMPLATE = PromptTemplate.from_template(RAG_PROMPT)


SUMMARIZE_PROMPT = """
You are an assistant that is given the user query and corresponding API/Database response.
Create a short but descriptive summary from this information.
Make sure you convery important information in an easy to understand format.
Do not mention usage of tools.
Do not add unnecessary formatting.

Query: {query}
Response: {tool_response}

Summary: 
"""

SUMMARIZE_TEMPLATE = PromptTemplate.from_template(SUMMARIZE_PROMPT)


CONTENT_MODERATION_PROMPT = """
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

CONTENT_MODERATION_TEMPLATE = PromptTemplate.from_template(CONTENT_MODERATION_PROMPT)

CHAINED_TOOL_CALL_PROMPT = """
You are an expert Action Identification Agent responsible for determining the next best action to execute based on a user query, available actions, and the history of previous actions and their results.

## Available Actions:
{available_actions}

## User Query:
{query}

## Context Information:
- Previous Action Results (if any):
{context}

## Instructions:
1. Analyze the user's query carefully.
2. Review the results from all previously executed actions.
3. Do not repeat any actions that have already been executed unless absolutely necessary.
4. From the **available actions**, select the **single next best action** that will help progress towards a complete and accurate response.
5. If no further actions are required to answer the user query, return an **empty JSON object**: {{}}
6. The session parameter will be provided by the system, assign it as null

If no further action is required, return {{}}

Response Schema:
{{
    "name": (string) The exact action name from the available actions.
    "parameters": (object) A dictionary of key-value pairs containing the parameters required by the action.
}}

Response:
"""

CHAINED_TOOL_CALL_TEMPLATE = PromptTemplate.from_template(CHAINED_TOOL_CALL_PROMPT)

SUMMARY_SCORE_PROMPT = """
You are a scoring agent. You are given a query and an AI generated summary. Evaluate the given information and return a score and an analysis. The score should be out of 100. The analysis should a one sentence reasoning for the score.

Schema:
{{
    "analysis": Reasoning,
    "score": <score out of 100>
}}

Query: {query}
Summary: {summary}

Response:
"""

SUMMARY_SCORE_TEMPLATE = PromptTemplate.from_template(SUMMARY_SCORE_PROMPT)
