from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from api import db, agent
from sqlmodel import Session
from api.core.logging_config import logger
from typing import Annotated, Dict, Any
from uuid import uuid4
from langgraph.types import Command, Interrupt

router = APIRouter()
SessionDep = Annotated[Session, Depends(db.get_session)]

@router.websocket("/ws/task_execution/")
async def websocket_task_execution(websocket: WebSocket, session: SessionDep):
    await websocket.accept()
    thread_id = None
    try:
        # Receive initial message from client
        initial_data = await websocket.receive_json()
        query = initial_data.get("query", "")
        chained = initial_data.get("chained", False)
        thread_id = initial_data.get("thread_id") or uuid4().hex
        resume = initial_data.get("resume")

        logger.warning(f"Task Execution Query: {query}, Thread ID: {thread_id}")

        config = {"configurable": {"thread_id": thread_id}}

        command = Command(resume=resume) if resume is not None else None
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
            "action_context": None,
            "iter_count": 0,
        }

        # Start the stream with either the resume command or initial state
        stream = agent.task_execution_graph.astream(command if command else initial_state, config=config)

        async for event in stream:
            logger.info(f"Event: {event}")

            # Handle interrupt inside '__interrupt__' key
            if isinstance(event, dict) and "__interrupt__" in event:
                interrupt_tuple = event["__interrupt__"]
                if isinstance(interrupt_tuple, tuple) and len(interrupt_tuple) > 0 and isinstance(interrupt_tuple[0], Interrupt):
                    interrupt_obj = interrupt_tuple[0]
                    await websocket.send_json({
                        "interrupt": True,
                        "payload": interrupt_obj.value,
                        "resumable": interrupt_obj.resumable,
                        "namespace": interrupt_obj.ns,
                        "thread_id": thread_id,
                    })
                    approval_data = await websocket.receive_json()
                    resume_value = approval_data.get("resume")
                    if resume_value is not None:
                        command = Command(resume=resume_value)
                        stream = agent.task_execution_graph.astream(command, config=config)
                        continue
                    else:
                        break
                else:
                    logger.error(f"Invalid interrupt format: {interrupt_tuple}")
                    await websocket.send_json({"error": "Invalid interrupt format"})
                    break

            # Handle normal dict state events
            elif isinstance(event, dict):
                state = list(event.values())[0] if event.values() else {}
                if not isinstance(state, dict):
                    logger.error(f"Unexpected state type: {type(state)}, state: {state}")
                    await websocket.send_json({"error": "Invalid state format"})
                    break

                event_data = {
                    "response": state.get("tool_response", ""),
                    "status": bool(state.get("tool_response", "")),
                    "thread_id": thread_id,
                    "requires_approval": state.get("requires_approval", False),
                    "actions_to_review": state.get("actions_to_review"),
                    "is_final": state.get("final_response") is not None,
                }
                await websocket.send_json(event_data)

                if state.get("requires_approval", False):
                    logger.warning("Approval required, awaiting user decision")
                    approval_data = await websocket.receive_json()
                    resume_value = approval_data.get("resume")
                    if resume_value is not None:
                        state["user_approved"] = resume_value.lower() == "true"
                        command = Command(resume=resume_value.lower())
                        stream = agent.task_execution_graph.astream(command, config=config)
                        continue

                if state.get("final_response") and not state.get("requires_approval", False):
                    break

            else:
                logger.error(f"Unexpected event type: {type(event)}, event: {event}")
                await websocket.send_json({"error": f"Invalid event format: {type(event)}"})
                break


    except WebSocketDisconnect:
        logger.info("WebSocket connection closed by client")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({"error": str(e)})
    finally:
        session.close()
        logger.info("WebSocket connection closed")
        await websocket.close()
