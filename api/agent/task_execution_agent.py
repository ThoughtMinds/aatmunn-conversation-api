import time
from typing import Dict, TypedDict, Optional, List, Any
from pydantic import BaseModel, validator
from json import dumps
from uuid import uuid4
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
from api import llm, tools
from api.core.logging_config import logger

from api.core.config import settings


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


class ExecutedAction(BaseModel):
    name: str
    parameters: Optional[Dict[str, Any]] = None
    timestamp: float  # Unix timestamp

    @validator("parameters", pre=True, always=True)
    def normalize_params(cls, v):
        # If parameters is None, convert to empty dict
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError("parameters must be a dict or None")
        # Normalize keys to lowercase and sort keys for consistent comparison
        return {k.lower(): v[k] for k in sorted(v)}


class ActionContext(BaseModel):
    previous_results: List[str] = []
    already_executed: List[ExecutedAction] = []

    def add_executed_action(self, name: str, parameters: Dict[str, Any]):
        new_action = ExecutedAction(name=name, parameters=parameters, timestamp=time.time())
        if not any(
            (ea.name == new_action.name and ea.parameters == new_action.parameters)
            for ea in self.already_executed
        ):
            self.already_executed.append(new_action)

    def add_previous_result(self, result: str):
        self.previous_results.append(result)


tool_list = [
    # tools.aatumunn_api_integration.list_users,
    tools.aatumunn_api_integration.search_user_by_name,
    tools.aatumunn_api_integration.update_user,
    # tools.aatumunn_api_integration.get_user_by_id,
]




TOOL_DESCRIPTION = tools.render_text_description(tool_list)

logger.warning(TOOL_DESCRIPTION)

tool_dict = {tool.name: tool for tool in tool_list}
logger.info(f"[Task Execution Tools] {', '.join(tool_dict.keys())}")

# Use a single LLM for both tool execution and chained tool calls
single_llm = llm.get_chat_model(model_name=settings.TASK_EXECUTION_CHAT_MODEL)
llm_with_tools = single_llm.bind_tools(tool_list)

NO_RESPONSE = "We could not find any relevant information. Please rephrase the query"
FALLBACK_RESPONSE = "Task execution failed. Please rephrase or retry"
MAX_CHAIN_ITERATIONS = 4


def get_or_init_action_context(state: AgentState) -> ActionContext:
    """
    Get existing action_context from state or initialize a new one.
    Ensures consistent action context handling across all functions.
    """
    if "action_context" not in state or not isinstance(state["action_context"], dict):
        return ActionContext()
    else:
        try:
            return ActionContext.parse_obj(state["action_context"])
        except Exception as e:
            logger.error(f"Failed to parse action_context: {e}")
            return ActionContext()


