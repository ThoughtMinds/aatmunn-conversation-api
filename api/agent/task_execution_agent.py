from typing import Dict, TypedDict, Optional
from pydantic import BaseModel
from json import dumps
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from api import db, llm, tools, schema
from api.core.logging_config import logger
from langchain_core.tools import tool
from uuid import uuid4


class ToolCall(BaseModel):
    name: str
    parameters: Dict


class ChainedToolCall(BaseModel):
    name: str = ""
    parameters: Dict = {}


class AgentState(TypedDict):
    query: str
    chained: bool
    tool_calls: list
    tool_response: str
    final_response: str
    user_approved: bool
    requires_approval: bool
    actions_to_review: Optional[Dict]
    action_context: Optional[Dict]
    iter_count: Optional[int]


chat_model = llm.get_ollama_chat_model(cache=True)
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
chained_tool_chain = llm.create_chain_for_task(
    task="chained tool call",
    llm=chat_model,
    output_schema=schema.ChainedToolCall,
)

NO_RESPONSE = "We could not find any relevant information. Please rephrase the query"
FALLBACK_RESPONSE = "Task execution failed. Please rephrase or retry"
MAX_CHAIN_ITERATIONS = 10


def identify_actions(state: AgentState) -> AgentState:
    logger.critical("Performing normal Action Identification")
    response = llm_with_tools.invoke(state["query"])
    state["tool_calls"] = response.tool_calls or []

    if not state["tool_calls"]:
        logger.info("No tool call detected!")
        state["final_response"] = NO_RESPONSE
        return state

    # Prepare approval request and set interrupt
    state["requires_approval"] = True
    state["actions_to_review"] = {
        "question": "Please review and approve the following actions:",
        "actions": [
            {
                "tool": tool_call["name"],
                "parameters": tool_call["args"],
                "description": f"Execute {tool_call['name']} with parameters: {tool_call['args']}",
            }
            for tool_call in state["tool_calls"]
        ],
        "query": state["query"],
    }
    interrupt(state["actions_to_review"])  # This triggers the Interrupt event
    return state

def chained_identify_actions(state: AgentState) -> AgentState:
    iter_count = state.get("iter_count", 0)
    if iter_count >= MAX_CHAIN_ITERATIONS:
        state["final_response"] = state["tool_response"] or NO_RESPONSE
        return state

    if "action_context" not in state or not isinstance(state["action_context"], dict):
        state["action_context"] = {"previous_results": [], "already_executed": []}

    input_dict = {
        "query": state["query"],
        "context": dumps(state["action_context"]),
        "available_actions": TOOL_DESCRIPTION,
    }

    try:
        tool_call: ChainedToolCall = chained_tool_chain.invoke(input_dict)
    except Exception as e:
        logger.error(f"Chained identify failed: {e}")
        state["final_response"] = FALLBACK_RESPONSE
        return state

    if not tool_call.name:
        state["final_response"] = state["tool_response"] or NO_RESPONSE
        return state

    state["identified_actions"] = [
        {
            "name": tool_call.name,
            "args": tool_call.parameters,
            "id": str(uuid4()),
            "type": "tool_call",
        }
    ]

    # Prepare approval request and set interrupt
    state["requires_approval"] = True
    state["actions_to_review"] = {
        "question": "Please review and approve the following actions:",
        "actions": [
            {
                "tool": tc["name"],
                "parameters": tc["args"],
                "description": f"Execute {tc['name']} with parameters: {tc['args']}",
            }
            for tc in state["identified_actions"]
        ],
        "query": state["query"],
    }
    interrupt(state["actions_to_review"])
    return state


def execute_approved_tools(state: AgentState) -> AgentState:
    state["tool_response"] = state.get("tool_response", "")

    if not state.get("user_approved", False):
        # User rejected, end chain
        state["final_response"] = "Task execution cancelled by user."
        return state

    try:
        for tool_call in state.get("identified_actions", state.get("tool_calls", [])):
            name = tool_call["name"]
            args = tool_call.get("args") or tool_call.get("parameters")
            func = tool_dict.get(name)
            if func is None:
                raise Exception(f"Function not found: {name}")
            logger.info(f"Executing approved tool: {name} | Args: {args}")
            response = func.invoke(args)
            logger.info(f"Tool Response:\n{response}")
            response_string = dumps(response)
            tool_response_str = f"{name}: {response_string}"
            state["tool_response"] += f"{tool_response_str}\n"
            if state["chained"]:
                if "action_context" not in state or not isinstance(state["action_context"], dict):
                    state["action_context"] = {"previous_results": [], "already_executed": []}
                if "previous_results" not in state["action_context"]:
                    state["action_context"]["previous_results"] = []
                if "already_executed" not in state["action_context"]:
                    state["action_context"]["already_executed"] = []
                state["action_context"]["previous_results"].append(tool_response_str)
                state["action_context"]["already_executed"].append({"name": name, "parameters": args})
        if not state["chained"]:
            state["final_response"] = state["tool_response"]
    except Exception as e:
        logger.error(f"Tool execution failed due to: {e}")
        state["final_response"] = FALLBACK_RESPONSE
    finally:
        state["user_approved"] = False
        state["requires_approval"] = False
        state["actions_to_review"] = None

    return state


def tool_call_router(state: AgentState) -> str:
    if state["chained"]:
        return "chained_identify_actions"
    return "identify_actions"


workflow = StateGraph(AgentState)
workflow.add_node("identify_actions", identify_actions)
workflow.add_node("chained_identify_actions", chained_identify_actions)
workflow.add_node("execute_approved_tools", execute_approved_tools)

workflow.set_conditional_entry_point(
    tool_call_router,
    {
        "identify_actions": "identify_actions",
        "chained_identify_actions": "chained_identify_actions",
    },
)

workflow.add_edge("identify_actions", "execute_approved_tools")
workflow.add_edge("chained_identify_actions", "execute_approved_tools")

workflow.add_conditional_edges(
    "execute_approved_tools",
    lambda state: "chained_identify_actions" if state["chained"] and not state.get("final_response") else END,
    {
        "chained_identify_actions": "chained_identify_actions",
        END: END,
    },
)

memory = MemorySaver()
task_execution_graph = workflow.compile(checkpointer=memory)