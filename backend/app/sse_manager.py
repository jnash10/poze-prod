# backend/app/sse_manager.py (Redis Version)
import asyncio
from fastapi import Request
from typing import AsyncGenerator
import json
import redis.asyncio as redis # Import the async version
import logging
import os # To get Redis URL if needed

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Configure Redis connection
# Use environment variable or default to localhost
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
# Create a connection pool for efficiency
redis_pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)

# No more in-memory task_queues dictionary needed

async def sse_generator(request: Request, task_id: str) -> AsyncGenerator[str, None]:
    """
    Yields SSE formatted messages received via Redis Pub/Sub.
    Cleans up subscription on disconnect or completion.
    """
    logger.info(f"SSE generator starting for task: {task_id}")
    # Each generator needs its own connection from the pool
    redis_conn = redis.Redis(connection_pool=redis_pool)
    pubsub = redis_conn.pubsub()
    redis_channel = f"sse:{task_id}" # Define a channel name pattern

    await pubsub.subscribe(redis_channel)
    logger.info(f"SSE generator subscribed to Redis channel: {redis_channel}")

    client_disconnected = False
    try:
        while not client_disconnected:
            # 1. Check for client disconnect first
            if await request.is_disconnected():
                logger.warning(f"Client disconnected for task: {task_id}")
                client_disconnected = True
                break # Exit loop immediately

            # 2. Check for messages from Redis with a timeout
            try:
                # process message Coroutine waits for message or timeout
                message = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0),
                    timeout=1.5 # Slightly larger timeout for wait_for itself
                )

                if message is not None:
                    message_data_str = message['data']
                    logger.info(f"Received message from Redis for {task_id}: {message_data_str[:100]}...") # Log truncated data

                    # Attempt to parse the JSON data received from Redis
                    try:
                        event_dict = json.loads(message_data_str)
                        event_type = event_dict.get("event")
                        event_payload = event_dict.get("data")

                        if event_type == "__CLOSE__":
                            logger.info(f"Received __CLOSE__ via Redis for task {task_id}. Breaking SSE loop.")
                            break # Exit loop cleanly

                        # Format and yield the actual event
                        sse_message = f"event: {event_type}\ndata: {json.dumps(event_payload)}\n\n"
                        yield sse_message
                    except json.JSONDecodeError:
                        logger.error(f"Failed to decode JSON from Redis for {task_id}: {message_data_str}")
                    except Exception as parse_err:
                         logger.error(f"Error processing Redis message data for {task_id}: {parse_err}", exc_info=True)

            except asyncio.TimeoutError:
                # No message received from Redis in timeout period, loop continues to check disconnect
                # Optional: yield a keepalive comment here if needed
                # yield ": ping\n\n"
                continue
            except asyncio.CancelledError:
                 logger.info(f"SSE generator task cancelled for {task_id}")
                 client_disconnected = True # Treat cancellation like disconnect
                 break
            except Exception as e:
                 logger.error(f"Error in SSE generator Redis loop for {task_id}: {e}", exc_info=True)
                 client_disconnected = True # Stop on errors
                 break

    finally:
        logger.info(f"Cleaning up SSE Redis resources for task: {task_id}. Client disconnected: {client_disconnected}")
        # Unsubscribe and close the connection
        try:
            if pubsub.connection:
                await pubsub.unsubscribe(redis_channel)
                await pubsub.close()
            logger.info(f"Unsubscribed from Redis channel: {redis_channel}")
        except Exception as clean_err:
            logger.error(f"Error during Redis pubsub cleanup for {task_id}: {clean_err}")


async def send_update(task_id: str, event: str, data: dict | list | str | None = None):
    """
    Publishes an update to the task's Redis channel.
    """
    redis_conn = None # Create connection per publish or reuse one? Per publish is safer for short tasks.
    try:
        redis_conn = redis.Redis(connection_pool=redis_pool)
        redis_channel = f"sse:{task_id}"
        # Structure the message payload consistently
        message_payload = json.dumps({"event": event, "data": data})

        logger.info(f"Publishing event '{event}' to Redis channel '{redis_channel}' for task {task_id}")
        await redis_conn.publish(redis_channel, message_payload)
        logger.info(f"Successfully published event '{event}' for task {task_id}")

    except Exception as e:
        logger.error(
            f"Failed to publish update '{event}' to Redis for task {task_id}: {e}",
            exc_info=True,
        )
    finally:
         if redis_conn:
             await redis_conn.close() # Close the connection


async def close_connection(task_id: str):
    """Signal the SSE generator to close gracefully via a special event published to Redis."""
    # Use the same send_update function, which now publishes to Redis
    await send_update(task_id, "__CLOSE__", None)