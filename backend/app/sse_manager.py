# backend/app/sse_manager.py (REVISED)
import asyncio
from fastapi import Request
from typing import Dict, AsyncGenerator
import json
from .models import SSEventData
import logging  # Use proper logging

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Dictionary to hold queues per task_id. Queues are created by the first sender or receiver.
# WARNING: Still in-memory, not suitable for multi-replica.
#          Potential minor memory leak if client never connects & task errors before __CLOSE__.
task_queues: Dict[str, asyncio.Queue] = {}
# Lock to prevent race conditions when accessing/modifying task_queues dict itself
_dict_lock = asyncio.Lock()


async def sse_generator(request: Request, task_id: str) -> AsyncGenerator[str, None]:
    """
    Yields SSE formatted messages. Retrieves or creates queue for the task.
    Cleans up the queue on disconnect or completion.
    """
    queue = None
    # --- Safely get or create the queue ---
    async with _dict_lock:
        if task_id in task_queues:
            queue = task_queues[task_id]
            logger.info(
                f"SSE generator attaching to existing queue for task: {task_id}"
            )
        else:
            # This case might happen if client connects before any send_update was called
            queue = asyncio.Queue()
            task_queues[task_id] = queue
            logger.info(f"SSE generator created new queue for task: {task_id}")
    # --- End safe access ---

    client_disconnected = False
    try:
        while not client_disconnected:
            # Check disconnect before waiting
            if await request.is_disconnected():
                logger.warning(f"Client disconnected for task: {task_id}")
                client_disconnected = True
                break  # Exit loop immediately

            try:
                # Wait for an update with a timeout to allow disconnect check
                event_data: SSEventData = await asyncio.wait_for(
                    queue.get(), timeout=1.0
                )

                if (
                    event_data.event == "__CLOSE__"
                ):  # Special event to close from backend
                    logger.info(
                        f"Closing SSE connection via __CLOSE__ signal for task: {task_id}"
                    )
                    break  # Exit loop

                # Format and send the actual event
                sse_message = f"event: {event_data.event}\ndata: {json.dumps(event_data.data)}\n\n"
                yield sse_message
                queue.task_done()  # Mark task as done in queue

            except asyncio.TimeoutError:
                # No update received, loop continues to check disconnect
                continue
            except asyncio.CancelledError:
                logger.info(f"SSE generator task cancelled for {task_id}")
                client_disconnected = True  # Treat cancellation like disconnect
                break
            except Exception as e:
                # Log detailed error and try to inform client
                logger.error(
                    f"Error in SSE generator loop for {task_id}: {e}", exc_info=True
                )
                try:
                    error_event = SSEventData(
                        event="error", data={"message": "Internal SSE processing error"}
                    )
                    yield f"event: {error_event.event}\ndata: {json.dumps(error_event.data)}\n\n"
                except Exception as send_err:
                    logger.error(
                        f"Failed to send error event to client for {task_id}: {send_err}"
                    )
                break  # Stop sending on internal errors

    finally:
        logger.info(
            f"Cleaning up SSE resources for task: {task_id}. Client disconnected: {client_disconnected}"
        )
        # --- Safely remove the queue ---
        async with _dict_lock:
            if task_id in task_queues:
                # Optional: Log if queue still has items (indicates client disconnect before completion)
                # pending_items = task_queues[task_id].qsize()
                # if pending_items > 0:
                #    logger.warning(f"Removing queue for {task_id} with {pending_items} pending items.")
                del task_queues[task_id]
                logger.info(
                    f"Removed queue from active connections for task: {task_id}"
                )
            else:
                # This might happen if cleanup is called twice somehow, or task errored very early
                logger.warning(
                    f"Tried to clean up queue for task {task_id}, but it was already removed."
                )
        # --- End safe access ---


async def send_update(task_id: str, event: str, data: dict | list | str | None = None):
    """
    Pushes an update to the task's queue. Creates queue if it doesn't exist.
    """
    queue = None
    event_data = SSEventData(event=event, data=data)
    # --- Safely get or create the queue ---
    async with _dict_lock:
        if task_id not in task_queues:
            # Create the queue if this is the first message for this task
            task_queues[task_id] = asyncio.Queue()
            logger.info(f"Send_update created queue for task: {task_id}")
        queue = task_queues[task_id]
    # --- End safe access ---

    try:
        # Put the item in the queue (even if generator isn't listening yet)
        await queue.put(event_data)
        # logger.debug(f"Sent update '{event}' for task {task_id}") # Use debug level for frequent logs
    except Exception as e:
        # Log error if putting into queue fails (should be rare)
        logger.error(
            f"Failed to put update '{event}' into queue for task {task_id}: {e}",
            exc_info=True,
        )


# close_connection remains the same, it uses the modified send_update
async def close_connection(task_id: str):
    """Signal the SSE generator to close gracefully via a special event."""
    await send_update(task_id, "__CLOSE__", None)
