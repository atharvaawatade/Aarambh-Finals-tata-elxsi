"""
Helper utilities - PERFORMANCE OPTIMIZED
Ultra-fast drawing and formatting functions
"""

import cv2
import numpy as np
from typing import List, Dict, Any, Tuple

# Optimized color constants (BGR format)
RISK_COLORS = {
    'Critical': (0, 0, 255),    # Red
    'High': (0, 100, 255),      # Orange-Red  
    'Medium': (0, 165, 255),    # Orange
    'Low': (0, 255, 255),       # Yellow
    'None': (0, 255, 0),        # Green
}

def draw_detections(frame: np.ndarray, tracked_objects: List[Dict], collision_analysis: Dict) -> np.ndarray:
    """
    Lane-aware detection drawing with threat visualization
    """
    if not tracked_objects:
        return frame
    
    try:
        # Draw lane boundaries first
        lane_info = collision_analysis.get('lane_info')
        if lane_info:
            frame = draw_lane_boundaries(frame, lane_info)
        
        # Get threatening objects for special highlighting
        threatening_objects = [t for t in collision_analysis.get('threatening_objects', []) if 'object' in t]
        threat_ids = {t['object'].get('track_id') for t in threatening_objects}
        
        # Draw all tracked objects
        for obj in tracked_objects:
            bbox = obj.get('bbox', [0, 0, 0, 0])
            class_name = obj.get('class_name', 'object')
            track_id = obj.get('track_id', 0)
            
            # Determine color based on threat level
            if track_id in threat_ids:
                # Find this object's threat details
                threat_detail = next((t for t in threatening_objects if t['object'].get('track_id') == track_id), None)
                if threat_detail:
                    threat_type = threat_detail.get('threat_type', 'none')
                    if threat_type == 'same_lane':
                        color = (0, 0, 255)  # Red for same lane threats
                    elif threat_type == 'oncoming':
                        color = (0, 100, 255)  # Orange-red for oncoming
                    elif threat_type == 'lane_change':
                        color = (0, 165, 255)  # Orange for lane change
                    else:
                        color = (0, 255, 255)  # Yellow for other threats
                    thickness = 3
                else:
                    color = (0, 255, 0)  # Green for non-threats
                    thickness = 2
            else:
                color = (0, 255, 0)  # Green for non-threats
                thickness = 2
            
            # Draw bounding box
            x1, y1, x2, y2 = map(int, bbox)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
            
            # Enhanced label with threat info
            label = f"{class_name}"
            if track_id in threat_ids:
                threat_detail = next((t for t in threatening_objects if t['object'].get('track_id') == track_id), None)
                if threat_detail:
                    distance = threat_detail.get('distance', 0)
                    label += f" {distance:.1f}m"
                    threat_type = threat_detail.get('threat_type', '').replace('_', ' ').title()
                    if threat_type != 'None':
                        label += f" ({threat_type})"
            
            # Draw label with background for better visibility
            (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame, (x1, y1 - text_height - 10), (x1 + text_width, y1), color, -1)
            cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Draw lane change indicator
        if lane_info and lane_info.lane_change_detected:
            draw_lane_change_indicator(frame, lane_info.lane_change_direction)
        
        return frame
        
    except Exception as e:
        print(f"❌ Drawing error: {e}")
        return frame

