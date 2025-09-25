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
from api.core.config import settings


class ToolCall(BaseModel):
    name: str
    parameters: Dict


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
    identified_actions: list


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
    result = tools.list_tool_names(tool_list)
    logger.info(f"list_tool_names result: {result}")
    return result


tool_list.append(list_tool_names)
TOOL_DESCRIPTION = tools.render_text_description(tool_list)
tool_dict = {tool.name: tool for tool in tool_list}
logger.info(f"[Task Execution Tools] {', '.join(tool_dict.keys())}")

tool_llm, chained_llm = llm.get_chat_model(
    model_name=settings.TASK_EXECUTION_CHAT_MODEL
), llm.get_chat_model(model_name=settings.CHAINED_TOOL_CALL_CHAT_MODEL)
llm_with_tools = tool_llm.bind_tools(tool_list)
chained_tool_chain = llm.create_chain_for_task(
    task="chained tool call",
    llm=chained_llm,
    output_schema=schema.ChainedToolCall,
)

NO_RESPONSE = "We could not find any relevant information. Please rephrase the query"
FALLBACK_RESPONSE = "Task execution failed. Please rephrase or retry"
MAX_CHAIN_ITERATIONS = 4


def identify_actions(state: AgentState) -> AgentState:
    logger.info(
        f"Performing normal Action Identification for query: {state['query']}",
        extra={"bold": True},
    )
    response = llm_with_tools.invoke(state["query"])
    state["tool_calls"] = response.tool_calls or []

    if not state["tool_calls"]:
        logger.info("No tool call detected!")
        state["final_response"] = NO_RESPONSE
        state["requires_approval"] = False
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
    logger.info(f"Prepared actions for approval: {state['actions_to_review']}")
    interrupt(state["actions_to_review"])
    return state


def chained_identify_actions(state: AgentState) -> AgentState:
    logger.info(
        f"Entering chained_identify_actions for query: {state['query']}, iter_count: {state.get('iter_count', 0)}"
    )
    iter_count = state.get("iter_count", 0) + 1
    state["iter_count"] = iter_count

    if iter_count >= MAX_CHAIN_ITERATIONS:
        logger.warning(
            f"Max iterations ({MAX_CHAIN_ITERATIONS}) reached", extra={"bold": True}
        )
        state["final_response"] = state["tool_response"] or NO_RESPONSE
        state["requires_approval"] = False
        return state

    if "action_context" not in state or not isinstance(state["action_context"], dict):
        state["action_context"] = {"previous_results": [], "already_executed": []}

    # Filter out already executed actions
    already_executed = state["action_context"].get("already_executed", [])
    logger.info(f"Already executed actions: {already_executed}")

    input_dict = {
        "query": state["query"],
        "context": dumps(state["action_context"]),
        "available_actions": TOOL_DESCRIPTION,
    }
    logger.debug(f"LLM input for chained_identify_actions: {input_dict}")

    try:
        tool_call: schema.ChainedToolCall = chained_tool_chain.invoke(input_dict)
        logger.debug(f"LLM output: {tool_call}")
    except Exception as e:
        logger.error(f"Chained identify failed: {e}")
        state["final_response"] = FALLBACK_RESPONSE
        state["requires_approval"] = False
        return state

    if not tool_call.name:
        logger.info("No further chained tool calls identified")
        state["final_response"] = state["tool_response"] or NO_RESPONSE
        state["requires_approval"] = False
        return state

    # Check if the identified action was already executed
    action_key = {"name": tool_call.name, "parameters": tool_call.parameters}
    if action_key in already_executed:
        logger.info(
            f"Action {tool_call.name} with parameters {tool_call.parameters} already executed, skipping",
            extra={"bold": True},
        )
        state["final_response"] = state["tool_response"] or NO_RESPONSE
        state["requires_approval"] = False
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
    logger.info(f"Prepared chained actions for approval: {state['actions_to_review']}")
    interrupt(state["actions_to_review"])
    return state


