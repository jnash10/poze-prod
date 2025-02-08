from VLM.helpers import VideoProcessor
from VLM.get_attributes import GeminiVideoAttributeExtractor
from VLM.generate_feedback import GeminiFeedbackGenerator


# First get attributes and process video
video_processor = VideoProcessor()
image_data = video_processor.process_video("data/112.mp4", n_frames=10)

attribute_extractor = GeminiVideoAttributeExtractor()
attributes = attribute_extractor.get_attributes(image_data)

print(f"Player Age: {attributes.age}")
print(f"Experience Level: {attributes.experience_level}")
print(f"Ball Length: {attributes.ball_length}")
print(f"Shot Type: {attributes.shot_type}")

# Generate feedback using processed frames and attributes
feedback_generator = GeminiFeedbackGenerator()
feedback = feedback_generator.generate_feedback(attributes, image_data)

# Access structured feedback
print("\nStance:")
for point in feedback.stance:
    print(f"- {point}")

print("\nWeight Transfer:")
for point in feedback.weight_transfer:
    print(f"- {point}")

print("\nShot Technique:")
for point in feedback.shot_technique:
    print(f"- {point}")
