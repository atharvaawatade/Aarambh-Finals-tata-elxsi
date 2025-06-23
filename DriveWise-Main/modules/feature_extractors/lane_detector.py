from abc import ABC, abstractmethod
from typing import Any, List, Tuple, Optional, Dict
import numpy as np
import cv2

# Placeholder for lane data
class Lane:
    def __init__(self, line_segments: Any, lane_id: int = 0):
        self.line_segments = line_segments
        self.lane_id = lane_id
        self.left_boundary = None
        self.right_boundary = None
        self.center_line = None
        
    def __repr__(self):
        return f"Lane(lane_id={self.lane_id}, line_segments={len(self.line_segments) if self.line_segments else 0})"

class LaneInfo:
    """Complete lane information for the current frame"""
    def __init__(self):
        self.lanes: List[Lane] = []
        self.ego_lane_id: int = 0  # Which lane our vehicle is in
        self.lane_boundaries: List[Tuple[np.ndarray, np.ndarray]] = []  # (left_line, right_line) pairs
        self.lane_change_detected: bool = False
        self.lane_change_direction: str = "none"  # "left", "right", "none"
        self.frame_width: int = 0
        self.frame_height: int = 0

class LaneDetector(ABC):
    @abstractmethod
    def detect_lanes(self, frame: np.ndarray) -> LaneInfo:
        """
        Detects lanes in a given frame and returns comprehensive lane information.
        """
        pass

class SimpleLaneDetector(LaneDetector):
    """
    Simple lane detector using Hough lines and basic lane logic
    """
    
    def __init__(self):
        # Lane detection parameters
        self.canny_low = 50
        self.canny_high = 150
        self.hough_threshold = 50
        self.min_line_length = 100
        self.max_line_gap = 50
        
        # Lane tracking
        self.previous_lanes = None
        self.ego_lane_history = []
        self.lane_change_threshold = 30  # pixels
        
    def detect_lanes(self, frame: np.ndarray) -> LaneInfo:
        """Detect lanes and return comprehensive lane information"""
        lane_info = LaneInfo()
        lane_info.frame_height, lane_info.frame_width = frame.shape[:2]
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Focus on lower half of frame (road area)
        height = gray.shape[0]
        roi_start = height // 2
        gray_roi = gray[roi_start:, :]
        
        # Edge detection
        edges = cv2.Canny(gray_roi, self.canny_low, self.canny_high)
        
        # Hough line detection
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=self.hough_threshold,
            minLineLength=self.min_line_length,
            maxLineGap=self.max_line_gap
        )
        
        if lines is not None:
            # Adjust line coordinates to full frame
            adjusted_lines = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                adjusted_lines.append([x1, y1 + roi_start, x2, y2 + roi_start])
            
            # Process lines to identify lanes
            lane_info = self._process_lane_lines(adjusted_lines, lane_info)
        
        # Detect ego vehicle position and lane changes
        self._detect_ego_position(lane_info)
        
        return lane_info
    
    def _process_lane_lines(self, lines: List, lane_info: LaneInfo) -> LaneInfo:
        """Process detected lines to identify lane boundaries"""
        if not lines:
            return lane_info
        
        left_lines = []
        right_lines = []
        center_x = lane_info.frame_width // 2
        
        for line in lines:
            x1, y1, x2, y2 = line
            
            # Calculate slope to filter vertical lines
            if x2 - x1 == 0:
                continue
            slope = (y2 - y1) / (x2 - x1)
            
            # Filter lines with reasonable slopes for lane markings
            if abs(slope) < 0.3 or abs(slope) > 3.0:
                continue
            
            # Determine if line is on left or right side
            line_center_x = (x1 + x2) / 2
            if line_center_x < center_x:
                left_lines.append(line)
            else:
                right_lines.append(line)
        
        # Create lane boundaries
        if left_lines and right_lines:
            # Find the rightmost left line and leftmost right line
            left_boundary = max(left_lines, key=lambda l: (l[0] + l[2]) / 2)
            right_boundary = min(right_lines, key=lambda l: (l[0] + l[2]) / 2)
            
            lane_info.lane_boundaries.append((
                np.array([left_boundary[:2], left_boundary[2:]]),
                np.array([right_boundary[:2], right_boundary[2:]])
            ))
            
            # Create a lane object
            lane = Lane(line_segments=[left_boundary, right_boundary], lane_id=0)
            lane.left_boundary = left_boundary
            lane.right_boundary = right_boundary
            lane_info.lanes.append(lane)
        
        return lane_info
    
    def _detect_ego_position(self, lane_info: LaneInfo):
        """Detect ego vehicle position and lane changes"""
        if not lane_info.lane_boundaries:
            return
        
        # Assume ego vehicle is at bottom center of frame
        ego_x = lane_info.frame_width // 2
        
        # Check which lane ego vehicle is in
        for i, (left_boundary, right_boundary) in enumerate(lane_info.lane_boundaries):
            left_x = np.mean([left_boundary[0][0], left_boundary[1][0]])
            right_x = np.mean([right_boundary[0][0], right_boundary[1][0]])
            
            if left_x <= ego_x <= right_x:
                lane_info.ego_lane_id = i
                break
        
        # Track ego position for lane change detection
        self.ego_lane_history.append(ego_x)
        if len(self.ego_lane_history) > 10:  # Keep last 10 frames
            self.ego_lane_history.pop(0)
        
        # Detect lane changes
        if len(self.ego_lane_history) >= 5:
            recent_movement = self.ego_lane_history[-1] - self.ego_lane_history[-5]
            if abs(recent_movement) > self.lane_change_threshold:
                lane_info.lane_change_detected = True
                lane_info.lane_change_direction = "right" if recent_movement > 0 else "left"
    
    def get_vehicle_lane(self, vehicle_bbox: List[float], lane_info: LaneInfo) -> int:
        """Determine which lane a vehicle is in based on its bounding box"""
        if not lane_info.lane_boundaries:
            return 0  # Default lane
        
        # Use vehicle center x-coordinate
        vehicle_center_x = (vehicle_bbox[0] + vehicle_bbox[2]) / 2
        
        # Check which lane the vehicle is in
        for i, (left_boundary, right_boundary) in enumerate(lane_info.lane_boundaries):
            left_x = np.mean([left_boundary[0][0], left_boundary[1][0]])
            right_x = np.mean([right_boundary[0][0], right_boundary[1][0]])
            
            if left_x <= vehicle_center_x <= right_x:
                return i
        
        # If not in any detected lane, determine based on position
        center_x = lane_info.frame_width // 2
        if vehicle_center_x < center_x:
            return -1  # Left of ego lane (oncoming traffic)
        else:
            return 1   # Right of ego lane
