from abc import ABC, abstractmethod
from typing import Optional
import os
from dotenv import load_dotenv


class VLMClient(ABC):
    """
    Base class for Vision Language Model clients.
    Handles API key management and client instantiation.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the VLM client.

        Args:
            api_key: Optional API key. If not provided, will attempt to load from environment variables.
        """
        load_dotenv()  # Load environment variables from .env file
        self.api_key = api_key or self._load_api_key()
        self.client = self._initialize_client()

    @property
    @abstractmethod
    def env_key_name(self) -> str:
        """
        Name of the environment variable containing the API key.
        Must be implemented by child classes.
        """
        pass

    def _load_api_key(self) -> str:
        """Load API key from environment variables"""
        api_key = os.getenv(self.env_key_name)
        if not api_key:
            raise ValueError(
                f"API key not found. Please set {self.env_key_name} in your environment or .env file"
            )
        return api_key

    @abstractmethod
    def _initialize_client(self):
        """
        Initialize the specific VLM client.
        Must be implemented by child classes.
        """
        pass


class GeminiClient(VLMClient):
    """Google's Gemini Pro Vision client"""

    @property
    def env_key_name(self) -> str:
        return "GEMINI_API_KEY"

    def _initialize_client(self):
        from google import genai

        client = genai.Client(api_key=self.api_key)
        return client


class ClaudeClient(VLMClient):
    """Anthropic's Claude client"""

    @property
    def env_key_name(self) -> str:
        return "ANTHROPIC_API_KEY"

    def _initialize_client(self):
        from anthropic import Anthropic

        return Anthropic(api_key=self.api_key)


class OpenAIClient(VLMClient):
    """OpenAI's GPT-4 Vision client"""

    @property
    def env_key_name(self) -> str:
        return "OPENAI_API_KEY"

    def _initialize_client(self):
        from openai import OpenAI

        return OpenAI(api_key=self.api_key)
