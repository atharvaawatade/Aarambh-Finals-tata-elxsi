from abc import ABC, abstractmethod
from typing import List, Dict, Any

class AnalysisEngine(ABC):
    @abstractmethod
    def analyze_video(self, video_path: str) -> Dict[str, Any]:
        """
        Performs a full analysis of a video file and returns a report.
        """
        pass

    @abstractmethod
    def generate_annotated_video(self, video_path: str, output_path: str):
        """
        Processes a video and saves a new video with annotations.
        """
        pass
