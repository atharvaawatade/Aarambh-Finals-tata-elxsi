"""
Kalman Tracker Plugin - PERFORMANCE OPTIMIZED
Ultra-fast object tracking for competition
"""

import numpy as np
import cv2
from typing import List, Dict, Any, Optional
from scipy.optimize import linear_sum_assignment
import time

class FastKalmanFilter:
    """Simplified Kalman filter for maximum speed"""
    
    def __init__(self, bbox: List[int]):
        # State: [x, y, vx, vy] - position and velocity
        self.state = np.array([
            (bbox[0] + bbox[2]) / 2,  # center x
            (bbox[1] + bbox[3]) / 2,  # center y
            0,  # velocity x
            0   # velocity y
        ], dtype=np.float32)
        
        # Simplified covariance matrix
        self.P = np.eye(4, dtype=np.float32) * 1000
        
        # Simplified transition matrix (constant velocity model)
        self.F = np.array([
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)
        
        # Measurement matrix (observe position only)
        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ], dtype=np.float32)
        
        # Simplified noise matrices
        self.Q = np.eye(4, dtype=np.float32) * 1
        self.R = np.eye(2, dtype=np.float32) * 100
        
        self.bbox = bbox
        self.age = 0
        self.hits = 1
        self.time_since_update = 0
    
    def predict(self):
        """Fast prediction step"""
        self.state = self.F @ self.state
        self.P = self.F @ self.P @ self.F.T + self.Q
        self.age += 1
        self.time_since_update += 1
        return self.state[:2]  # Return predicted position
    
    def update(self, bbox: List[int]):
        """Fast update step"""
        # Measurement (center of bounding box)
        z = np.array([
            (bbox[0] + bbox[2]) / 2,
            (bbox[1] + bbox[3]) / 2
        ], dtype=np.float32)
        
        # Innovation
        y = z - (self.H @ self.state)
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # Update state and covariance
        self.state = self.state + K @ y
        self.P = (np.eye(4) - K @ self.H) @ self.P
        
        # Update bbox and tracking info
        self.bbox = bbox
        self.hits += 1
        self.time_since_update = 0
    
    def get_bbox(self) -> List[int]:
        """Get current bounding box"""
        if self.time_since_update > 0:
            # Predict bbox based on current state
            cx, cy = self.state[0], self.state[1]
            w = self.bbox[2] - self.bbox[0]
            h = self.bbox[3] - self.bbox[1]
            return [int(cx - w/2), int(cy - h/2), int(cx + w/2), int(cy + h/2)]
        return self.bbox

