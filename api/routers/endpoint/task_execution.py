from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from api import db, schema, agent
from sqlmodel import Session
from api.core.logging_config import logger
from typing import Annotated, AsyncGenerator
from json import dumps
from uuid import uuid4

router = APIRouter()
SessionDep = Annotated[Session, Depends(db.get_session)]


@router.get("/execute_task/", response_model=None)
async def execute_task(
    session: SessionDep,
    query: str = Query(..., description="The user's query"),
    chained: bool = Query(False, description="Whether to use chained tool calls"),
    thread_id: str = Query(
        None, description="Optional thread ID for resuming execution"
    ),
    resume_action: str = Query(
        None, description="Resume action (approve/reject) if resuming"
    ),
) -> StreamingResponse:
    """
    Execute a task for a given query using Server-Sent Events (SSE).

    This endpoint streams the task execution process, including intermediate states and interruptions
    for human approval, using SSE.

    Args:
        session (SessionDep): The database session dependency.
        query (str): The user's query.
        chained (bool): Whether to use chained tool calls.
        thread_id (str, optional): The thread ID for resuming execution.
        resume_action (str, optional): Resume action if resuming (approve/reject).

    Returns:
        StreamingResponse: A stream of task execution states in SSE format.
    """
    logger.warning(f"Task Execution Query: {query}")

    async def stream_task_execution() -> AsyncGenerator[str, None]:
        try:
            # thread_id = thread_id or uuid4().hex
            thread_id = uuid4().hex
            config = {"configurable": {"thread_id": thread_id}}

            initial_state = {
                "query": query,
                "chained": chained,
                "tool_calls": [],
                "identified_actions": [],
                "tool_response": "",
                "summarized_response": "",
                "final_response": "",
                "user_approved": False,
                "requires_approval": False,
                "actions_to_review": None,
            }

            if thread_id and resume_action is not None:
                initial_state["user_approved"] = resume_action == "approve"

            async for event in agent.task_execution_graph.astream(
                initial_state, config=config
            ):
                state = list(event.values())[0]  # Get the latest state
                event_data = {
                    "response": state.get("final_response", ""),
                    "status": state.get("final_response", "") != "",
                    "processing_time": 0,  # To be updated with actual time
                    "thread_id": thread_id,
                    "requires_approval": state.get("requires_approval", False),
                    "actions_to_review": state.get("actions_to_review"),
                }

                # Send intermediate state
                yield f"data: {dumps(event_data, default=lambda o: '<object>')}\n\n"
                logger.info(f"Streamed event: {event_data}")

                # If approval is required, wait for user input (handled client-side)
                if state.get("requires_approval", False):
                    logger.warning("Approval required, awaiting user decision")
                    break  # Pause streaming until approval is received

                # If final response is set, end the stream
                if state.get("final_response", "") and not state.get(
                    "requires_approval", False
                ):
                    logger.info("Task execution completed")
                    break

        except Exception as e:
            error_msg = {"error": str(e)}
            logger.error(f"Stream error: {e}")
            yield f"data: {dumps(error_msg)}\n\n"
        finally:
            session.close()
            logger.info("Stream response generator closed")

    return StreamingResponse(
        stream_task_execution(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/handle_approval/", response_model=None)
async def handle_approval(
    session: SessionDep,
    thread_id: str = Query(..., description="The thread ID to resume"),
    approved: bool = Query(..., description="Whether to approve the actions"),
) -> StreamingResponse:
    """
    Handle user approval/rejection of actions using SSE.

    Args:
        session (SessionDep): The database session dependency.
        thread_id (str): The thread ID to resume.
        approved (bool): Whether to approve the actions.

    Returns:
        StreamingResponse: A stream confirming the approval result.
    """
    logger.warning(f"Handling approval for thread {thread_id}: {approved}")

    async def stream_approval_result() -> AsyncGenerator[str, None]:
        try:
            config = {"configurable": {"thread_id": thread_id}}
            initial_state = {
                "user_approved": approved,
                "query": "",  # Query preserved in checkpoint
                "chained": False,
                "tool_calls": [],
                "identified_actions": [],
                "tool_response": "",
                "summarized_response": "",
                "final_response": "",
            }

            async for event in agent.task_execution_graph.astream(
                initial_state, config=config
            ):
                state = list(event.values())[0]
                event_data = {
                    "response": state.get("final_response", "Approval processed"),
                    "status": True,
                    "processing_time": 0,  # To be updated with actual time
                    "thread_id": thread_id,
                    "requires_approval": False,
                    "actions_to_review": None,
                }
                yield f"data: {dumps(event_data, default=lambda o: '<object>')}\n\n"
                logger.info(f"Streamed approval result: {event_data}")

                if state.get("final_response", ""):
                    logger.info("Approval process completed")
                    break

        except Exception as e:
            error_msg = {"error": str(e)}
            logger.error(f"Approval stream error: {e}")
            yield f"data: {dumps(error_msg)}\n\n"
        finally:
            session.close()
            logger.info("Approval stream generator closed")

    return StreamingResponse(
        stream_approval_result(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