def execute_approved_tools(state: AgentState) -> AgentState:
    logger.info(
        f"Executing tools with state: user_approved={state.get('user_approved')}, chained={state['chained']}, tool_calls={state.get('tool_calls')}, identified_actions={state.get('identified_actions')}"
    )
    state["tool_response"] = state.get("tool_response", "")

    if not state.get("user_approved", False):
        logger.critical(
            "Execution cancelled due to lack of user approval", extra={"bold": True}
        )
        state["final_response"] = "Task execution cancelled by user."
        state["requires_approval"] = False
        return state

    try:
        tool_calls_to_execute = (
            state.get("tool_calls", [])
            if not state["chained"]
            else state.get("identified_actions", [])
        )
        if not tool_calls_to_execute:
            logger.info("No tools to execute")
            state["final_response"] = NO_RESPONSE
            state["requires_approval"] = False
            return state

        for tool_call in tool_calls_to_execute:
            name = tool_call["name"]
            args = tool_call.get("args") or tool_call.get("parameters")
            func = tool_dict.get(name)
            if func is None:
                raise Exception(f"Function not found: {name}")
            logger.info(f"Executing approved tool: {name} | Args: {args}")
            response = func.invoke(args)
            logger.info(f"Tool Response:\n{response}")
            response_string = (
                dumps(response) if isinstance(response, dict) else str(response)
            )
            tool_response_str = f"{name}: {response_string}\n"
            state["tool_response"] += tool_response_str

            if state["chained"]:
                if "action_context" not in state or not isinstance(
                    state["action_context"], dict
                ):
                    state["action_context"] = {
                        "previous_results": [],
                        "already_executed": [],
                    }
                if "previous_results" not in state["action_context"]:
                    state["action_context"]["previous_results"] = []
                if "already_executed" not in state["action_context"]:
                    state["action_context"]["already_executed"] = []
                state["action_context"]["previous_results"].append(tool_response_str)
                state["action_context"]["already_executed"].append(
                    {"name": name, "parameters": args}
                )

        # Set final_response for non-chained calls
        if not state["chained"]:
            state["final_response"] = state["tool_response"] or NO_RESPONSE
            state["requires_approval"] = False
            logger.info(
                f"Set final_response for non-chained call: {state['final_response'][:100]}..."
            )

    except Exception as e:
        logger.error(f"Tool execution failed due to: {e}")
        state["final_response"] = FALLBACK_RESPONSE
        state["requires_approval"] = False

    finally:
        # Only clear tool_calls and identified_actions if workflow is complete
        if state.get("final_response"):
            state["user_approved"] = False
            state["requires_approval"] = False
            state["actions_to_review"] = None
            state["tool_calls"] = []
            state["identified_actions"] = []
        logger.info(f"State after execution: {state}")

    return state


def tool_call_router(state: AgentState) -> str:
    logger.info(
        f"Routing with state: chained={state['chained']}, final_response={bool(state.get('final_response'))}, iter_count={state.get('iter_count', 0)}, tool_calls={state.get('tool_calls')}, identified_actions={state.get('identified_actions')}"
    )
    if state.get("final_response") or (
        not state.get("requires_approval", False)
        and not state.get("tool_calls")
        and not state.get("identified_actions")
        and state.get("iter_count", 0) > 0
    ):
        logger.info("Routing to END due to final_response or no pending actions")
        return END
    if state["chained"]:
        logger.info("Routing to chained_identify_actions")
        return "chained_identify_actions"
    logger.info("Routing to identify_actions")
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
        END: END,
    },
)

workflow.add_edge("identify_actions", "execute_approved_tools")
workflow.add_edge("chained_identify_actions", "execute_approved_tools")

workflow.add_conditional_edges(
    "execute_approved_tools",
    lambda state: (
        "chained_identify_actions"
        if state["chained"]
        and not state.get("final_response")
        and state.get("iter_count", 0) < MAX_CHAIN_ITERATIONS
        else END
    ),
    {
        "chained_identify_actions": "chained_identify_actions",
        END: END,
    },
)

memory = MemorySaver()
task_execution_graph = workflow.compile(checkpointer=memory)
