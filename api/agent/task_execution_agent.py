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
    final_response: str
    user_approved: bool
    requires_approval: bool
    actions_to_review: Optional[Dict]
    execution_history: List[Dict]
    iter_count: Optional[int]


class ExecutionRecord(BaseModel):
    name: str
    parameters: Optional[Dict[str, Any]] = None
    result: str
    timestamp: float

    @validator("parameters", pre=True, always=True)
    def normalize_params(cls, v):
        if v is None:
            return {}
        if not isinstance(v, dict):
            raise ValueError("parameters must be a dict or None")
        return {k.lower(): v[k] for k in sorted(v)}


tool_list = [
    tools.aatumunn_api_integration.search_user_by_name,
    tools.aatumunn_api_integration.update_user,
]

# Create LLM with tools bound directly
single_llm = llm.get_chat_model(model_name=settings.TASK_EXECUTION_CHAT_MODEL)
llm_with_tools = single_llm.bind_tools(tool_list)

# Create tool dictionary for execution
tool_dict = {tool.name: tool for tool in tool_list}

NO_RESPONSE = "We could not find any relevant information. Please rephrase the query"
FALLBACK_RESPONSE = "Task execution failed. Please rephrase or retry"
MAX_CHAIN_ITERATIONS = 4

logger.info(f"[Task Execution Agent] Initialized with tools: {', '.join(tool_dict.keys())}")


def has_been_executed(name: str, parameters: Dict[str, Any], history: List[Dict]) -> bool:
    """Check if an action has already been executed based on history"""
    normalized_params = ExecutionRecord(name=name, parameters=parameters, result="", timestamp=0).parameters
    
    for record in history:
        if (record.get("name") == name and 
            record.get("parameters", {}) == normalized_params):
            return True
    return False


