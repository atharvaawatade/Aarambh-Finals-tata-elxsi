from abc import ABC, abstractmethod
import cv2
import numpy as np

class FrameProcessor(ABC):
    @abstractmethod
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocesses a single frame.
        """
        pass

class BasicFrameProcessor(FrameProcessor):
    def __init__(self, target_size: tuple[int, int] = (640, 480)):
        self.target_size = target_size

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Resizes the frame to the target size.
        """
        if frame is None:
            return None
        return cv2.resize(frame, self.target_size)
