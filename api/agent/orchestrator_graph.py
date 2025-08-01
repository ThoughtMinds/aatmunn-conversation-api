from typing_extensions import TypedDict
from langgraph.graph import START, StateGraph
from api import llm

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
        response = llm.orchestrator_chain.invoke({"query": state["query"]})
        category = response.content.lower()
        # TODO: Add validation
        return {"category": category}
    except Exception as e:
        print(f"Failed to get Orchestration due to: {e}")
        return {"category": "error"} 

graph_builder = StateGraph(State)

graph_builder.add_node("identify_intent", identify_intent)

graph_builder.add_edge(START, "identify_intent")

orchestrator_graph = graph_builder.compile()