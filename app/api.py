import uuid
import json
import datetime
import asyncio
import logging
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
from graph.builder import build_graph
from langgraph.checkpoint.memory import MemorySaver

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize MemorySaver for state storage
memory = MemorySaver()
# Initialize graph
graph = build_graph(memory)

# Dict to store sessions
active_sessions: Dict[str, Any] = {}

# Store interrupt status
interrupt_status = {}

app = FastAPI(title="BEJO AI API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    user_id: str


class MessageRequest(BaseModel):
    user_id: str
    question: str


class InterruptResponse(BaseModel):
    user_id: str
    approved: bool


@app.post("/ask")
async def create_session(request: AskRequest):
    """
    Create a new session for chat with AI

    Args:
        request: Object with user_id

    Returns:
        Dict with newly created session_id
    """
    try:
        session_id = str(uuid.uuid4())
        active_sessions[session_id] = {
            "user_id": request.user_id,
            "created_at": datetime.datetime.now(),
        }

        logger.info(f"Created new session {session_id} for user {request.user_id}")
        return {"session_id": session_id}
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")


@app.post("/ask/{session_id}")
async def ask_question(session_id: str, request: MessageRequest, req: Request):
    """
    Send a question to AI in a specific session

    Args:
        session_id: Chat session ID
        request: Object with user_id and question

    Returns:
        StreamingResponse with answers from AI
    """
    # Validate session_id
    if session_id not in active_sessions:
        logger.warning(f"Session {session_id} not found")
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate user_id matches session
    if active_sessions[session_id]["user_id"] != request.user_id:
        logger.warning(f"User ID {request.user_id} does not match session {session_id}")
        raise HTTPException(status_code=403, detail="User ID does not match session")

    # Reset interrupt status if exists
    if session_id in interrupt_status:
        del interrupt_status[session_id]

    # Configuration for graph
    config = {"configurable": {"thread_id": session_id}}

    async def generate_stream():
        """Generator for streaming response from AI"""
        try:
            # Send initial message
            yield {
                "event": "start",
                "data": json.dumps({"type": "info", "data": "Processing question..."}),
            }

            # Pass both question and user_id to the graph
            step_data = {
                "question": request.question,
                "thread_id": session_id,
                "user_id": request.user_id,
            }

            # Stream directly from graph
            for step in graph.stream(step_data, config, stream_mode="updates"):
                # Check if client disconnected
                if await req.is_disconnected():
                    logger.info(f"Client disconnected from session {session_id}")
                    break

                # If there's an interrupt, send notification and wait for confirmation
                if "__interrupt__" in step:
                    # Send interrupt event
                    yield {
                        "event": "interrupt",
                        "data": json.dumps(
                            {
                                "type": "interrupt",
                                "data": "Do you want to execute this query?",
                            }
                        ),
                    }

                    # Wait for response from user
                    wait_count = 0
                    max_wait = 60  # 60 seconds timeout
                    while session_id not in interrupt_status and wait_count < max_wait:
                        await asyncio.sleep(1)
                        wait_count += 1

                        # Check if client disconnected during wait
                        if await req.is_disconnected():
                            logger.info(
                                f"Client disconnected during interrupt wait in session {session_id}"
                            )
                            return

                    # Check if there's a response
                    if session_id not in interrupt_status:
                        logger.warning(
                            f"Timeout waiting for confirmation in session {session_id}"
                        )
                        yield {
                            "event": "error",
                            "data": json.dumps(
                                {
                                    "type": "error",
                                    "data": "Timeout waiting for confirmation",
                                }
                            ),
                        }
                        return

                    # If user approves, continue
                    if interrupt_status[session_id]:
                        logger.info(f"User approved interrupt in session {session_id}")
                        for cont_step in graph.stream(
                            None, config, stream_mode="updates"
                        ):
                            if "answer" in cont_step:
                                yield {
                                    "event": "message",
                                    "data": json.dumps(
                                        {"type": "answer", "data": cont_step["answer"]}
                                    ),
                                }
                            elif "result_query" in cont_step:
                                yield {
                                    "event": "result",
                                    "data": json.dumps(
                                        {
                                            "type": "result",
                                            "data": cont_step["result_query"],
                                        }
                                    ),
                                }
                    else:
                        logger.info(f"User cancelled operation in session {session_id}")
                        yield {
                            "event": "message",
                            "data": json.dumps(
                                {
                                    "type": "answer",
                                    "data": "Operation cancelled by user",
                                }
                            ),
                        }

                    # Delete interrupt status
                    del interrupt_status[session_id]

                # If there's normal processing result
                elif "answer" in step:
                    yield {
                        "event": "message",
                        "data": json.dumps({"type": "answer", "data": step["answer"]}),
                    }
                # If there's intermediate result (e.g., SQL result)
                elif "result_query" in step:
                    yield {
                        "event": "result",
                        "data": json.dumps(
                            {"type": "result", "data": step["result_query"]}
                        ),
                    }
                # Debug - send all received steps
                else:
                    # Send step content as debug
                    yield {
                        "event": "debug",
                        "data": json.dumps({"type": "debug", "data": str(step)}),
                    }

            # Send completion message
            yield {
                "event": "end",
                "data": json.dumps(
                    {"type": "info", "data": "Finished processing question"}
                ),
            }

        except Exception as e:
            logger.error(f"Error in stream processing: {str(e)}")
            # Handle error and send as event
            yield {
                "event": "error",
                "data": json.dumps({"type": "error", "data": str(e)}),
            }

    return EventSourceResponse(generate_stream())


@app.post("/ask/{session_id}/interrupt")
async def handle_interrupt(session_id: str, response: InterruptResponse):
    """
    Handle interrupt response from user

    Args:
        session_id: Chat session ID
        response: Object with user_id and approved

    Returns:
        Confirmation that interrupt has been handled
    """
    try:
        # Validate session_id
        if session_id not in active_sessions:
            logger.warning(f"Session {session_id} not found for interrupt")
            raise HTTPException(status_code=404, detail="Session not found")

        # Validate user_id matches session
        if active_sessions[session_id]["user_id"] != response.user_id:
            logger.warning(
                f"User ID {response.user_id} does not match session {session_id} for interrupt"
            )
            raise HTTPException(
                status_code=403, detail="User ID does not match session"
            )

        # Save interrupt status
        interrupt_status[session_id] = response.approved
        logger.info(f"Interrupt response for session {session_id}: {response.approved}")

        return {"status": "success", "approved": response.approved}
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error handling interrupt: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error handling interrupt: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """
    Simple health check endpoint

    Returns:
        Status information about the API
    """
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "active_sessions": len(active_sessions),
    }


if __name__ == "__main__":
    import uvicorn

    load_dotenv()
    uvicorn.run(app, host="0.0.0.0", port=8000)