def identify_actions(state: AgentState) -> AgentState:
    logger.critical(
        f"Performing normal Action Identification for query: {state['query']}"
    )
    response = llm_with_tools.invoke(state["query"])
    state["tool_calls"] = response.tool_calls or []

    if not state["tool_calls"]:
        logger.info("No tool call detected!")
        state["final_response"] = NO_RESPONSE
        state["requires_approval"] = False
        return state

    # Initialize or parse action_context for duplicate detection
    action_context = get_or_init_action_context(state)

    # Filter out already executed tools
    filtered_tool_calls = []
    for tool_call in state["tool_calls"]:
        # Check for duplicate action
        action_key = ExecutedAction(name=tool_call["name"], parameters=tool_call["args"], timestamp=time.time())
        if any(
            (ea.name == action_key.name and ea.parameters == action_key.parameters)
            for ea in action_context.already_executed
        ):
            logger.warning(
                f"Skipping duplicate action {tool_call['name']} with parameters {tool_call['args']} - already executed"
            )
            continue
        filtered_tool_calls.append(tool_call)
    
    state["tool_calls"] = filtered_tool_calls
    
    if not state["tool_calls"]:
        logger.info("All identified tools have already been executed!")
        state["final_response"] = state.get("tool_response") or "All requested actions have already been completed."
        state["requires_approval"] = False
        return state

    # Update action_context in state for persistence
    state["action_context"] = action_context.dict()

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

    if iter_count > MAX_CHAIN_ITERATIONS:
        logger.warning(f"Max iterations ({MAX_CHAIN_ITERATIONS}) reached")
        state["final_response"] = state.get("tool_response") or NO_RESPONSE
        state["requires_approval"] = False
        return state

    # Initialize or parse action_context with validation
    action_context = get_or_init_action_context(state)

    # Prepare enhanced query with context for the LLM
    context_info = f"""
Previous Results: {action_context.previous_results}
Already Executed Actions: {[{"name": a.name, "parameters": a.parameters} for a in action_context.already_executed]}

Original Query: {state["query"]}

Based on the previous results and already executed actions, determine the next tool to call to complete the user's request. If no further action is needed, don't call any tools.
"""
    
    logger.debug(f"Enhanced query for chained_identify_actions: {context_info}")

    try:
        response = llm_with_tools.invoke(context_info)
        tool_calls = response.tool_calls or []
        logger.debug(f"LLM tool calls response: {tool_calls}")
    except Exception as e:
        logger.error(f"Chained identify failed: {e}")
        state["final_response"] = FALLBACK_RESPONSE
        state["requires_approval"] = False
        return state

    if not tool_calls:
        logger.info("No further chained tool calls identified")
        state["final_response"] = state.get("tool_response") or NO_RESPONSE
        state["requires_approval"] = False
        return state

    # Use the first tool call for chained execution (single tool at a time)
    tool_call = tool_calls[0]
    
    # Normalize action key for duplicate detection
    action_key = ExecutedAction(name=tool_call["name"], parameters=tool_call["args"], timestamp=time.time())

    # Check for duplicate action
    if any(
        (ea.name == action_key.name and ea.parameters == action_key.parameters)
        for ea in action_context.already_executed
    ):
        logger.warning(
            f"Action {tool_call['name']} with parameters {tool_call['args']} already executed, continuing to identify next actions"
        )
        # Instead of exiting, continue to the next iteration to identify other actions
        state["action_context"] = action_context.model_dump()
        return state

    # Prepare identified actions for approval
    state["identified_actions"] = [
        {
            "name": tool_call["name"],
            "args": tool_call["args"],
            "id": tool_call["id"],
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
    state["requires_approval"] = True
    # Update action_context in state as dict for persistence
    state["action_context"] = action_context.dict()
    return state

def execute_approved_tools(state: AgentState) -> AgentState:
    logger.info(
        f"Executing tools with state: user_approved={state.get('user_approved')}, chained={state['chained']}, tool_calls={state.get('tool_calls')}, identified_actions={state.get('identified_actions')}"
    )
    state["tool_response"] = state.get("tool_response", "")

    if not state.get("user_approved", False):
        logger.warning("Execution cancelled due to lack of user approval")
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

        # Parse or initialize action_context
        action_context = get_or_init_action_context(state)

        for tool_call in tool_calls_to_execute:
            name = tool_call["name"]
            args = tool_call.get("args") or tool_call.get("parameters")
            
            # Final duplicate check before execution
            action_key = ExecutedAction(name=name, parameters=args, timestamp=time.time())
            if any(
                (ea.name == action_key.name and ea.parameters == action_key.parameters)
                for ea in action_context.already_executed
            ):
                logger.warning(
                    f"Skipping execution of {name} with parameters {args} - already executed"
                )
                # Add a note to the tool response about the skipped execution
                skip_message = f"{name}: Skipped - already executed with same parameters\n"
                state["tool_response"] += skip_message
                continue
            
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

            # Update action_context with results and executed actions for both chained and non-chained
            action_context.add_previous_result(tool_response_str)
            action_context.add_executed_action(name, args)

        # Update action_context in state as dict for persistence
        state["action_context"] = action_context.dict()

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
