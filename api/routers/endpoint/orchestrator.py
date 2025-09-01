from fastapi import APIRouter, Depends, Query
from api import agent, db, schema
from typing import Annotated, Optional, AsyncGenerator
from sqlmodel import Session
from fastapi.responses import StreamingResponse
from json import dumps
from api.core.logging_config import logger


router = APIRouter()
SessionDep = Annotated[Session, Depends(db.get_session)]


@router.post("/identify_intent/", response_model=schema.OrchestrationResponse)
async def identify_intent(
    session: SessionDep, data: schema.OrchestrationQuery
) -> schema.OrchestrationResponse:
    """
    Identify the intent of a user's query.

    This endpoint takes a user's query and uses the orchestrator agent to
    categorize it as 'navigation', 'summarization', or 'task_execution'.

    Args:
        session (SessionDep): The database session dependency.
        data (schema.OrchestrationQuery): The user's query.

    Returns:
        schema.OrchestrationResponse: The identified category of the query.
    """
    query = data.query
    response = await agent.get_orchestrator_response(query=query)
    return response


@router.get("/invoke_agent")
async def invoke_agent(
    agent_name: str = Query(
        ...,
        description="The agent to invoke (e.g., navigation, summarization, task_execution)",
    ),
    query: str = Query(..., description="The user's query"),
    chained: bool = Query(False, description="Whether to use chained tool calls"),
) -> StreamingResponse:
    """
    Invoke an agent to process a query using Server-Sent Events (SSE).

    This endpoint takes an agent name, query, and chained parameter as query parameters and streams the response
    using SSE.

    Args:
        session (SessionDep): The database session dependency.
        agent_name (str): The name of the agent to invoke.
        query (str): The user's query.
        chained (bool): Whether to use chained tool calls.

    Returns:
        StreamingResponse: A stream of agent responses in SSE format.
    """
    logger.info(f"Request: {agent_name=} | {chained=}")

    # Map agent name to the appropriate function
    agent_to_use = None

    if agent_name == "summarization":
        agent_to_use = agent.get_streaming_summarized_response
    elif agent_name in ["task_execution", "taskexecution"]:
        agent_to_use = agent.get_streaming_task_execution_response
    elif agent_name == "navigation":
        agent_to_use = agent.get_streaming_navigation_response
    else:
        async def error_stream() -> AsyncGenerator[str, None]:
            yield f"data: {dumps({'error': 'Invalid agent specified'})}\n\n"
        return StreamingResponse(
            error_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    logger.info(f"Using agent: {agent_name}")

    async def stream_response() -> AsyncGenerator[str, None]:
        try:
            async for event in agent_to_use(query=query, chained=chained):
                # Check if this is the final event with a response
                if event.get("final_response"):
                    # This is the final message
                    logger.info(f"Final event: {event}")
                    event_data = dumps(event, default=lambda o: "<object>")
                    yield f"data: {event_data}\n\n"
                    logger.info("Stream completed successfully")
                    break
                else:
                    # Intermediate event
                    logger.info(f"Intermediate event: {event}")
                    event_data = dumps(event, default=lambda o: "<object>")
                    yield f"data: {event_data}\n\n"

        except Exception as e:
            error_msg = f"data: {dumps({'error': str(e)})}\n\n"
            logger.error(f"Stream error: {e}")
            yield error_msg
        finally:
            # Ensure any cleanup happens here
            logger.info("Stream response generator closed")

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
