import time
from typing import Optional
from .clients import GeminiClient


class GeminiVideoUploader:
    """
    Handles video upload and processing for Gemini API
    """

    def __init__(self, client: Optional[GeminiClient] = None):
        """
        Initialize the uploader with a GeminiClient

        Args:
            client: Optional GeminiClient instance. If not provided, creates a new one.
        """
        self.client = client or GeminiClient()

    def upload_and_query(self, video_path: str, query: str) -> str:
        """
        Upload a video file and query it using Gemini API

        Args:
            video_path: Path to the video file
            query: Text prompt to analyze the video

        Returns:
            str: Gemini's response text
        """
        # Upload the video
        print("Uploading video...")
        video_file = self.client.client.files.upload(path=video_path)
        print(f"Upload completed: {video_file.uri}")

        # Wait for processing
        print("Processing video", end="")
        while video_file.state.name == "PROCESSING":
            print(".", end="", flush=True)
            time.sleep(1)
            video_file = self.client.client.files.get(name=video_file.name)
        print("\n")

        # Check for failure
        if video_file.state.name == "FAILED":
            raise ValueError(f"Video processing failed: {video_file.state.name}")

        # Generate response
        print("Generating response...")
        response = self.client.client.models.generate_content(
            model="gemini-2.0-flash", contents=[video_file, query]
        )

        return response.text
