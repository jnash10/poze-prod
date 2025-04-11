# backend/app/processing.py (REVISED)
import os
import asyncio
from dotenv import load_dotenv

# Import your VLM classes
from VLM.helpers import VideoProcessor
from VLM.get_attributes import GeminiVideoAttributeExtractor
from VLM.generate_feedback import GeminiFeedbackGenerator

# Import SSE manager and models
from .sse_manager import (
    send_update,
    close_connection,
    logger,
)  # Use logger from sse_manager
from .models import ExtractedAttributes, GeneratedFeedback

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


async def run_analysis_pipeline(task_id: str, video_path: str):
    """The main processing logic, running blocking calls in executor"""
    loop = asyncio.get_running_loop()  # Get the current event loop

    try:
        logger.info(f"[{task_id}] Starting analysis for {video_path}")
        await send_update(
            task_id, "status_update", {"message": "Initializing analysis..."}
        )

        # --- Initialization ---
        # NOTE: If these initializations themselves are slow/blocking,
        # they might also need run_in_executor, but usually they are fast.
        video_processor = VideoProcessor()
        # Ensure API Key is passed if needed by your classes constructor
        attribute_extractor = (
            GeminiVideoAttributeExtractor()
        )  # Assuming constructor is fast
        feedback_generator = GeminiFeedbackGenerator()  # Assuming constructor is fast

        # --- Step 1: Process Video (Run in executor) ---
        logger.info(f"[{task_id}] Processing video...")
        await send_update(
            task_id, "status_update", {"message": "Processing video frames..."}
        )
        # Use run_in_executor for the potentially blocking video processing
        frames = await loop.run_in_executor(
            None,  # Use default ThreadPoolExecutor
            video_processor.process_video,  # The function to run
            video_path,  # First argument to process_video
            10,  # Second argument (n_frames)
        )
        if not frames:
            raise ValueError("Failed to extract frames from video.")
        logger.info(f"[{task_id}] Video processing complete. Got {len(frames)} frames.")

        # --- Step 2: Get Attributes (Run in executor) ---
        logger.info(f"[{task_id}] Extracting attributes...")
        await send_update(
            task_id,
            "status_update",
            {"message": "Assistant Coach analysing..."},
        )
        # Use run_in_executor for the blocking call (includes Gemini network request)
        # **Important**: Pass the initialized extractor instance if needed by the method,
        # or make the method static/class method if appropriate.
        # Here assuming get_attributes is an instance method:
        attributes_obj_dict = await loop.run_in_executor(
            None,
            attribute_extractor.get_attributes,  # The method to run
            frames,  # Argument to get_attributes
            # Note: If get_attributes returned an object, you might need an intermediate function
            #       to call the method and then convert to dict, e.g.:
            #       lambda f: attribute_extractor.get_attributes(f).dict() # if it returns Pydantic model
            #       lambda f: attribute_extractor.get_attributes(f).__dict__ # if it returns simple object
        )
        # Assuming get_attributes returns a dict or object convertible to dict
        if isinstance(attributes_obj_dict, dict):
            attributes_data = attributes_obj_dict
        else:
            # Attempt conversion if it's an object (adjust based on actual return type)
            try:
                attributes_data = attributes_obj_dict.__dict__
            except AttributeError:
                logger.error(
                    f"[{task_id}] Cannot convert attributes result type {type(attributes_obj_dict)} to dict."
                )
                raise TypeError("Unexpected type returned by get_attributes")

        attributes_model = ExtractedAttributes(
            **attributes_data
        )  # Validate/Structure data
        await send_update(task_id, "attributes_update", attributes_model.dict())
        logger.info(f"[{task_id}] Attributes extracted.")

        # --- Step 3: Generate Feedback (Run in executor) ---
        logger.info(f"[{task_id}] Generating feedback...")
        await send_update(
            task_id, "status_update", {"message": "Head Coach giving feedback"}
        )
        # Use run_in_executor for the blocking call (includes Gemini network request)
        feedback_obj_dict = await loop.run_in_executor(
            None,
            feedback_generator.generate_feedback,  # The method to run
            attributes_model,  # First argument (pass the Pydantic model)
            frames,  # Second argument
            # Similar note as above regarding return type and conversion if necessary
        )
        # Assuming generate_feedback returns a dict or object convertible to dict
        if isinstance(feedback_obj_dict, dict):
            feedback_data = feedback_obj_dict
        else:
            try:
                feedback_data = feedback_obj_dict.__dict__
            except AttributeError:
                logger.error(
                    f"[{task_id}] Cannot convert feedback result type {type(feedback_obj_dict)} to dict."
                )
                raise TypeError("Unexpected type returned by generate_feedback")

        feedback_model = GeneratedFeedback(**feedback_data)  # Validate/Structure data
        await send_update(task_id, "feedback_update", feedback_model.dict())
        logger.info(f"[{task_id}] Feedback generated.")

        # --- Completion ---
        await send_update(
            task_id, "complete", {"message": "Analysis finished successfully."}
        )
        logger.info(f"[{task_id}] Analysis pipeline finished.")

    except Exception as e:
        # Log the full exception traceback for debugging
        logger.error(f"[{task_id}] Error during analysis: {e}", exc_info=True)
        # Send error details back to the client
        await send_update(task_id, "error", {"message": f"Analysis failed: {str(e)}"})
    finally:
        # Signal the SSE stream associated with this task to close
        await close_connection(task_id)
        # Clean up the temporary video file (run this sync is fine)
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                logger.info(f"[{task_id}] Removed temporary file: {video_path}")
        except OSError as e:
            logger.error(f"[{task_id}] Error removing temporary file {video_path}: {e}")
