"""
Decision Maker - PERFORMANCE OPTIMIZED
Simplified decision making for ultra-fast processing
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from enum import Enum

class WarningType(Enum):
    FORWARD_COLLISION = "Forward Collision Warning"
    LANE_DEPARTURE = "Lane Departure Warning"
    WEATHER_ALERT = "Weather Alert"

class DecisionMaker(ABC):
    @abstractmethod
    def make_decision(self, analysis_results: Dict[str, Any]) -> List[WarningType]:
        """
        Makes a decision based on the combined analysis results.
        """
        pass

class SimpleDecisionMaker(DecisionMaker):
    def make_decision(self, analysis_results: Dict[str, Any]) -> List[WarningType]:
        """
        Fast decision making based on risk level strings
        """
        warnings = []
        risk_level = analysis_results.get('risk_level', 'None')

        # Forward collision warning logic
        if risk_level in ['High', 'Critical']:
            warnings.append(WarningType.FORWARD_COLLISION)

        return warnings
    
    def get_warning_priority(self, risk_level: str) -> str:
        """Get the priority level of the warning"""
        return risk_level.upper() if risk_level else "NONE"