class KalmanTracker:
    """Fast multi-object tracker using simplified Kalman filters"""
    
    def __init__(self):
        self.trackers = []
        self.next_id = 1
        self.max_age = 5  # Reduced for speed
        self.min_hits = 2  # Reduced for speed
        self.iou_threshold = 0.3
        
        # Performance tracking
        self.frame_count = 0
        self.tracking_times = []
    
    def update(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fast tracking update
        
        Args:
            detections: List of detection dictionaries with 'bbox', 'confidence', 'class_name'
            
        Returns:
            List of tracked object dictionaries
        """
        start_time = time.perf_counter()
        
        # Predict all existing trackers
        predicted_bboxes = []
        for tracker in self.trackers:
            predicted_pos = tracker.predict()
            predicted_bboxes.append(tracker.get_bbox())
        
        # Convert detections to bboxes for matching
        detection_bboxes = [det['bbox'] for det in detections]
        
        # Fast assignment using IoU
        if len(self.trackers) > 0 and len(detection_bboxes) > 0:
            matches, unmatched_dets, unmatched_trks = self._fast_associate(
                detection_bboxes, predicted_bboxes
            )
        else:
            matches = []
            unmatched_dets = list(range(len(detections)))
            unmatched_trks = list(range(len(self.trackers)))
        
        # Update matched trackers
        for m in matches:
            det_idx, trk_idx = m
            self.trackers[trk_idx].update(detections[det_idx]['bbox'])
        
        # Create new trackers for unmatched detections
        for det_idx in unmatched_dets:
            if detections[det_idx]['confidence'] > 0.5:  # Only track high-confidence detections
                new_tracker = FastKalmanFilter(detections[det_idx]['bbox'])
                new_tracker.id = self.next_id
                new_tracker.class_name = detections[det_idx]['class_name']
                new_tracker.confidence = detections[det_idx]['confidence']
                self.trackers.append(new_tracker)
                self.next_id += 1
        
        # Remove old trackers
        self.trackers = [t for t in self.trackers if t.time_since_update <= self.max_age]
        
        # Generate output (only confirmed tracks)
        tracked_objects = []
        for tracker in self.trackers:
            if tracker.hits >= self.min_hits or tracker.time_since_update == 0:
                bbox = tracker.get_bbox()
                
                # Calculate simple velocity
                vx, vy = tracker.state[2], tracker.state[3]
                speed_pixels_per_frame = np.sqrt(vx*vx + vy*vy)
                
                tracked_obj = {
                    'track_id': tracker.id,
                    'bbox': bbox,
                    'class_name': getattr(tracker, 'class_name', 'object'),
                    'confidence': getattr(tracker, 'confidence', 1.0),
                    'center': [(bbox[0] + bbox[2]) // 2, (bbox[1] + bbox[3]) // 2],
                    'velocity': {'vx': float(vx), 'vy': float(vy)},
                    'speed': float(speed_pixels_per_frame * 2.0),  # Rough conversion to km/h
                    'age': tracker.age,
                    'hits': tracker.hits,
                    'area': (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                }
                tracked_objects.append(tracked_obj)
        
        # Performance tracking
        tracking_time = (time.perf_counter() - start_time) * 1000  # ms
        self.tracking_times.append(tracking_time)
        if len(self.tracking_times) > 50:
            self.tracking_times = self.tracking_times[-50:]
        
        self.frame_count += 1
        
        return tracked_objects
    
    def _fast_associate(self, detections: List[List[int]], trackers: List[List[int]]) -> tuple:
        """Fast association using IoU with Hungarian algorithm"""
        if len(trackers) == 0:
            return [], list(range(len(detections))), []
        
        # Compute IoU matrix
        iou_matrix = np.zeros((len(detections), len(trackers)), dtype=np.float32)
        
        for d_idx, det_bbox in enumerate(detections):
            for t_idx, trk_bbox in enumerate(trackers):
                iou_matrix[d_idx, t_idx] = self._calculate_iou_fast(det_bbox, trk_bbox)
        
        # Use Hungarian algorithm for optimal assignment
        if min(iou_matrix.shape) > 0:
            # Convert to cost matrix (1 - IoU)
            cost_matrix = 1 - iou_matrix
            det_indices, trk_indices = linear_sum_assignment(cost_matrix)
            
            # Filter matches by IoU threshold
            matches = []
            for d_idx, t_idx in zip(det_indices, trk_indices):
                if iou_matrix[d_idx, t_idx] >= self.iou_threshold:
                    matches.append([d_idx, t_idx])
            
            # Find unmatched detections and trackers
            matched_det_indices = set(m[0] for m in matches)
            matched_trk_indices = set(m[1] for m in matches)
            
            unmatched_dets = [i for i in range(len(detections)) if i not in matched_det_indices]
            unmatched_trks = [i for i in range(len(trackers)) if i not in matched_trk_indices]
            
            return matches, unmatched_dets, unmatched_trks
        else:
            return [], list(range(len(detections))), list(range(len(trackers)))
    
    def _calculate_iou_fast(self, bbox1: List[int], bbox2: List[int]) -> float:
        """Fast IoU calculation"""
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])
        
        if x2 <= x1 or y2 <= y1:
            return 0.0
        
        intersection = (x2 - x1) * (y2 - y1)
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get tracking performance statistics"""
        if not self.tracking_times:
            return {'avg_tracking_time_ms': 0.0, 'active_tracks': len(self.trackers)}
        
        return {
            'avg_tracking_time_ms': np.mean(self.tracking_times),
            'active_tracks': len(self.trackers),
            'frames_processed': self.frame_count,
            'min_tracking_time_ms': np.min(self.tracking_times),
            'max_tracking_time_ms': np.max(self.tracking_times)
        }

# Factory function for plugin system
def create_tracker(**kwargs) -> KalmanTracker:
    """Factory function to create Kalman tracker"""
    return KalmanTracker()
