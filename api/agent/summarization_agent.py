from typing import AsyncGenerator, Dict, TypedDict, Union
from pydantic import BaseModel
from json import dumps, loads
from langgraph.graph import StateGraph, END
from api import db, llm, schema, tools
from api.core.logging_config import logger
from sqlmodel import Session


class ToolCall(BaseModel):
    name: str
    parameters: Dict


# Define the state for the LangGraph
class AgentState(TypedDict):
    """
    Represents the state of the summarization agent.

    Attributes:
        query (str): The user's query.
        chained (bool): Whether to use chained tool calls.
        tool_calls (list): A list of tool calls to be executed.
        tool_response (str): The response from the tool execution.
        summarized_response (str): The summarized response from the language model.
        is_moderated (bool): Whether the content has been moderated.
        final_response (str): The final response to be returned to the user.
    """

    query: str
    chained: bool
    tool_calls: list
    tool_response: str
    summarized_response: str
    is_moderated: bool
    final_response: str


# Initialize tools and models
chat_model = llm.get_ollama_chat_model()
cache_chat_model = llm.get_ollama_chat_model(cache=True)

tool_list = [
    tools.summarization_api.get_issues,
    tools.summarization_api.get_navigation_points,
    tools.summarization_api.get_users,
    tools.summarization_api.get_navigation_points,
    tools.summarization_api.get_issues,
    tools.summarization_api.get_users,
    tools.summarization_api.get_roles,
    tools.summarization_api.get_organization,
    tools.summarization_api.get_product_models,
    tools.summarization_api.get_historical_data,
    tools.summarization_api.get_form_execution_summary,
    tools.summarization_api.get_areas_needing_attention,
    tools.summarization_api.get_user_statuses,
]

TOOL_DESCRIPTION = tools.render_text_description(tool_list)

tool_dict = {
    "get_issues": tools.summarization_api.get_issues,
    "get_navigation_points": tools.summarization_api.get_navigation_points,
    "get_users": tools.summarization_api.get_users,
    "get_roles": tools.summarization_api.get_roles,
    "get_organization": tools.summarization_api.get_organization,
    "get_product_models": tools.summarization_api.get_product_models,
    "get_historical_data": tools.summarization_api.get_historical_data,
    "get_form_execution_summary": tools.summarization_api.get_form_execution_summary,
    "get_areas_needing_attention": tools.summarization_api.get_areas_needing_attention,
    "get_user_statuses": tools.summarization_api.get_user_statuses,
}


logger.info(f"[Summarization Tools] {', '.join(tool_dict.keys())}")
llm_with_tools = chat_model.bind_tools(tool_list)
summarize_chain = llm.create_chain_for_task(task="summarization", llm=cache_chat_model)
chained_tool_chain = llm.create_chain_for_task(
    task="chained tool call",
    llm=chat_model,
    output_schema=schema.ChainedToolCall,
)
content_moderation_chain = llm.create_chain_for_task(
    task="content moderation",
    llm=cache_chat_model,
    output_schema=schema.ContentValidation,
)

NO_SUMMARY_RESPONSE = (
    "We could not find any relevant information. Please rephrase the query"
)
FALLBACK_SUMMARY_RESPONSE = (
    "Summary flagged by content policy. Please rephrase or retry"
)


# Node to invoke tools based on the query
# If 'chained' = False
def invoke_tools(state: AgentState) -> AgentState:
    session = Session(db.engine)
    response = llm_with_tools.invoke(state["query"])
    state["tool_calls"] = response.tool_calls
    state["tool_response"] = ""

    if not state["tool_calls"]:
        logger.info("No tool call detected!")
        logger.error(f"NoToolCall: {response.content}")
        state["final_response"] = NO_SUMMARY_RESPONSE
        return state

    logger.info(f"Found {len(state['tool_calls'])} Tool Calls")
    try:
        for tool_call in state["tool_calls"]:
            name, args, _tool_id = tool_call["name"], tool_call["args"], tool_call["id"]
            func = tool_dict.get(name)
            if func is None:
                raise Exception(f"Function not found: {name}")
            logger.info(f"Tool: {name} | Args: {args} | ID: {_tool_id}")
            args["session"] = session
            response = func.invoke(args)
            logger.info(f"Tool Response: {response}")
            if response == None:
                response_string = "No tools were made due to connection error"
            else:
                response_string = dumps(response)
            state["tool_response"] += f"{name}: {response_string}"
    except Exception as e:
        logger.error(f"Tool invocation failed due to: {e}")
        state["final_response"] = response.content
    finally:
        session.close()

    return state


