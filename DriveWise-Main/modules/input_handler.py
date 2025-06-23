from abc import ABC, abstractmethod
import cv2
import numpy as np

class InputHandler(ABC):
    @abstractmethod
    def get_frame(self) -> np.ndarray | None:
        """
        Gets the next frame from the input source.
        Returns None if no more frames are available.
        """
        pass

    @abstractmethod
    def release(self):
        """
        Releases the input source.
        """
        pass

class VideoInput(InputHandler):
    def __init__(self, video_path: str):
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise IOError(f"Cannot open video file: {video_path}")

    def get_frame(self) -> np.ndarray | None:
        ret, frame = self.cap.read()
        return frame if ret else None

    def release(self):
        self.cap.release()

class CameraInput(InputHandler):
    def __init__(self, camera_index: int = 0):
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise IOError(f"Cannot open camera with index: {camera_index}")

    def get_frame(self) -> np.ndarray | None:
        ret, frame = self.cap.read()
        return frame if ret else None

    def release(self):
        self.cap.release()