def draw_primary_warning(frame: np.ndarray, warning_text: str, risk_level: str) -> np.ndarray:
    """
    Fast primary warning display
    """
    if not warning_text or risk_level == 'None' or not isinstance(warning_text, str):
        return frame
    
    try:
        height, width = frame.shape[:2]
        
        # Get warning color
        warning_color = RISK_COLORS.get(risk_level, (0, 255, 255))
        
        # Draw warning background (simplified)
        if risk_level in ['Critical', 'High']:
            # Draw warning rectangle
            warning_height = 80
            y_start = height // 2 - warning_height // 2
            cv2.rectangle(frame, (50, y_start), (width - 50, y_start + warning_height), 
                         warning_color, -1)
            
            # Draw warning text
            text_size = cv2.getTextSize(warning_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 2)[0]
            text_x = (width - text_size[0]) // 2
            text_y = y_start + warning_height // 2 + text_size[1] // 2
            
            cv2.putText(frame, warning_text, (text_x, text_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2, cv2.LINE_AA)
        
        return frame
        
    except Exception as e:
        print(f"❌ Warning drawing error: {e}")
        return frame

def format_detection_info(tracked_objects: List[Dict]) -> str:
    """
    Fast detection info formatting
    """
    if not tracked_objects:
        return "No objects detected"
    
    try:
        info_lines = []
        for i, obj in enumerate(tracked_objects[:3]):  # Limit to first 3 for speed
            class_name = obj.get('class_name', 'object')
            confidence = obj.get('confidence', 0.0)
            distance = obj.get('distance_estimate', 0.0)
            
            info_lines.append(f"{class_name}: {confidence:.1f} ({distance:.1f}m)")
        
        return "\n".join(info_lines)
        
    except Exception as e:
        return f"Error formatting info: {e}"

def draw_lane_boundaries(frame: np.ndarray, lane_info) -> np.ndarray:
    """
    Draw detected lane boundaries
    """
    try:
        if not lane_info or not lane_info.lane_boundaries:
            return frame
        
        # Draw lane boundaries
        for left_boundary, right_boundary in lane_info.lane_boundaries:
            # Draw left boundary
            if len(left_boundary) >= 2:
                cv2.line(frame, tuple(left_boundary[0].astype(int)), 
                        tuple(left_boundary[1].astype(int)), (255, 255, 0), 2)
            
            # Draw right boundary  
            if len(right_boundary) >= 2:
                cv2.line(frame, tuple(right_boundary[0].astype(int)), 
                        tuple(right_boundary[1].astype(int)), (255, 255, 0), 2)
        
        # Highlight ego lane
        height, width = frame.shape[:2]
        ego_center_x = width // 2
        cv2.circle(frame, (ego_center_x, height - 50), 10, (0, 255, 0), -1)
        cv2.putText(frame, "EGO", (ego_center_x - 15, height - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        return frame
    except Exception as e:
        print(f"❌ Lane drawing error: {e}")
        return frame

def draw_lane_change_indicator(frame: np.ndarray, direction: str) -> np.ndarray:
    """
    Draw lane change indicator
    """
    try:
        height, width = frame.shape[:2]
        
        # Position for indicator
        indicator_y = 50
        center_x = width // 2
        
        if direction == 'left':
            # Draw left arrow
            points = np.array([
                [center_x - 100, indicator_y],
                [center_x - 130, indicator_y - 15],
                [center_x - 130, indicator_y + 15]
            ], np.int32)
            cv2.fillPoly(frame, [points], (0, 165, 255))
            cv2.putText(frame, "CHANGING LEFT", (center_x - 80, indicator_y + 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
        
        elif direction == 'right':
            # Draw right arrow
            points = np.array([
                [center_x + 100, indicator_y],
                [center_x + 130, indicator_y - 15],
                [center_x + 130, indicator_y + 15]
            ], np.int32)
            cv2.fillPoly(frame, [points], (0, 165, 255))
            cv2.putText(frame, "CHANGING RIGHT", (center_x + 20, indicator_y + 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
        
        return frame
    except Exception as e:
        print(f"❌ Lane change indicator error: {e}")
        return frame

def calculate_simple_distance(bbox: List[int], class_name: str, frame_height: int) -> float:
    """
    Ultra-fast distance estimation
    """
    try:
        # Simple height-based estimation
        object_height = bbox[3] - bbox[1]
        if object_height <= 0:
            return 50.0
        
        # Simplified known heights
        known_heights = {
            'car': 1.5, 'truck': 2.8, 'person': 1.7,
            'motorcycle': 1.2, 'bicycle': 1.0
        }
        
        real_height = known_heights.get(class_name.lower(), 1.5)
        focal_length = frame_height * 0.8
        
        distance = (real_height * focal_length) / object_height
        return max(1.0, min(distance, 100.0))
        
    except:
        return 50.0


