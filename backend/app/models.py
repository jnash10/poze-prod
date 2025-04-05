from pydantic import BaseModel, Field
from typing import List, Optional


# Mirror the structure of your attributes object
class ExtractedAttributes(BaseModel):
    age: Optional[str] = None
    experience_level: Optional[str] = None
    ball_length: Optional[str] = None
    shot_type: Optional[str] = None
    # Add any other fields your attribute_extractor returns


# Mirror the structure of your feedback object
class GeneratedFeedback(BaseModel):
    stance: List[str] = Field(default_factory=list)
    weight_transfer: List[str] = Field(default_factory=list)
    shot_technique: List[str] = Field(default_factory=list)
    # Add other feedback categories if they exist


# Model for SSE event data
class SSEventData(BaseModel):
    event: str
    data: dict | list | str | None = None  # Flexible data part
