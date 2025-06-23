from abc import ABC, abstractmethod
from enum import Enum
from modules.feature_extractors.lane_detector import Lane

class LaneDepartureRisk(Enum):
    NONE = "No Departure"
    LEFT_DEPARTURE = "Left Lane Departure"
    RIGHT_DEPARTURE = "Right Lane Departure"

class LaneDepartureAnalyzer(ABC):
    @abstractmethod
    def analyze_lanes(self, lanes: Lane | None) -> LaneDepartureRisk:
        """
        Analyzes lane data to detect lane departure.
        """
        pass
