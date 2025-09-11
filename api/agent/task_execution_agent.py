from typing import AsyncGenerator, Dict, TypedDict, Union, List, Literal, Optional
from pydantic import BaseModel
from json import dumps, loads
from langgraph.graph import StateGraph, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from api import db, llm, schema, tools
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
    summarized_response: str
    final_response: str
    user_approved: bool
    requires_approval: bool
    actions_to_review: Optional[Dict]


# Initialize tools and models
chat_model = llm.get_ollama_chat_model()
tool_list = [
    tools.task_execution_api.search_users,
    tools.task_execution_api.update_user,
    tools.task_execution_api.get_roles,
    tools.task_execution_api.get_entities,
    tools.task_execution_api.get_modules,
    tools.task_execution_api.get_navigation_points,
    tools.task_execution_api.get_user_by_id,
    tools.task_execution_api.get_roles_by_user_id,
    tools.task_execution_api.get_role_by_id,
    tools.task_execution_api.get_product_models,
    tools.task_execution_api.get_templates_by_module_id,
    tools.task_execution_api.get_form_execution_summary,
    tools.task_execution_api.get_areas_needing_attention,
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

tool_dict = {
    "search_users": tools.task_execution_api.search_users,
    "update_user": tools.task_execution_api.update_user,
    "get_roles": tools.task_execution_api.get_roles,
    "get_entities": tools.task_execution_api.get_entities,
    "get_modules": tools.task_execution_api.get_modules,
    "get_navigation_points": tools.task_execution_api.get_navigation_points,
    "get_user_by_id": tools.task_execution_api.get_user_by_id,
    "get_roles_by_user_id": tools.task_execution_api.get_roles_by_user_id,
    "get_role_by_id": tools.task_execution_api.get_role_by_id,
    "get_product_models": tools.task_execution_api.get_product_models,
    "get_templates_by_module_id": tools.task_execution_api.get_templates_by_module_id,
    "get_form_execution_summary": tools.task_execution_api.get_form_execution_summary,
    "get_areas_needing_attention": tools.task_execution_api.get_areas_needing_attention,
    "list_tool_names": list_tool_names,
}

logger.info(f"[Task Execution Tools] {', '.join(tool_dict.keys())}")

llm_with_tools = chat_model.bind_tools(tool_list)
summarize_chain = llm.create_chain_for_task(task="summarization", llm=chat_model)
chained_tool_chain = llm.create_chain_for_task(
    task="chained tool call",
    llm=chat_model,
    output_schema=schema.ChainedToolCall,
)

NO_RESPONSE = "We could not find any relevant information. Please rephrase the query"
FALLBACK_RESPONSE = "Task execution failed. Please rephrase or retry"


# Node to identify actions without executing them
def identify_actions(state: AgentState) -> AgentState:
    session = Session(db.engine)
    response = llm_with_tools.invoke(state["query"])
    state["identified_actions"] = response.tool_calls or []

    if not state["identified_actions"]:
        logger.info("No tool call detected!")
        logger.error(f"NoToolCall: {response.content}")
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
    session.close()
    return state


# Human approval node
def human_approval(
    state: AgentState,
) -> Command[Literal["execute_approved_tools", "user_rejected"]]:
    if state.get("requires_approval", False) and state.get("actions_to_review"):
        logger.warning("Triggering Interrupt for approval")
        is_approved = interrupt(state["actions_to_review"])
        if is_approved:
            state["user_approved"] = True
            state["requires_approval"] = False
            return Command(goto="execute_approved_tools")
        else:
            state["user_approved"] = False
            state["requires_approval"] = False
            return Command(goto="user_rejected")
    return Command(goto="execute_approved_tools")  # Fallback if no approval needed


# Node for user rejection
def user_rejected(state: AgentState) -> AgentState:
    state["final_response"] = "Task execution cancelled by user."
    state["requires_approval"] = False
    state["actions_to_review"] = None
    return state


# Node to execute approved tools
def execute_approved_tools(state: AgentState) -> AgentState:
    session = Session(db.engine)
    state["tool_response"] = ""

    try:
        for tool_call in state["identified_actions"]:
            name, args, _tool_id = tool_call["name"], tool_call["args"], tool_call["id"]
            func = tool_dict.get(name)
            if func is None:
                raise Exception(f"Function not found: {name}")
            logger.info(f"Executing approved tool: {name} | Args: {args}")
            args["session"] = session
            response = func.invoke(args)
            logger.info(f"Tool Response: {response}")
            response_string = dumps(response)
            state["tool_response"] += f"{name}: {response_string}"
    except Exception as e:
        logger.error(f"Tool execution failed due to: {e}")
        state["final_response"] = FALLBACK_RESPONSE
    finally:
        session.close()

    return state


# Chained Tool Calling Node
def chained_invoke_tools(state: AgentState) -> AgentState:
    session = Session(db.engine)
    action_context = {"previous_results": [], "already_executed": []}
    user_query = state["query"]

    state["tool_response"] = ""

    try:
        iter_cnt = 0
        while True:
            if iter_cnt == 3:
                break
            iter_cnt += 1
            logger.info({"query": user_query, "context": dumps(action_context)})
            try:
                tool_call: schema.ChainedToolCall = chained_tool_chain.invoke(
                    {
                        "query": user_query,
                        "context": dumps(action_context),
                        "available_actions": TOOL_DESCRIPTION,
                    }
                )
                logger.info(f"Chained Response: {tool_call}")
            except Exception as e:
                logger.error(f"Invalid JSON in chained response: {e}")
                break

            if tool_call == {}:
                break

            name = tool_call.name
            args = tool_call.parameters.copy()
            func = tool_dict.get(name)
            if func is None:
                raise Exception(f"Function not found: {name}")
            logger.info(f"Tool: {name} | Args: {args}")
            args["session"] = session
            tool_response = func.invoke(args)
            logger.info(f"Tool Response: {tool_response}")
            response_string = dumps(tool_response)
            tool_response_str = f"{name}: {response_string}"

            action_context["already_executed"].append(tool_call.model_dump())
            action_context["previous_results"].append(tool_response_str)

            state["tool_response"] += tool_response_str + "\n"
    except Exception as e:
        logger.error(f"Chained tool invocation failed due to: {e}")
        state["final_response"] = FALLBACK_RESPONSE
    finally:
        session.close()

    if not state["tool_response"]:
        state["final_response"] = NO_RESPONSE

    return state


# Node to summarize the tool response
def summarize_response(state: AgentState) -> AgentState:
    if state["final_response"]:
        return state

    response = summarize_chain.invoke(
        {"query": state["query"], "tool_response": state["tool_response"]}
    )
    state["summarized_response"] = response.content
    state["final_response"] = response.content
    logger.info(f"Summarized Response: {state['summarized_response']}")
    return state


# Router function
def tool_call_router(state: AgentState) -> str:
    is_chained = state["chained"]
    logger.critical(f"Chained Tool Call: {is_chained}")
    return "chained_invoke_tools" if is_chained else "identify_actions"


# Define the workflow
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("identify_actions", identify_actions)
workflow.add_node("human_approval", human_approval)
workflow.add_node("execute_approved_tools", execute_approved_tools)
workflow.add_node("user_rejected", user_rejected)
workflow.add_node("chained_invoke_tools", chained_invoke_tools)
workflow.add_node("summarize_response", summarize_response)

# Set conditional entry point
workflow.set_conditional_entry_point(
    tool_call_router,
    {
        "identify_actions": "identify_actions",
        "chained_invoke_tools": "chained_invoke_tools",
    },
)

# Define edges
workflow.add_edge("identify_actions", "human_approval")
workflow.add_conditional_edges(
    "human_approval",
    lambda state: "execute_approved_tools" if state.get("user_approved", False) else "user_rejected",
    {
        "execute_approved_tools": "execute_approved_tools",
        "user_rejected": "user_rejected",
    },
)
workflow.add_edge("execute_approved_tools", "summarize_response")
workflow.add_edge("chained_invoke_tools", "summarize_response")
workflow.add_edge("user_rejected", END)
workflow.add_edge("summarize_response", END)

# Compile the graph with checkpointing
memory = MemorySaver()
task_execution_graph = workflow.compile(checkpointer=memory)
# Chained, summarize
