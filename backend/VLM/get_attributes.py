from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from .clients import GeminiClient, ClaudeClient, OpenAIClient
from .helpers import VideoProcessor
from google.genai import types
import base64
import io
from VLM.helpers import ImageData


@dataclass
class BattingAttributes:
    """Dataclass to store batting analysis attributes"""

    age: str
    experience_level: str
    ball_length: str
    # shot_type: str


class BaseVideoAttributeExtractor(ABC):
    """Base class for extracting batting attributes from video using VLM"""

    SYSTEM_PROMPT = """You are a cricket expert who offers online coaching to people improving their batting technique."""

    ATTRIBUTE_PROMPT = """Analyze this cricket batting clip and provide the following attributes in a structured format:
    1. Approximate age of the player 
    2. Experience level (choose one: beginner(just starting to learn cricket), enthusiast(knows the basics and has practised), intermediate(University level), advanced(semi-professional), expert(professional level))
    3. Ball length (choose one: short, medium, full)
    4. Type of shot played or should have played
    
    Provide your response in the following format exactly:
    Age: <range_start_number - range_end_number>
    Experience: <level>
    Ball Length: <length>
    """  # Shot Type: <shot>

    def __init__(self, n_frames: int = 5):
        """
        Initialize the extractor

        Args:
            n_frames: Number of frames to extract from video
        """
        self.video_processor = VideoProcessor()
        self.n_frames = n_frames
        self.client = self._initialize_client()

    @abstractmethod
    def _initialize_client(self):
        """Initialize the specific VLM client"""
        pass

    @abstractmethod
    def _get_attributes(self, image_data: List[ImageData], prompt: str) -> str:
        """
        Get attributes from VLM using frames and prompt

        Args:
            image_data: List of ImageData objects containing PIL Images and their encodings
            prompt: Prompt for the VLM

        Returns:
            Raw response from VLM
        """
        pass

    def _parse_response(self, response: str) -> BattingAttributes:
        """Parse VLM response into structured format"""
        lines = response.strip().split("\n")
        attributes = {}

        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                attributes[key.strip().lower()] = value.strip()

        return BattingAttributes(
            age=attributes.get("age", ""),
            experience_level=attributes.get("experience", "").lower(),
            ball_length=attributes.get("ball length", "").lower(),
            # shot_type=attributes.get("shot type", ""),
        )

    def get_attributes(self, image_data: List[ImageData]) -> BattingAttributes:
        """
        Extract batting attributes from video frames

        Args:
            image_data: List of ImageData objects containing frames and their encodings

        Returns:
            BattingAttributes object containing the analysis
        """
        # Get VLM response
        response = self._get_attributes(image_data, self.ATTRIBUTE_PROMPT)

        # Parse and return attributes
        return self._parse_response(response)


class GeminiVideoAttributeExtractor(BaseVideoAttributeExtractor):
    """Gemini implementation of video attribute extractor"""

    def _initialize_client(self):
        return GeminiClient()

    def _get_attributes(self, image_data: List[ImageData], prompt: str) -> str:
        # Use PIL images directly
        contents = [self.SYSTEM_PROMPT] + [data.image for data in image_data] + [prompt]

        response = self.client.client.models.generate_content(
            model="gemini-2.0-flash-exp", contents=contents
        )
        return response.text


class ClaudeVideoAttributeExtractor(BaseVideoAttributeExtractor):
    """Claude implementation of video attribute extractor"""

    def _initialize_client(self):
        return ClaudeClient()

    def _get_attributes(self, image_data: List[ImageData], prompt: str) -> str:
        # Implementation will depend on Claude's specific API for handling images
        # This is a placeholder - needs to be implemented based on Claude's API
        raise NotImplementedError("Claude implementation pending")


class OpenAIVideoAttributeExtractor(BaseVideoAttributeExtractor):
    """OpenAI implementation of video attribute extractor"""

    def _initialize_client(self):
        return OpenAIClient()

    def _get_attributes(self, image_data: List[ImageData], prompt: str) -> str:
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "image_url": {"url": f"data:image/jpeg;base64,{data.encoding}"},
                    }
                    for data in image_data
                ]
                + [{"type": "text", "text": prompt}],
            },
        ]

        response = self.client.client.chat.completions.create(
            model="gpt-4-vision-preview", messages=messages, max_tokens=300
        )
        return response.choices[0].message.content
