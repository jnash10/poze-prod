from dataclasses import dataclass
from typing import List, Union, Tuple
import cv2
from PIL import Image
import base64
import io
import numpy as np


@dataclass
class ImageData:
    image: Image.Image
    encoding: str


class VideoProcessor:
    def __init__(self, target_size: Tuple[int, int] = (512, 512)):
        """
        Initialize VideoProcessor with target size for resizing

        Args:
            target_size: Tuple of (width, height) for resizing images
        """
        self.target_size = target_size

    def _resize_image(self, image: Image.Image) -> Image.Image:
        """
        Resize image while maintaining aspect ratio

        Args:
            image: PIL Image to resize

        Returns:
            Resized PIL Image
        """
        # Calculate aspect ratio
        aspect_ratio = image.width / image.height

        if aspect_ratio > 1:
            # Image is wider than tall
            new_width = self.target_size[0]
            new_height = int(new_width / aspect_ratio)
        else:
            # Image is taller than wide
            new_height = self.target_size[1]
            new_width = int(new_height * aspect_ratio)

        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def extract_frames(self, video_path: str, n_frames: int) -> List[Image.Image]:
        """
        Extract n_frames uniformly from a video file

        Args:
            video_path: Path to the video file
            n_frames: Number of frames to extract

        Returns:
            List of PIL Image objects
        """
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Calculate frame indices to extract
        indices = np.linspace(0, total_frames - 1, n_frames, dtype=int)
        frames = []

        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Convert to PIL Image
                pil_image = Image.fromarray(rgb_frame)
                # resize image
                resized_image = self._resize_image(pil_image)

                frames.append(resized_image)

        cap.release()
        return frames

    def encode_image(
        self, image: Union[Image.Image, List[Image.Image]]
    ) -> Union[str, List[str]]:
        """
        Encode PIL Image or list of PIL Images to base64 string(s)

        Args:
            image: Single PIL Image or list of PIL Images

        Returns:
            Single base64 string or list of base64 strings
        """
        if isinstance(image, list):
            return [self._encode_single_image(img) for img in image]
        return self._encode_single_image(image)

    def _encode_single_image(self, image: Image.Image) -> str:
        """Helper method to encode a single PIL Image"""
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    def process_video(self, video_path: str, n_frames: int) -> List[ImageData]:
        """
        Extract frames from video and encode them

        Args:
            video_path: Path to the video file
            n_frames: Number of frames to extract

        Returns:
            List of ImageData objects containing both PIL Image and base64 encoding
        """
        frames = self.extract_frames(video_path, n_frames)
        encodings = self.encode_image(frames)

        return [
            ImageData(image=frame, encoding=encoding)
            for frame, encoding in zip(frames, encodings)
        ]
