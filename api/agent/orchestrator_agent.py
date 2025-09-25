from typing_extensions import TypedDict
from langgraph.graph import START, StateGraph
from api import llm, schema
from typing import Optional
from api.core.logging_config import logger
from api.core.config import settings


chat_model = llm.get_chat_model(model_name=settings.ORCHESTRATOR_CHAT_MODEL, cache=True)
orchestrator_chain = llm.create_chain_for_task(task="orchestration", llm=chat_model)


class State(TypedDict):
    """
    Represents the state of the graph.

    Attributes:
        query (str): The question being asked.
        category (str): The identified category of the query.
    """

    query: str
    category: str


def identify_intent(state: State) -> State:
    """
    Identifies the intent of the query using the LLM.

    Args:
        state (State): The current state containing the query.

    Returns:
        State: Updated state with the identified category.
    """
    try:
        response = orchestrator_chain.invoke({"query": state["query"]})
        category = response.content.lower()
        return {"category": category}
    except Exception as e:
        print(f"Failed to get Orchestration due to: {e}")
        return {"category": "error"}


graph_builder = StateGraph(State)

graph_builder.add_node("identify_intent", identify_intent)

graph_builder.add_edge(START, "identify_intent")

orchestrator_graph = graph_builder.compile()


async def get_orchestrator_response(
    query: str, chained: bool = False
) -> Optional[schema.OrchestrationResponse]:
    """
    Generates a Orchestrator response for a given query using a LangGraph workflow.

    Args:
        query (str): The user's query for navigation.
        chained (bool): This parameter is ignored, but included for compatibility.

    Returns:
        schema.OrchestrationResponse: The navigation response, or None if no response is generated.
    """
    result = orchestrator_graph.invoke({"query": query})
    category = result.get("category")
    logger.info(f"Category: {category}")
    response = schema.OrchestrationResponse(category=category)
    return response
