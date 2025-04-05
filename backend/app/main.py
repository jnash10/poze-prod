import os
import uuid
import asyncio
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import aiofiles  # For async file writing

from .sse_manager import sse_generator
from .processing import run_analysis_pipeline

# --- App Initialization ---
app = FastAPI(title="Video Analysis API")

# --- CORS Middleware ---
# Allow requests from your React frontend development server and production URL
# IMPORTANT: Update origins in production!
origins = [
    "http://localhost:5173",  # Default Vite dev server port
    "http://localhost:3000",  # Default create-react-app dev server port
    "http://192.168.0.103:5173",
    # Add your production frontend URL here later
    # e.g., "https://your-frontend-app.azurewebsites.net"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# --- Temporary File Storage ---
# Ensure this directory exists or create it
UPLOAD_DIR = "/tmp/video_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# --- Endpoints ---
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Video Analysis API"}


@app.post(
    "/analyze_video", status_code=202
)  # 202 Accepted: request accepted, processing started
async def analyze_video_endpoint(
    background_tasks: BackgroundTasks, file: UploadFile = File(...)
):
    """
    Uploads video, starts background analysis, returns task ID.
    """
    if not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Please upload a video."
        )

    task_id = str(uuid.uuid4())
    file_extension = os.path.splitext(file.filename)[1]
    temp_video_path = os.path.join(UPLOAD_DIR, f"{task_id}{file_extension}")

    # Save the uploaded file asynchronously
    try:
        async with aiofiles.open(temp_video_path, "wb") as buffer:
            content = await file.read()  # Read file content
            await buffer.write(content)  # Write to temp file
        print(f"File saved temporarily to: {temp_video_path}")
    except Exception as e:
        print(f"Error saving file: {e}")
        raise HTTPException(
            status_code=500, detail=f"Could not save uploaded file: {e}"
        )
    finally:
        await file.close()  # Ensure file handle is closed

    # Add the analysis function to background tasks
    background_tasks.add_task(run_analysis_pipeline, task_id, temp_video_path)
    print(f"Background task scheduled: {task_id}")

    # Return the task ID so the client can connect to the stream
    return JSONResponse({"task_id": task_id})


@app.get("/stream/{task_id}")
async def stream_endpoint(request: Request, task_id: str):
    """
    Endpoint for Server-Sent Events connection.
    """
    # Basic check if task_id looks valid (UUID format) - doesn't guarantee task exists yet
    try:
        uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format.")

    # Return the streaming response using the generator
    # media_type must be text/event-stream for SSE
    return StreamingResponse(
        sse_generator(request, task_id), media_type="text/event-stream"
    )
