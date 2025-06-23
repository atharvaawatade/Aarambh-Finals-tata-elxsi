from abc import ABC, abstractmethod
from enum import Enum
import numpy as np

class WeatherCondition(Enum):
    CLEAR = "Clear"
    RAINY = "Rainy"
    FOGGY = "Foggy"
    UNKNOWN = "Unknown"

class WeatherDetector(ABC):
    @abstractmethod
    def detect_weather(self, frame: np.ndarray) -> WeatherCondition:
        """
        Detects the weather condition from a given frame.
        """
        pass
