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
You are an assistant that is given the user query and retrieved data.
Create a short but descriptive summary from this information containing important information
Ensure that important details present in the data is mentioned.
Do not mention usage of tools.
Do not add unnecessary formatting.

Query: {query}
Response: {tool_response}

Summary: 
"""

SUMMARIZE_TEMPLATE = PromptTemplate.from_template(SUMMARIZE_PROMPT)


CONTENT_MODERATION_PROMPT = """
You are an assistant that has access to the user query and machine generated summary.
Your task is to validate the given summary.
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
- Previous Action Results Summary:
{context}

## Instructions:
1. Carefully analyze the user's query and break it into sequential steps if needed.
2. Use previous action results and executed actions to inform your next step.
3. Select the single next best action from the available actions that progresses towards a complete response.
4. Do not repeat any action or parameters already executed.
5. If parameters are missing for an update action, fetch them first using the appropriate action.
6. If no further action is required, respond with an empty JSON object `{{}}`.

Response Schema:
{{
    "name": (string) The exact action name from the available actions.
    "parameters": (object) Key-value pairs of parameters required by the action.
}}

Response
"""

CHAINED_TOOL_CALL_TEMPLATE = PromptTemplate.from_template(CHAINED_TOOL_CALL_PROMPT)

SUMMARY_SCORE_PROMPT = """
You are a scoring agent. You are given a query and an AI generated summary. Evaluate the given information and return a score and an analysis. If provided, the score should be assigned based on user provided directive.
The score should be out of 100. The analysis should a one sentence reasoning for the score.

Schema:
{{
    "analysis": Reasoning,
    "score": <score out of 100>
}}

Query: {query}
Summary: {summary}
Directive: {directive}

Response:
"""

SUMMARY_SCORE_TEMPLATE = PromptTemplate.from_template(SUMMARY_SCORE_PROMPT)
