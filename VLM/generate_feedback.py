from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
from .clients import GeminiClient, ClaudeClient, OpenAIClient
from .get_attributes import BattingAttributes
from .helpers import ImageData


@dataclass
class BattingFeedback:
    """Dataclass to store structured batting feedback"""

    stance: List[str]
    weight_transfer: List[str]
    shot_technique: List[str]


class BaseFeedbackGenerator(ABC):
    """Base class for generating personalized batting feedback using VLM"""

    SYSTEM_PROMPT = """You are an experienced cricket coach who provides personalized feedback to help players improve their batting technique. 
    Your feedback should be specific, actionable, and focused on helping the player reach the next skill level."""

    FEEDBACK_PROMPT = """Based on the player's profile and the video frames shown:
    - Age: {age}
    - Current Level: {experience_level}
    - Ball Length: {ball_length}
    - Shot Played: {shot_type}

    Provide detailed feedback focusing only on the most critical aspects needed to progress to the next level.
    Consider the player's current experience level when providing feedback. Give feedback to help the player progress to the next level .
    Experience level: beginner(just starting to learn cricket), enthusiast(knows the basics and has practised), intermediate(University level), advanced(semi-professional), expert(professional level)
    Reference specific visual observations from the video frames in your feedback.
    
    Structure your response exactly as follows:
    Stance:
    - [List 2-3 key technical observations from the video]
    
    Weight transfer:
    - [List 2-3 specific areas to focus on]
    
    Shot Technique:
    - [List 2-3 key skills/improvements needed to progress]
    """

    def __init__(self):
        """Initialize the feedback generator"""
        self.client = self._initialize_client()

    @abstractmethod
    def _initialize_client(self):
        """Initialize the specific VLM client"""
        pass

    @abstractmethod
    def _generate_feedback(
        self, attributes: BattingAttributes, image_data: List[ImageData]
    ) -> str:
        """
        Generate feedback using the VLM

        Args:
            attributes: BattingAttributes object containing player analysis
            image_data: List of ImageData objects containing frames and their encodings

        Returns:
            Raw response from VLM
        """
        pass

    def _parse_feedback(self, response: str) -> BattingFeedback:
        """Parse VLM response into structured feedback"""
        feedback_dict = {"stance": [], "weight_transfer": [], "shot_technique": []}
        # print(response)

        # Find the sections using bold markers or section headers
        sections = {
            "stance": ["Stance:", "**Stance:**"],
            "weight_transfer": [
                "Weight Transfer:",
                "Weight transfer:",
                "**Weight transfer:**",
                "**Weight Transfer:**",
            ],
            "shot_technique": ["Shot Technique:", "**Shot Technique:**"],
        }

        lines = response.split("\n")
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if this line is a section header
            for section, headers in sections.items():
                if any(line == header for header in headers):
                    current_section = section
                    break

            # If we're in a section and line starts with a bullet point, add it
            if current_section and line.startswith(("-", "*")):
                feedback_dict[current_section].append(line[2:])

        return BattingFeedback(
            stance=feedback_dict["stance"],
            weight_transfer=feedback_dict["weight_transfer"],
            shot_technique=feedback_dict["shot_technique"],
        )

    def generate_feedback(
        self, attributes: BattingAttributes, image_data: List[ImageData]
    ) -> BattingFeedback:
        """
        Generate structured feedback based on attributes and frames

        Args:
            attributes: BattingAttributes object containing player analysis
            image_data: List of ImageData objects containing frames and their encodings

        Returns:
            BattingFeedback object containing structured feedback
        """
        response = self._generate_feedback(attributes, image_data)
        return self._parse_feedback(response)


class GeminiFeedbackGenerator(BaseFeedbackGenerator):
    """Gemini implementation of feedback generator"""

    def _initialize_client(self):
        return GeminiClient()

    def _generate_feedback(
        self, attributes: BattingAttributes, image_data: List[ImageData]
    ) -> str:
        prompt = self.FEEDBACK_PROMPT.format(
            age=attributes.age,
            experience_level=attributes.experience_level,
            ball_length=attributes.ball_length,
            shot_type=attributes.shot_type,
        )

        # Use PIL images directly
        contents = [self.SYSTEM_PROMPT] + [data.image for data in image_data] + [prompt]

        response = self.client.client.models.generate_content(
            model="gemini-2.0-flash-exp", contents=contents
        )
        return response.text


class ClaudeFeedbackGenerator(BaseFeedbackGenerator):
    """Claude implementation of feedback generator"""

    def _initialize_client(self):
        return ClaudeClient()

    def _generate_feedback(
        self, attributes: BattingAttributes, image_data: List[ImageData]
    ) -> str:
        prompt = self.FEEDBACK_PROMPT.format(
            age=attributes.age,
            experience_level=attributes.experience_level,
            ball_length=attributes.ball_length,
            shot_type=attributes.shot_type,
        )

        # Claude implementation for handling images would go here
        raise NotImplementedError("Claude implementation pending")


class OpenAIFeedbackGenerator(BaseFeedbackGenerator):
    """OpenAI implementation of feedback generator"""

    def _initialize_client(self):
        return OpenAIClient()

    def _generate_feedback(
        self, attributes: BattingAttributes, image_data: List[ImageData]
    ) -> str:
        prompt = self.FEEDBACK_PROMPT.format(
            age=attributes.age,
            experience_level=attributes.experience_level,
            ball_length=attributes.ball_length,
            shot_type=attributes.shot_type,
        )

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
            model="gpt-4-vision-preview", messages=messages, max_tokens=1000
        )
        return response.choices[0].message.content
