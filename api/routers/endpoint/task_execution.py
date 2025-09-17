from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from api import db, agent
from sqlmodel import Session
from api.core.logging_config import logger
from typing import Annotated, Dict, Any
from uuid import uuid4
from langgraph.types import Command, Interrupt
import asyncio

router = APIRouter()
SessionDep = Annotated[Session, Depends(db.get_session)]

@router.websocket("/ws/task_execution/")
async def websocket_task_execution(websocket: WebSocket, session: SessionDep):
    await websocket.accept()
    thread_id = None
    current_state = None

    try:
        # Receive initial message from client
        initial_data = await websocket.receive_json()
        query = initial_data.get("query", "")
        chained = initial_data.get("chained", False)
        thread_id = initial_data.get("thread_id") or str(uuid4().hex)
        resume = initial_data.get("resume")

        logger.warning(f"Task Execution Query: {query}, Thread ID: {thread_id}, Chained: {chained}")

        config = {"configurable": {"thread_id": thread_id}}

        # Initialize state
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
            "action_context": {"previous_results": [], "already_executed": []},
            "iter_count": 0,
        }

        # Initialize stream and iterator
        stream = agent.task_execution_graph.astream(
            initial_state if resume is None else Command(resume=resume.lower()),
            config=config
        )
        stream_iter = stream.__aiter__()

        while True:
            try:
                event = await stream_iter.__anext__()
                logger.debug(f"Processing stream event: {event}")
            except StopAsyncIteration:
                logger.info("Stream ended normally, closing WebSocket")
                break
            except Exception as e:
                logger.error(f"Stream error: {e}")
                await websocket.send_json({"error": f"Stream processing failed: {str(e)}"})
                break

            # Handle interrupt event
            if isinstance(event, dict) and "__interrupt__" in event:
                interrupt_tuple = event["__interrupt__"]
                if (
                    isinstance(interrupt_tuple, tuple)
                    and len(interrupt_tuple) > 0
                    and isinstance(interrupt_tuple[0], Interrupt)
                ):
                    interrupt_obj = interrupt_tuple[0]
                    logger.info(f"Interrupt received - resumable: {interrupt_obj.resumable}, namespace: {interrupt_obj.ns}")

                    await websocket.send_json(
                        {
                            "interrupt": True,
                            "payload": interrupt_obj.value,
                            "resumable": interrupt_obj.resumable,
                            "namespace": interrupt_obj.ns,
                            "thread_id": thread_id,
                        }
                    )

                    try:
                        approval_data = await asyncio.wait_for(websocket.receive_json(), timeout=300.0)
                        resume_value = approval_data.get("resume")
                        if resume_value is None:
                            logger.warning(f"No resume value received for thread {thread_id}, cancelling")
                            await websocket.send_json({"error": "No approval decision provided"})
                            break

                        logger.info(f"Received approval response: {resume_value}, thread_id: {thread_id}")

                        # Update state with approval decision
                        current_state = await agent.task_execution_graph.aget_state(config)
                        if not current_state:
                            logger.error(f"Failed to retrieve state for thread {thread_id}")
                            await websocket.send_json({"error": "Failed to retrieve workflow state"})
                            break

                        current_state_values = current_state.values
                        current_state_values["user_approved"] = resume_value.lower() == "true"
                        logger.debug(f"Updating state with user_approved={current_state_values['user_approved']}, tool_calls={current_state_values.get('tool_calls')}, identified_actions={current_state_values.get('identified_actions')}")
                        await agent.task_execution_graph.aupdate_state(config, current_state_values)

                        # Resume stream from current checkpoint
                        stream = agent.task_execution_graph.astream(
                            Command(resume=resume_value.lower()),
                            config=config
                        )
                        stream_iter = stream.__aiter__()
                        continue

                    except asyncio.TimeoutError:
                        logger.error(f"Approval timeout for thread {thread_id}")
                        await websocket.send_json({"error": "Approval request timed out"})
                        break
                    except Exception as e:
                        logger.error(f"Error processing approval for thread {thread_id}: {e}")
                        await websocket.send_json({"error": f"Approval processing failed: {str(e)}"})
                        break

                else:
                    logger.error(f"Invalid interrupt format: {interrupt_tuple}")
                    await websocket.send_json({"error": "Invalid interrupt format"})
                    break

            # Handle normal state events
            elif isinstance(event, dict) and len(event) == 1:
                state_key = next(iter(event.keys()))
                state = event[state_key]

                if not isinstance(state, dict):
                    logger.error(f"Unexpected state type: {type(state)}, state: {state}")
                    await websocket.send_json({"error": "Invalid state format"})
                    break

                current_state = state
                logger.debug(f"Processing state: {state}")

                event_data = {
                    "response": state.get("final_response") or state.get("tool_response", ""),
                    "status": bool(state.get("final_response") or state.get("tool_response", "")),
                    "thread_id": thread_id,
                    "requires_approval": state.get("requires_approval", False),
                    "actions_to_review": state.get("actions_to_review"),
                    "is_final": bool(state.get("final_response")) and not state.get("requires_approval", False),
                }

                logger.debug(f"Sending event data: {event_data}")
                await websocket.send_json(event_data)

                if state.get("final_response") and not state.get("requires_approval", False):
                    logger.info(f"Final response reached for thread {thread_id}: {state['final_response'][:50]}...")
                    event_data["is_final"] = True
                    await websocket.send_json(event_data)
                    break

            else:
                logger.error(f"Unexpected event type: {type(event)}, event: {event}")
                await websocket.send_json({"error": f"Invalid event format: {type(event)}"})
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket connection closed by client, thread_id: {thread_id}")
    except asyncio.TimeoutError:
        logger.error(f"WebSocket operation timed out, thread_id: {thread_id}")
        await websocket.send_json({"error": "Operation timed out"})
    except Exception as e:
        logger.error(f"WebSocket error for thread {thread_id}: {e}")
        await websocket.send_json({"error": str(e)})
    finally:
        if session:
            session.close()
        logger.info(f"WebSocket connection closed for thread: {thread_id}")
        try:
            await websocket.close()
        except:
            pass