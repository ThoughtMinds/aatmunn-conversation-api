from typing import Dict, TypedDict, Optional
from pydantic import BaseModel
from json import dumps
from langgraph.graph import StateGraph, END
from langgraph.types import interrupt
from langgraph.checkpoint.memory import MemorySaver
from api import db, llm, tools
from api.core.logging_config import logger
from sqlmodel import Session
from langchain_core.tools import tool


class ToolCall(BaseModel):
    name: str
    parameters: Dict


# Define the state for the LangGraph
class AgentState(TypedDict):
    query: str
    chained: bool
    tool_calls: list
    identified_actions: list
    tool_response: str
    final_response: str
    user_approved: bool
    requires_approval: bool
    actions_to_review: Optional[Dict]


# Initialize tools and models
chat_model = llm.get_ollama_chat_model()
tool_list = [
    tools.aatumunn_api_integration.search_users,
    tools.aatumunn_api_integration.update_user,
    tools.aatumunn_api_integration.get_user_by_id,
]


@tool
def list_tool_names():
    """
    Lists all available tools

    Returns:
        str: Formatted string containing all tools.
    """
    return tools.list_tool_names(tool_list)


tool_list.append(list_tool_names)
TOOL_DESCRIPTION = tools.render_text_description(tool_list)

tool_dict = {tool.name: tool for tool in tool_list}

logger.info(f"[Task Execution Tools] {', '.join(tool_dict.keys())}")

llm_with_tools = chat_model.bind_tools(tool_list)

NO_RESPONSE = "We could not find any relevant information. Please rephrase the query"
FALLBACK_RESPONSE = "Task execution failed. Please rephrase or retry"


# Node to identify actions without executing them
def identify_actions(state: AgentState) -> AgentState:
    response = llm_with_tools.invoke(state["query"])
    state["identified_actions"] = response.tool_calls or []

    # Mock examples for testing
    # state["identified_actions"] = [
    #     {
    #         "name": "search_users",
    #         "args": {"size": 2},
    #         "id": "80e90a74-9566-4870-aec7-9cf7650bf982",
    #         "type": "tool_call",
    #     }
    # ]
    # state["identified_actions"] = [{"name": "update_user", "args": {"first_name": "THIS_USER", "user_id": "1336"}}]

    if not state["identified_actions"]:
        logger.info("No tool call detected!")
        state["final_response"] = NO_RESPONSE
    else:
        logger.info(f"Found {len(state['identified_actions'])} actions to approve")
        logger.critical(state["identified_actions"])
        state["requires_approval"] = True
        state["actions_to_review"] = {
            "question": "Please review and approve the following actions:",
            "actions": [
                {
                    "tool": tool_call["name"],
                    "parameters": tool_call["args"],
                    "description": f"Execute {tool_call['name']} with parameters: {tool_call['args']}",
                }
                for tool_call in state["identified_actions"]
            ],
            "query": state["query"],
        }
    return state


# Human approval node using LangGraph interrupt
def human_approval(state: AgentState) -> AgentState:
    # If approval already provided (resumed), proceed
    if state.get("user_approved", False):
        logger.info("Approval already provided, proceeding to execute approved tools")
        state["requires_approval"] = False
        state["actions_to_review"] = None
        return state

    # If approval is required and actions to review exist, pause for human input
    if state.get("requires_approval", False) and state.get("actions_to_review"):
        logger.warning("Triggering interrupt for approval")
        is_approved = interrupt(state["actions_to_review"])

        # After resuming, interrupt returns the human input (True/False)
        if is_approved:
            state["user_approved"] = True
            state["requires_approval"] = False
            state["actions_to_review"] = None
            return state
        else:
            state["user_approved"] = False
            state["requires_approval"] = False
            state["actions_to_review"] = None
            state["final_response"] = "Task execution cancelled by user."
            return state

    return state


# Node to execute approved tools
def execute_approved_tools(state: AgentState) -> AgentState:
    state["tool_response"] = ""

    try:
        for tool_call in state["identified_actions"]:
            name, args, _tool_id = tool_call["name"], tool_call["args"], tool_call["id"]
            func = tool_dict.get(name)
            if func is None:
                raise Exception(f"Function not found: {name}")
            logger.info(f"Executing approved tool: {name} | Args: {args}")
            response = func.invoke(args)
            logger.info(f"Tool Response:\n{response}")
            response_string = dumps(response)
            state["tool_response"] += f"{name}: {response_string}\n"
        state["final_response"] = state["tool_response"]
    except Exception as e:
        logger.error(f"Tool execution failed due to: {e}")
        state["final_response"] = FALLBACK_RESPONSE

    return state


# Router function to determine entry point
def tool_call_router(state: AgentState) -> str:
    is_chained = state["chained"]
    logger.critical(f"Chained Tool Call: {is_chained}")
    # Always route to identify_actions first
    return "identify_actions"


# Define the workflow graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("identify_actions", identify_actions)
workflow.add_node("human_approval", human_approval)
workflow.add_node("execute_approved_tools", execute_approved_tools)

# Set conditional entry point
workflow.set_conditional_entry_point(
    tool_call_router,
    {
        "identify_actions": "identify_actions",
    },
)

# Define edges
workflow.add_edge("identify_actions", "human_approval")
workflow.add_conditional_edges(
    "human_approval",
    lambda state: (
        "execute_approved_tools" if state.get("user_approved", False) else END
    ),
    {
        "execute_approved_tools": "execute_approved_tools",
        END: END,
    },
)
workflow.add_edge("execute_approved_tools", END)

# Compile the graph with checkpointing
memory = MemorySaver()
task_execution_graph = workflow.compile(checkpointer=memory)
