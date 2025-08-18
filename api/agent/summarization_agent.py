from typing import Dict, TypedDict, Annotated
from pydantic import BaseModel
from json import dumps
from langgraph.graph import StateGraph, END
from api import db, llm, schema, tools
from api.core.logging_config import logger
from sqlmodel import Session
import operator

class ToolCall(BaseModel):
    name: str
    parameters: Dict

# Define the state for the LangGraph
class AgentState(TypedDict):
    query: str
    tool_calls: list
    tool_response: str
    summarized_response: str
    is_valid: bool
    final_response: str

# Initialize tools and models
chat_model = llm.get_ollama_chat_model()
tool_list = [
    tools.summarization.fetch_employee_by_id_db,
    tools.summarization.list_employees_by_skill_level_db,
    tools.summarization.list_employees_by_performance_rating_db,
    tools.summarization.list_employees_by_skill_db,
    tools.summarization.list_employees_by_department_db,
    tools.summarization.list_employees_by_project_db,
    tools.summarization.list_employees_by_shift_db,
    tools.summarization.list_employees_by_hire_year_db,
]
tool_dict = {
    "fetch_employee_by_id_db": tools.summarization.fetch_employee_by_id_db,
    "list_employees_by_skill_level_db": tools.summarization.list_employees_by_skill_level_db,
    "list_employees_by_performance_rating_db": tools.summarization.list_employees_by_performance_rating_db,
    "list_employees_by_skill_db": tools.summarization.list_employees_by_skill_db,
    "list_employees_by_department_db": tools.summarization.list_employees_by_department_db,
    "list_employees_by_project_db": tools.summarization.list_employees_by_project_db,
    "list_employees_by_shift_db": tools.summarization.list_employees_by_shift_db,
    "list_employees_by_hire_year_db": tools.summarization.list_employees_by_hire_year_db,
}
logger.info(f"[Summarization Tools] {', '.join(tool_dict.keys())}")
llm_with_tools = chat_model.bind_tools(tool_list)
summarize_chain = llm.create_chain_for_task(task="summarization", llm=chat_model)
content_validation_chain = llm.create_chain_for_task(
    task="content validation", llm=chat_model, output_schema=schema.ContentValidation
)
FALLBACK_SUMMARY_RESPONSE = "Summary flagged by content policy. Please rephrase or retry"

# Node to invoke tools based on the query
def invoke_tools(state: AgentState) -> AgentState:
    logger.info("Generating summary")
    session = Session(db.engine)
    response = llm_with_tools.invoke(state["query"])
    state["tool_calls"] = response.tool_calls
    state["tool_response"] = ""
    
    if not state["tool_calls"]:
        logger.info("No tool call detected!")
        state["final_response"] = FALLBACK_SUMMARY_RESPONSE
        return state
    
    try:
        for tool_call in state["tool_calls"]:
            name, args, _tool_id = tool_call["name"], tool_call["args"], tool_call["id"]
            func = tool_dict.get(name)
            if func is None:
                raise Exception(f"Function not found: {name}")
            logger.debug(f"Tool: {name} | Args: {args} | ID: {_tool_id}")
            args["session"] = session
            response = func.invoke(args)
            logger.debug(f"Tool Response: {response}")
            response_string = dumps(response)
            state["tool_response"] += f"{name}: {response_string}"
    except Exception as e:
        logger.error(f"Tool invocation failed due to: {e}")
        state["final_response"] = response.content
    finally:
        session.close()
    
    return state

# Node to summarize the tool response
def summarize_response(state: AgentState) -> AgentState:
    if state["final_response"]:
        return state  # Skip if final_response is already set (e.g., no tool calls or error)
    
    response = summarize_chain.invoke(
        {"query": state["query"], "tool_response": state["tool_response"]}
    )
    state["summarized_response"] = response.content
    logger.info(f"Summarized Response: {state['summarized_response']}")
    return state

# Node to validate content
def validate_content(state: AgentState) -> AgentState:
    if state["final_response"]:
        return state  # Skip if final_response is already set
    
    logger.info("Validating Content")
    content_validity = content_validation_chain.invoke(
        {"query": state["query"], "summary": state["summarized_response"]}
    )
    state["is_valid"] = content_validity["content_valid"]
    logger.info(f"Content is valid: {state['is_valid']}")
    
    state["final_response"] = (
        state["summarized_response"] if state["is_valid"] else FALLBACK_SUMMARY_RESPONSE
    )
    return state

# Define the LangGraph workflow
def create_summarization_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("invoke_tools", invoke_tools)
    workflow.add_node("summarize_response", summarize_response)
    workflow.add_node("validate_content", validate_content)
    
    # Define edges
    workflow.set_entry_point("invoke_tools")
    workflow.add_edge("invoke_tools", "summarize_response")
    workflow.add_edge("summarize_response", "validate_content")
    workflow.add_edge("validate_content", END)
    
    return workflow.compile()

# Function to run the summarization agent
def get_summarized_response(query: str) -> str:
    """
    Generates a summarized response for a given query using a LangGraph workflow.

    Args:
        query (str): The user's query for summarization.

    Returns:
        str: The summarized response.
    """
    graph = create_summarization_graph()
    initial_state = {
        "query": query,
        "tool_calls": [],
        "tool_response": "",
        "summarized_response": "",
        "is_valid": False,
        "final_response": ""
    }
    result = graph.invoke(initial_state)
    return result["final_response"]