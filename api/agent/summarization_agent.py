from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from typing import TypedDict, List
from api import db, llm

# Define the state to track the workflow
class AgentState(TypedDict):
    messages: List[dict]
    query: str
    table_names: str
    schema: str
    checked_query: str
    query_result: str
    summary: str

chat_model = llm.get_ollama_chat_model()

toolkit = SQLDatabaseToolkit(db=db.sqlite_db, llm=chat_model)
tools = toolkit.get_tools()

# Define system prompt for query generation and execution
system_prompt = """You are a SQL expert designed to interact with a SQL database. Given an input question, follow these steps:
1. List available tables using sql_db_list_tables.
2. Get the schema of relevant tables using sql_db_schema.
3. Generate a syntactically correct {dialect} query, limiting to 5 results unless specified.
4. Check the query using sql_db_query_checker before execution.
5. Execute the query using sql_db_query.
6. Summarize the results in natural language.
Never query all columns; select only relevant ones. Do not make DML statements (INSERT, UPDATE, DELETE, DROP).
Always start by listing tables and querying schemas of relevant tables.
If an error occurs, rewrite the query and try again.
Dialect: {dialect}
Top K: 5
"""

# Create the agent
agent_executor = create_react_agent(chat_model, tools, prompt=system_prompt.format(dialect=db.sqlite_db.dialect, top_k=5))

# Define nodes
def list_tables_node(state: AgentState) -> AgentState:
    result = agent_executor.invoke({"messages": [("user", "List all tables in the database")]}).get("messages")[-1].content
    return {"table_names": result, "messages": state["messages"] + [{"role": "assistant", "content": result}]}

def get_schema_node(state: AgentState) -> AgentState:
    table_names = state["table_names"]
    result = agent_executor.invoke({"messages": [("user", f"Get schema for {table_names}")]}).get("messages")[-1].content
    return {"schema": result, "messages": state["messages"] + [{"role": "assistant", "content": result}]}

def generate_query_node(state: AgentState) -> AgentState:
    query = state["query"]
    schema = state["schema"]
    prompt = f"Given the schema:\n{schema}\nGenerate a SQL query for: {query}"
    result = agent_executor.invoke({"messages": [("user", prompt)]}).get("messages")[-1].content
    return {"checked_query": result, "messages": state["messages"] + [{"role": "assistant", "content": result}]}

def check_query_node(state: AgentState) -> AgentState:
    query = state["checked_query"]
    result = agent_executor.invoke({"messages": [("user", f"Check this query: {query}")]}).get("messages")[-1].content
    return {"checked_query": result, "messages": state["messages"] + [{"role": "assistant", "content": result}]}

def execute_query_node(state: AgentState) -> AgentState:
    query = state["checked_query"]
    result = agent_executor.invoke({"messages": [("user", f"Execute this query: {query}")]}).get("messages")[-1].content
    return {"query_result": result, "messages": state["messages"] + [{"role": "assistant", "content": result}]}

def summarize_result_node(state: AgentState) -> AgentState:
    result = state["query_result"]
    prompt = f"Summarize the following SQL query result in natural language:\n{result}"
    summary = agent_executor.invoke({"messages": [("user", prompt)]}).get("messages")[-1].content
    return {"summary": summary, "messages": state["messages"] + [{"role": "assistant", "content": summary}]}

# Define the workflow
workflow = StateGraph(AgentState)
workflow.add_node("list_tables", list_tables_node)
workflow.add_node("get_schema", get_schema_node)
workflow.add_node("generate_query", generate_query_node)
workflow.add_node("check_query", check_query_node)
workflow.add_node("execute_query", execute_query_node)
workflow.add_node("summarize_result", summarize_result_node)

# Define edges
workflow.add_edge(START, "list_tables")
workflow.add_edge("list_tables", "get_schema")
workflow.add_edge("get_schema", "generate_query")
workflow.add_edge("generate_query", "check_query")
workflow.add_edge("check_query", "execute_query")
workflow.add_edge("execute_query", "summarize_result")
workflow.add_edge("summarize_result", END)

# Compile the graph
summarization_graph = workflow.compile()