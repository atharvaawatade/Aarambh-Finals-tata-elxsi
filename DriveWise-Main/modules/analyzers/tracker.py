from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import numpy as np
import time
import math
from modules.feature_extractors.object_detector import Detection
import config

class TrackedObject:
    def __init__(self, box: List[int], track_id: int, class_name: str, timestamp: float = None):
        self.box = box  # [x1, y1, x2, y2]
        self.track_id = track_id
        self.class_name = class_name
        self.timestamp = timestamp if timestamp else time.time()
        
        # Enhanced tracking features
        self.position_history = []  # List of (timestamp, center_x, center_y)
        self.velocity = np.array([0.0, 0.0])  # [vx, vy] in pixels/sec
        self.acceleration = np.array([0.0, 0.0])  # [ax, ay] in pixels/sec²
        
        # Physical properties
        self.distance_estimate = 0.0  # estimated distance in meters
        self.real_world_velocity = np.array([0.0, 0.0])  # [vx, vy] in m/s
        self.speed = 0.0  # magnitude of velocity in km/h
        self.time_to_collision = float('inf')  # time to collision in seconds
        
        # Risk assessment
        self.risk_level = "None"
        self.confidence = 1.0  # Tracking confidence
        self.age = 0  # Number of frames this object has been tracked
        
        # Calculate initial center and properties
        center_x = (box[0] + box[2]) / 2
        center_y = (box[1] + box[3]) / 2
        self.position_history.append((self.timestamp, center_x, center_y))
        
        # Initialize distance and risk
        self._estimate_distance()
        self._assess_risk()
    
    def update_position(self, new_box: List[int], timestamp: float = None):
        """Update the object's position with advanced motion analysis"""
        if timestamp is None:
            timestamp = time.time()
            
        self.box = new_box
        self.age += 1
        center_x = (new_box[0] + new_box[2]) / 2
        center_y = (new_box[1] + new_box[3]) / 2
        
        # Add to position history
        self.position_history.append((timestamp, center_x, center_y))
        
        # Maintain reasonable history length
        max_history = config.TRACK_HISTORY_LENGTH
        if len(self.position_history) > max_history:
            self.position_history = self.position_history[-max_history:]
        
        # Calculate motion properties
        if len(self.position_history) >= 2:
            self._calculate_velocity_and_acceleration()
        
        # Update physical properties
        self._estimate_distance()
        self._calculate_real_world_motion()
        self._calculate_time_to_collision()
        self._assess_risk()
    
    def _calculate_velocity_and_acceleration(self):
        """Calculate velocity and acceleration using smoothed derivatives"""
        if len(self.position_history) < 2:
            return
        
        # Use last few points for smoothing
        n_points = min(3, len(self.position_history))
        recent_history = self.position_history[-n_points:]
        
        if len(recent_history) >= 2:
            # Calculate velocity (pixels/second)
            t1, x1, y1 = recent_history[-2]
            t2, x2, y2 = recent_history[-1]
            dt = t2 - t1
            
            if dt > 0:
                new_velocity = np.array([(x2 - x1) / dt, (y2 - y1) / dt])
                
                # Smooth velocity with previous estimate
                alpha = 0.3  # Smoothing factor
                self.velocity = alpha * new_velocity + (1 - alpha) * self.velocity
        
        # Calculate acceleration if we have velocity history
        if len(self.position_history) >= 3:
            t1, _, _ = self.position_history[-3]
            t2, _, _ = self.position_history[-2]
            t3, _, _ = self.position_history[-1]
            
            dt1 = t2 - t1
            dt2 = t3 - t2
            
            if dt1 > 0 and dt2 > 0:
                # Simple finite difference for acceleration
                v1 = np.array([(self.position_history[-2][1] - self.position_history[-3][1]) / dt1,
                              (self.position_history[-2][2] - self.position_history[-3][2]) / dt1])
                v2 = self.velocity
                
                self.acceleration = (v2 - v1) / dt2
    
    def _estimate_distance(self):
        """Enhanced distance estimation using multiple methods"""
        box_height = self.box[3] - self.box[1]
        box_width = self.box[2] - self.box[0]
        
        # Get object dimensions from enhanced config
        obj_data = config.KNOWN_OBJECT_SIZES.get(
            self.class_name.lower(), 
            config.KNOWN_OBJECT_SIZES.get('person', {'height': 1.7, 'width': 0.5, 'length': 0.3})
        )
        
        real_height = obj_data['height']
        real_width = obj_data['width']
        
        # Method 1: Height-based distance estimation
        distance_from_height = float('inf')
        if box_height > 0:
            distance_from_height = (real_height * config.CAMERA_FOCAL_LENGTH) / box_height
        
        # Method 2: Width-based distance estimation  
        distance_from_width = float('inf')
        if box_width > 0:
            distance_from_width = (real_width * config.CAMERA_FOCAL_LENGTH) / box_width
        
        # Method 3: Area-based estimation (more stable)
        box_area = box_height * box_width
        real_area = real_height * real_width
        distance_from_area = float('inf')
        if box_area > 0:
            # Simplified area-based distance (assumes frontal view)
            distance_from_area = config.CAMERA_FOCAL_LENGTH * math.sqrt(real_area / box_area)
        
        # Combine estimates with weights (height is usually most reliable)
        distances = [d for d in [distance_from_height, distance_from_width, distance_from_area] if d != float('inf')]
        
        if distances:
            # Weighted average (prefer height-based estimate)
            weights = [0.5, 0.3, 0.2][:len(distances)]
            self.distance_estimate = sum(d * w for d, w in zip(distances, weights)) / sum(weights)
        else:
            self.distance_estimate = 50.0  # Default far distance
        
        # Apply reasonable bounds for automotive scenarios
        self.distance_estimate = max(0.5, min(self.distance_estimate, 100.0))
    
    def _calculate_real_world_motion(self):
        """Convert pixel motion to real-world motion"""
        if self.distance_estimate > 0:
            # Convert pixel velocity to real-world velocity
            # Approximate conversion: pixels to meters at current distance
            pixel_to_meter_ratio = self.distance_estimate / config.CAMERA_FOCAL_LENGTH
            
            self.real_world_velocity = self.velocity * pixel_to_meter_ratio
            
            # Calculate speed in km/h
            speed_ms = np.linalg.norm(self.real_world_velocity)
            self.speed = speed_ms * 3.6  # Convert m/s to km/h
    
    def _calculate_time_to_collision(self):
        """Enhanced TTC calculation with trajectory prediction"""
        if self.distance_estimate <= 0:
            self.time_to_collision = float('inf')
            return
        
        # Method 1: Simple radial approach
        # Check if object is moving towards camera (increasing in size or moving down)
        if len(self.position_history) >= 2:
            # Check if object is getting closer (increasing in size)
            current_height = self.box[3] - self.box[1]
            
            # Get previous box size if available (simplified approach)
            is_approaching = self.velocity[1] > 0  # Moving down in frame
            
            if is_approaching and np.linalg.norm(self.real_world_velocity) > 0.1:
                # Calculate TTC based on closing speed
                closing_speed = np.linalg.norm(self.real_world_velocity)
                self.time_to_collision = self.distance_estimate / closing_speed
            else:
                self.time_to_collision = float('inf')
        
        # Cap TTC to reasonable values
        if self.time_to_collision > 60:  # More than 1 minute
            self.time_to_collision = float('inf')
    
    def _assess_risk(self):
        """Enhanced risk assessment using multiple factors"""
        # Get thresholds from config
        critical_dist = config.CRITICAL_DISTANCE_THRESHOLD
        high_dist = config.HIGH_RISK_DISTANCE_THRESHOLD
        medium_dist = config.MEDIUM_RISK_DISTANCE_THRESHOLD
        
        critical_ttc = config.CRITICAL_TTC_THRESHOLD
        high_ttc = config.HIGH_RISK_TTC_THRESHOLD
        medium_ttc = config.MEDIUM_RISK_TTC_THRESHOLD
        
        # Priority-based assessment
        is_high_priority = self.class_name.lower() in [cls.lower() for cls in config.HIGH_PRIORITY_CLASSES]
        is_medium_priority = self.class_name.lower() in [cls.lower() for cls in config.MEDIUM_PRIORITY_CLASSES]
        
        # Multi-factor risk assessment
        risk_factors = []
        
        # Distance factor
        if self.distance_estimate <= critical_dist:
            risk_factors.append(4)  # Critical
        elif self.distance_estimate <= high_dist:
            risk_factors.append(3)  # High
        elif self.distance_estimate <= medium_dist:
            risk_factors.append(2)  # Medium
        else:
            risk_factors.append(1)  # Low
        
        # TTC factor
        if self.time_to_collision <= critical_ttc:
            risk_factors.append(4)  # Critical
        elif self.time_to_collision <= high_ttc:
            risk_factors.append(3)  # High
        elif self.time_to_collision <= medium_ttc:
            risk_factors.append(2)  # Medium
        else:
            risk_factors.append(1)  # Low
        
        # Speed factor
        if self.speed > config.HIGH_SPEED_THRESHOLD:
            risk_factors.append(3)  # High speed increases risk
        elif self.speed > config.MEDIUM_SPEED_THRESHOLD:
            risk_factors.append(2)
        else:
            risk_factors.append(1)
        
        # Object priority factor
        if is_high_priority:
            risk_factors.append(3)
        elif is_medium_priority:
            risk_factors.append(2)
        else:
            risk_factors.append(1)
        
        # Calculate overall risk
        max_risk = max(risk_factors)
        avg_risk = sum(risk_factors) / len(risk_factors)
        
        # Use weighted combination of max and average
        final_risk_score = 0.7 * max_risk + 0.3 * avg_risk
        
        # Map to risk levels
        if final_risk_score >= 3.5:
            self.risk_level = "Critical"
        elif final_risk_score >= 2.5:
            self.risk_level = "High"
        elif final_risk_score >= 1.8:
            self.risk_level = "Medium"
        elif final_risk_score >= 1.2:
            self.risk_level = "Low"
        else:
            self.risk_level = "None"
    
    def get_prediction(self, time_ahead: float = 1.0) -> Tuple[float, float]:
        """Predict future position using current velocity and acceleration"""
        if not self.position_history:
            return 0.0, 0.0
        
        current_pos = np.array([self.position_history[-1][1], self.position_history[-1][2]])
        
        # Kinematic prediction: pos = current_pos + v*t + 0.5*a*t²
        future_pos = (current_pos + 
                     self.velocity * time_ahead + 
                     0.5 * self.acceleration * time_ahead**2)
        
        return float(future_pos[0]), float(future_pos[1])
    
    def get_detailed_info(self) -> dict:
        """Get comprehensive object information for analysis"""
        return {
            'track_id': self.track_id,
            'class_name': self.class_name,
            'distance': self.distance_estimate,
            'speed': self.speed,
            'velocity': self.real_world_velocity.tolist(),
            'acceleration': self.acceleration.tolist(),
            'time_to_collision': self.time_to_collision,
            'risk_level': self.risk_level,
            'confidence': self.confidence,
            'age': self.age,
            'box': self.box,
            'position_history_length': len(self.position_history)
        }

    def __repr__(self):
        return (f"TrackedObject(id={self.track_id}, class='{self.class_name}', "
                f"distance={self.distance_estimate:.1f}m, speed={self.speed:.1f}km/h, "
                f"ttc={self.time_to_collision:.1f}s, risk={self.risk_level}, age={self.age})")

class Tracker(ABC):
    @abstractmethod
    def track_objects(self, detections: List[Detection], frame: np.ndarray) -> List[TrackedObject]:
        """
        Tracks objects based on detections from the current frame.
        """
        pass
