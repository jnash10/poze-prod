# Poze

## Cricket Coaching Assistance
Delivered to your smartphone for free, powered by VLMs

## Usage

### Basic Usage

```python
from VLM.helpers import VideoProcessor
from VLM.get_attributes import GeminiVideoAttributeExtractor
from VLM.generate_feedback import GeminiFeedbackGenerator

# Initialize components
video_processor = VideoProcessor()
attribute_extractor = GeminiVideoAttributeExtractor()
feedback_generator = GeminiFeedbackGenerator()

# Process video and extract frames
# n_frames specifies how many frames to extract from the video
frames = video_processor.process_video("path/to/your/video.mp4", n_frames=10)

# Get batting attributes
attributes = attribute_extractor.get_attributes(frames)

# Print extracted attributes
print(f"Player Age: {attributes.age}")
print(f"Experience Level: {attributes.experience_level}")
print(f"Ball Length: {attributes.ball_length}")
print(f"Shot Type: {attributes.shot_type}")

# Generate detailed feedback
feedback = feedback_generator.generate_feedback(attributes, frames)

# Access structured feedback
print("\nStance Feedback:")
for point in feedback.stance:
    print(f"- {point}")

print("\nWeight Transfer Feedback:")
for point in feedback.weight_transfer:
    print(f"- {point}")

print("\nShot Technique Feedback:")
for point in feedback.shot_technique:
    print(f"- {point}")
```

### Components

#### 1. VideoProcessor
- Handles video frame extraction and processing
- Automatically resizes frames while maintaining aspect ratio
- Provides both PIL Image objects and base64 encodings
- Default target size: 512x512 pixels

```python
from VLM.helpers import VideoProcessor

processor = VideoProcessor(target_size=(512, 512))  # Optional custom size
frames = processor.process_video("video.mp4", n_frames=10)
```

#### 2. Attribute Extractors
Available implementations:
- `GeminiVideoAttributeExtractor` (Recommended)
- `OpenAIVideoAttributeExtractor`
- `ClaudeVideoAttributeExtractor` (Coming soon)

Extracts the following attributes:
- Player's approximate age
- Experience level (beginner/enthusiast/intermediate/advanced/expert)
- Ball length (short/medium/full)
- Shot type (Backfoot defence/Frontfoot defence/Drive/Miscellaneous)

```python
from VLM.get_attributes import GeminiVideoAttributeExtractor

extractor = GeminiVideoAttributeExtractor()
attributes = extractor.get_attributes(frames)
```

#### 3. Feedback Generators
Available implementations:
- `GeminiFeedbackGenerator` (Recommended)
- `OpenAIFeedbackGenerator`
- `ClaudeFeedbackGenerator` (Coming soon)

Generates structured feedback in three categories:
- Stance analysis
- Weight transfer assessment
- Shot technique recommendations

```python
from VLM.generate_feedback import GeminiFeedbackGenerator

generator = GeminiFeedbackGenerator()
feedback = generator.generate_feedback(attributes, frames)
```

### Advanced Usage

#### Custom Frame Count
Adjust the number of frames extracted for analysis:
```python
# Extract more frames for detailed analysis
frames = video_processor.process_video("video.mp4", n_frames=20)

# Extract fewer frames for faster processing
frames = video_processor.process_video("video.mp4", n_frames=5)
```

#### Working with Different VLM Providers
Choose between different VLM providers based on your needs:
```python
# Using OpenAI
from VLM.get_attributes import OpenAIVideoAttributeExtractor
from VLM.generate_feedback import OpenAIFeedbackGenerator

openai_extractor = OpenAIVideoAttributeExtractor()
openai_generator = OpenAIFeedbackGenerator()
```

### Notes
- Ensure your video is in a common format (MP4 recommended)
- For best results, ensure the video clearly shows the batting technique
- The default frame count (10) works well for most videos
- The Gemini implementation is currently recommended for best results