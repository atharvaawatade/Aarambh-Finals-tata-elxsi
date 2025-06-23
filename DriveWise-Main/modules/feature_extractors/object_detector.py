from abc import ABC, abstractmethod
from typing import List, Any
import numpy as np

# A simple data class to hold detection results
class Detection:
    def __init__(self, box: List[int], score: float, class_id: int, class_name: str):
        self.box = box  # [x1, y1, x2, y2]
        self.score = score
        self.class_id = class_id
        self.class_name = class_name

    def __repr__(self):
        return f"Detection(box={self.box}, score={self.score:.2f}, class_name='{self.class_name}')"

class ObjectDetector(ABC):
    @abstractmethod
    def detect_objects(self, frame: np.ndarray) -> List[Detection]:
        """
        Detects objects in a given frame.
        """
        pass
