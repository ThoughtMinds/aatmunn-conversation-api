from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from api import db, agent
from sqlmodel import Session
from api.core.logging_config import logger
from typing import Annotated, AsyncGenerator
from json import dumps
from uuid import uuid4
from langgraph.types import Command

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

    Streams the task execution process, including interruptions for human approval,
    and resumes execution based on user input.

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
    thread_id = thread_id or uuid4().hex

    async def stream_task_execution() -> AsyncGenerator[str, None]:
        try:
            config = {"configurable": {"thread_id": thread_id}}

            # Initial state for new execution
            initial_state = {
                "query": query,
                "chained": chained,
                "tool_calls": [],
                "identified_actions": [],
                "tool_response": "",
                "final_response": "",
                "user_approved": False,
                "requires_approval": False,
                "actions_to_review": None,
            }

            if resume_action is not None:
                # Resume graph with user approval decision
                resume_value = resume_action.lower() == "approve"
                command = Command(resume=resume_value)
                async for event in agent.task_execution_graph.astream(command, config=config):
                    state = list(event.values())[0]
                    event_data = {
                        "response": state.get("final_response", ""),
                        "status": bool(state.get("final_response", "")),
                        "thread_id": thread_id,
                        "requires_approval": state.get("requires_approval", False),
                        "actions_to_review": state.get("actions_to_review"),
                    }
                    yield f"data: {dumps(event_data)}\n\n"
                    if state.get("final_response", "") and not state.get("requires_approval", False):
                        break
            else:
                # Start new execution with initial state
                async for event in agent.task_execution_graph.astream(initial_state, config=config):
                    state = list(event.values())[0]
                    event_data = {
                        "response": state.get("final_response", ""),
                        "status": bool(state.get("final_response", "")),
                        "thread_id": thread_id,
                        "requires_approval": state.get("requires_approval", False),
                        "actions_to_review": state.get("actions_to_review"),
                    }
                    yield f"data: {dumps(event_data)}\n\n"
                    if state.get("requires_approval", False):
                        # Pause streaming until approval is received
                        logger.warning("Approval required, awaiting user decision")
                        break
                    if state.get("final_response", "") and not state.get("requires_approval", False):
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

    Resumes the workflow with the user's approval decision.

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
            command = Command(resume=approved)
            async for event in agent.task_execution_graph.astream(command, config=config):
                state = list(event.values())[0]
                event_data = {
                    "response": state.get("final_response", "Approval processed"),
                    "status": True,
                    "thread_id": thread_id,
                    "requires_approval": state.get("requires_approval", False),
                    "actions_to_review": state.get("actions_to_review"),
                }
                yield f"data: {dumps(event_data)}\n\n"
                if state.get("final_response", "") and not state.get("requires_approval", False):
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