def execute_tools(state: AgentState) -> AgentState:
    """
    Single unified function for tool execution using LLM with bound tools.
    Handles both initial and chained tool execution flows.
    """
    logger.info(f"Executing tools for query: {state['query']}")
    
    # Initialize execution history if not present
    if "execution_history" not in state:
        state["execution_history"] = []
    state["requires_approval"] = True

    # Track iterations for both chained and non-chained scenarios
    iter_count = state.get("iter_count", 0) + 1
    state["iter_count"] = iter_count
    
    # Check iteration limit
    if iter_count > MAX_CHAIN_ITERATIONS:
        logger.warning(f"Max iterations ({MAX_CHAIN_ITERATIONS}) reached")
        if state["execution_history"]:
            # Create final response from execution history
            results = [f"{record['name']}: {record['result']}" for record in state["execution_history"]]
            state["final_response"] = "\n".join(results)
        else:
            state["final_response"] = "Maximum iteration limit reached."
        state["requires_approval"] = False
        return state
    
    # Build context-aware query for execution
    if state["execution_history"]:
        # Get the most recent execution result for immediate context
        latest_result = state["execution_history"][-1] if state["execution_history"] else None
        
        # Build comprehensive history summary
        history_summary = "\n".join([
            f"- {record['name']}({record['parameters']}): {record['result'][:150]}..." 
            for record in state["execution_history"][-5:]  # Last 5 results for context
        ])
        
        enhanced_query = f"""
Original Query: {state["query"]}

Execution History (most recent first):
{history_summary}

Latest Tool Result: {latest_result['result'][:200] if latest_result else 'None'}...

Based on the original query and the latest tool execution result above, determine what additional tools (if any) need to be called to complete the user's request. 

Important guidelines:
1. If the query is to update a user, first search for the user to get their current details before updating
2. Use the latest tool result to inform parameters for subsequent tool calls
3. If the user's request is already satisfied by previous results, don't call any tools
4. If you need to update user information, use the user ID from the search result
"""
        query_to_use = enhanced_query
    else:
        # For initial execution with no history
        enhanced_query = f"""
Original Query: {state["query"]}

This is the first tool execution for this query. Determine what tools need to be called to complete the user's request.

Important guidelines:
1. If the query is to update a user, first search for the user to get their current details before updating
2. Break down complex requests into sequential steps
"""
        query_to_use = enhanced_query
    
    # Get tool calls from LLM with bound tools
    try:
        logger.info(f"Invoking LLM with query: {query_to_use[:200]}...")
        response = llm_with_tools.invoke(query_to_use)
        tool_calls = response.tool_calls or []

        print("TOOL CALLS ::::::::", tool_calls)
        
        # Remove duplicates and filter already executed
        unique_tool_calls = []
        for tool_call in tool_calls:
            name = tool_call.get("name", "")
            args = tool_call.get("args", {})
            
            # Check if already executed
            if not has_been_executed(name, args, state["execution_history"]):
                unique_tool_calls.append(tool_call)
            else:
                logger.info(f"Skipping already executed tool: {name}")
        
        logger.info(f"Found {len(unique_tool_calls)} unique tool calls to execute")
        
    except Exception as e:
        logger.error(f"Failed to get tool calls from LLM: {e}")
        state["final_response"] = FALLBACK_RESPONSE
        state["requires_approval"] = False
        return state
    
    # Handle no tool calls - check if request is satisfied
    if not unique_tool_calls:
        if state["execution_history"]:
            # Create final response from execution history
            results = [f"{record['name']}: {record['result']}" for record in state["execution_history"]]
            state["final_response"] = "\n".join(results)
            logger.info("No more tool calls needed, request appears to be satisfied")
        else:
            state["final_response"] = NO_RESPONSE
            logger.info("No tool calls identified for the query")
        
        state["requires_approval"] = False
        return state
    
    # Check if user approval is needed
    if not state.get("user_approved", False) and state.get("requires_approval", True):
        # Prepare approval request
        state["actions_to_review"] = {
            "question": "Please review and approve the following actions:",
            "actions": [
                {
                    "tool": tool_call["name"],
                    "parameters": tool_call["args"],
                    "description": f"Execute {tool_call['name']} with parameters: {tool_call['args']}",
                }
                for tool_call in unique_tool_calls
            ],
            "query": state["query"],
        }
        
        logger.info("Requesting user approval for tool execution")
        interrupt(state["actions_to_review"])
        return state
    
    # Execute approved tools - ONE AT A TIME
    try:
        # Execute only the first tool, then return to get fresh tool calls
        if unique_tool_calls:
            tool_call = unique_tool_calls[0]  # Execute only the first tool
            name = tool_call["name"]
            args = tool_call["args"]
            
            # Get tool function
            func = tool_dict.get(name)
            if func is None:
                logger.error(f"Tool not found: {name}")
                state["final_response"] = f"Tool {name} not found"
                state["requires_approval"] = False
                return state
            
            # Execute tool
            logger.info(f"Executing tool: {name} with args: {args}")
            result = func.invoke(args)
            
            # Format result
            if isinstance(result, dict):
                result_str = dumps(result, indent=2)
            else:
                result_str = str(result)
            
            # Record execution
            execution_record = {
                "name": name,
                "parameters": args,
                "result": result_str,
                "timestamp": time.time()
            }
            
            state["execution_history"].append(execution_record)
            
            logger.info(f"Tool {name} executed successfully. Result: {result_str[:200]}...")
            
            # For non-chained execution, check if we need more tools
            if not state["chained"]:
                # After executing one tool, check if we need more based on the result
                # This will be handled in the next iteration
                state["requires_approval"] = True
                state["user_approved"] = False
            else:
                # For chained execution, continue to next iteration to get fresh tool calls
                state["requires_approval"] = True
                state["user_approved"] = False
        
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        state["final_response"] = FALLBACK_RESPONSE
        state["requires_approval"] = False
    
    return state


def should_continue(state: AgentState) -> str:
    """Determine if workflow should continue or end"""
    
    # If we have a final response, we're done
    if state.get("final_response"):
        return END
    
    # Check iteration limits for safety
    iter_count = state.get("iter_count", 0)
    if iter_count > MAX_CHAIN_ITERATIONS:
        logger.warning(f"Max iterations ({MAX_CHAIN_ITERATIONS}) reached, ending workflow")
        return END
    
    # For chained execution, continue until explicitly finished
    if state["chained"]:
        return "execute_tools"
    
    # For non-chained execution, continue if we have execution history but no final response
    # This allows non-chained flows to also benefit from iterative tool calling
    if state.get("execution_history") and not state.get("final_response"):
        # Continue for a few iterations to allow tool results to inform next tool calls
        if iter_count < 3:  # Allow up to 3 iterations for non-chained
            return "execute_tools"
    
    return END


# Create simplified workflow with single function
workflow = StateGraph(AgentState)
workflow.add_node("execute_tools", execute_tools)

workflow.set_entry_point("execute_tools")

workflow.add_conditional_edges(
    "execute_tools",
    should_continue,
    {
        "execute_tools": "execute_tools",
        END: END,
    },
)

memory = MemorySaver()
task_execution_graph = workflow.compile(checkpointer=memory)