# Chained Tool Calling Node
# If 'chained' is True
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
            logger.info(
                {
                    "query": user_query,
                    "context": dumps(action_context),
                }
            )
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
        state["final_response"] = FALLBACK_SUMMARY_RESPONSE
    finally:
        session.close()

    if not state["tool_response"]:
        state["final_response"] = NO_SUMMARY_RESPONSE

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


# Node for content moderation
def moderate_content(state: AgentState) -> AgentState:
    if state["final_response"]:
        return state  # Skip if final_response is already set

    logger.info("Validating Content")
    content_validity = content_moderation_chain.invoke(
        {"query": state["query"], "summary": state["summarized_response"]}
    )
    state["is_moderated"] = not content_validity["content_valid"]

    logger.info(f"Content Moderation: {state['is_moderated']}")
    if state["is_moderated"]:
        logger.critical(f"Flagged summary: {state['summarized_response']}")

    state["final_response"] = (
        state["summarized_response"]
        if content_validity["content_valid"]
        else FALLBACK_SUMMARY_RESPONSE
    )
    return state


# Router function to decide between invoke_tools and chained_invoke_tools
def tool_call_router(state: AgentState) -> str:
    is_chained = state["chained"]
    logger.info(f"Chained Tool Call: {is_chained}")

    if is_chained:
        return "chained_invoke_tools"
    else:
        return "invoke_tools"


workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("invoke_tools", invoke_tools)
workflow.add_node("chained_invoke_tools", chained_invoke_tools)
workflow.add_node("summarize_response", summarize_response)
workflow.add_node("moderate_content", moderate_content)

# Define conditional branching based on 'chained'
workflow.set_conditional_entry_point(
    tool_call_router,
    {
        "invoke_tools": "invoke_tools",
        "chained_invoke_tools": "chained_invoke_tools",
    },
)

# Define edges
workflow.add_edge("invoke_tools", "summarize_response")
workflow.add_edge("chained_invoke_tools", "summarize_response")
workflow.add_edge("summarize_response", "moderate_content")
workflow.add_edge("moderate_content", END)

summarization_graph = workflow.compile()


async def get_summarized_response(query: str, chained: bool = True) -> tuple[str, bool]:
    """
    Generates a summarized response for a given query using a LangGraph workflow.

    Args:
        query (str): The user's query for summarization.
        chained (bool): Determines whether to use invoke_tools/chained_invoke_tools.

    Returns:
        tuple[str, bool]: The summarized response string and moderation status
    """
    logger.info("Generating summary")
    initial_state = {
        "query": query,
        "chained": chained,
        "tool_calls": [],
        "tool_response": "",
        "summarized_response": "",
        "is_moderated": False,
        "final_response": "",
    }

    result = await summarization_graph.ainvoke(initial_state)
    return result["final_response"], result["is_moderated"]


async def get_streaming_summarized_response(
    query: str, chained: bool = True
) -> AsyncGenerator[Dict, None]:
    """
    Generates a summarized response for a given query using a LangGraph workflow.

    Args:
        query (str): The user's query for summarization.
        chained (bool): Determines whether to use invoke_tools/chained_invoke_tools.

    Yields:
        Dict: The agent state at each step of the workflow.
    """
    logger.info("Generating streaming summary")
    initial_state = {
        "query": query,
        "chained": chained,
        "tool_calls": [],
        "tool_response": "",
        "summarized_response": "",
        "is_moderated": False,
        "final_response": "",
    }

    try:
        async for event in summarization_graph.astream(initial_state):
            for value in event.values():
                yield value
    except Exception as e:
        logger.error(f"Error in streaming summarization: {e}")
        yield {"error": str(e)}
