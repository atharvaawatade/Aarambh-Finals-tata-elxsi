"""
Intelligent Lane-Aware Collision Predictor
Only warns about vehicles that pose actual collision risk based on lane analysis
"""

import numpy as np
import math
from typing import List, Dict, Any, Optional, Tuple
import time

import config
from modules.feature_extractors.lane_detector import LaneInfo, SimpleLaneDetector

class IntelligentCollisionPredictor:
    """
    Lane-aware collision predictor that understands traffic flow and lane discipline
    Only generates warnings for actual collision threats:
    1. Vehicles in same lane moving slower/stationary
    2. Oncoming vehicles only if we're changing lanes into their path
    3. Vehicles from adjacent lanes only if they're changing into our lane
    """
    
    def __init__(self):
        self.frame_count = 0
        self.last_analysis_time = 0
        
        # Thresholds
        self.critical_distance = config.CRITICAL_DISTANCE_THRESHOLD
        self.high_risk_distance = config.HIGH_RISK_DISTANCE_THRESHOLD
        self.medium_risk_distance = config.MEDIUM_RISK_DISTANCE_THRESHOLD
        
        self.critical_ttc = config.CRITICAL_TTC_THRESHOLD
        self.high_risk_ttc = config.HIGH_RISK_TTC_THRESHOLD
        self.medium_risk_ttc = config.MEDIUM_RISK_TTC_THRESHOLD
        
        # Lane detector for intelligent analysis
        self.lane_detector = SimpleLaneDetector()
        
        # Vehicle tracking for direction analysis
        self.vehicle_history = {}  # track_id -> position history
        self.max_history_frames = 10
        
    def analyze_collision_risk(self, tracked_objects: List[Dict], frame: np.ndarray) -> Dict[str, Any]:
        """
        Intelligent collision risk analysis considering lane positions and movement patterns
        
        Args:
            tracked_objects: List of tracked object dictionaries
            frame: Current frame for lane detection
            
        Returns:
            Detailed analysis with lane-aware threat assessment
        """
        start_time = time.perf_counter()
        
        # Initialize result
        result = {
            'risk_level': 'None',
            'threat_score': 0,
            'primary_threat': None,
            'threatening_objects': [],
            'recommendations': [],
            'analysis_time_ms': 0,
            'total_objects': len(tracked_objects),
            'lane_info': None,
            'same_lane_threats': 0,
            'oncoming_threats': 0,
            'lane_change_threats': 0
        }
        
        if not tracked_objects:
            return result
        
        # Detect lanes and ego vehicle position
        lane_info = self.lane_detector.detect_lanes(frame)
        result['lane_info'] = lane_info
        
        # Filter for vehicle objects only
        vehicles = [
            obj for obj in tracked_objects 
            if obj.get('class_name', '').lower() in ['car', 'truck', 'bus', 'motorcycle']
        ]
        
        if not vehicles:
            return result
        
        # Analyze each vehicle for collision risk
        threatening_objects = []
        max_threat_score = 0
        primary_threat = None
        
        frame_height, frame_width = frame.shape[:2]
        
        for vehicle in vehicles:
            # Analyze individual vehicle threat
            threat_analysis = self._analyze_vehicle_threat(vehicle, lane_info, frame_height, frame_width)
            
            if threat_analysis['is_threat']:
                threatening_objects.append(threat_analysis)
                
                # Update counters
                if threat_analysis['threat_type'] == 'same_lane':
                    result['same_lane_threats'] += 1
                elif threat_analysis['threat_type'] == 'oncoming':
                    result['oncoming_threats'] += 1
                elif threat_analysis['threat_type'] == 'lane_change':
                    result['lane_change_threats'] += 1
                
                # Track primary threat
                if threat_analysis['threat_score'] > max_threat_score:
                    max_threat_score = threat_analysis['threat_score']
                    primary_threat = vehicle
        
        # Determine overall risk level
        if max_threat_score >= 80:
            risk_level = 'Critical'
        elif max_threat_score >= 60:
            risk_level = 'High'
        elif max_threat_score >= 40:
            risk_level = 'Medium'
        elif max_threat_score >= 20:
            risk_level = 'Low'
        else:
            risk_level = 'None'
        
        # Generate intelligent recommendations
        recommendations = self._generate_intelligent_recommendations(
            risk_level, threatening_objects, lane_info
        )
        
        # Update result
        result.update({
            'risk_level': risk_level,
            'threat_score': max_threat_score,
            'primary_threat': primary_threat,
            'threatening_objects': threatening_objects,
            'recommendations': recommendations,
            'analysis_time_ms': (time.perf_counter() - start_time) * 1000
        })
        
        return result
    
    def _analyze_vehicle_threat(self, vehicle: Dict, lane_info: LaneInfo, frame_height: int, frame_width: int) -> Dict:
        """Analyze if a specific vehicle poses a collision threat"""
        bbox = vehicle.get('bbox', [0, 0, 0, 0])
        track_id = vehicle.get('track_id', 0)
        
        # Basic threat analysis structure
        threat_analysis = {
            'object': vehicle,
            'is_threat': False,
            'threat_type': 'none',  # 'same_lane', 'oncoming', 'lane_change', 'none'
            'threat_score': 0,
            'distance': 0,
            'ttc': float('inf'),
            'vehicle_lane': 0,
            'movement_direction': 'unknown',
            'relative_speed': 0
        }
        
        # Calculate basic metrics
        distance = self._estimate_distance_fast(vehicle, frame_height)
        threat_analysis['distance'] = distance
        
        # Determine vehicle's lane
        vehicle_lane = self.lane_detector.get_vehicle_lane(bbox, lane_info)
        threat_analysis['vehicle_lane'] = vehicle_lane
        
        # Analyze vehicle movement pattern
        movement_analysis = self._analyze_vehicle_movement(vehicle, track_id)
        threat_analysis.update(movement_analysis)
        
        # Calculate TTC
        ttc = self._calculate_intelligent_ttc(vehicle, distance, movement_analysis)
        threat_analysis['ttc'] = ttc
        
        # Determine if this vehicle is actually a threat
        threat_assessment = self._assess_actual_threat(
            vehicle_lane, lane_info, movement_analysis, distance, ttc
        )
        
        threat_analysis.update(threat_assessment)
        
        return threat_analysis
    
    def _analyze_vehicle_movement(self, vehicle: Dict, track_id: int) -> Dict:
        """Analyze vehicle movement pattern to determine direction and speed"""
        bbox = vehicle.get('bbox', [0, 0, 0, 0])
        current_center = [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2]
        
        # Update vehicle history
        if track_id not in self.vehicle_history:
            self.vehicle_history[track_id] = []
        
        self.vehicle_history[track_id].append(current_center)
        
        # Keep only recent history
        if len(self.vehicle_history[track_id]) > self.max_history_frames:
            self.vehicle_history[track_id].pop(0)
        
        movement_info = {
            'movement_direction': 'unknown',
            'relative_speed': 0,
            'is_approaching': False,
            'is_changing_lanes': False,
            'lane_change_direction': 'none'
        }
        
        # Analyze movement if we have enough history
        if len(self.vehicle_history[track_id]) >= 3:
            positions = self.vehicle_history[track_id]
            
            # Calculate movement vector
            start_pos = positions[0]
            end_pos = positions[-1]
            
            dx = end_pos[0] - start_pos[0]
            dy = end_pos[1] - start_pos[1]
            
            # Determine movement direction
            if abs(dx) > abs(dy):
                if dx > 0:
                    movement_info['movement_direction'] = 'right'
                else:
                    movement_info['movement_direction'] = 'left'
            else:
                if dy > 0:
                    movement_info['movement_direction'] = 'down'  # towards camera
                    movement_info['is_approaching'] = True
                else:
                    movement_info['movement_direction'] = 'up'    # away from camera
            
            # Calculate relative speed (pixels per frame)
            movement_info['relative_speed'] = math.sqrt(dx*dx + dy*dy) / len(positions)
            
            # Detect lane changes (significant horizontal movement)
            if abs(dx) > 20:  # threshold for lane change detection
                movement_info['is_changing_lanes'] = True
                movement_info['lane_change_direction'] = 'right' if dx > 0 else 'left'
        
        return movement_info
    
    def _assess_actual_threat(self, vehicle_lane: int, lane_info: LaneInfo, 
                            movement_analysis: Dict, distance: float, ttc: float) -> Dict:
        """Determine if this vehicle actually poses a collision threat"""
        
        ego_lane = lane_info.ego_lane_id
        is_threat = False
        threat_type = 'none'
        threat_score = 0
        
        # Case 1: Vehicle in same lane
        if vehicle_lane == ego_lane:
            # Only a threat if it's closer and moving slower or stationary
            if distance < self.medium_risk_distance:
                if not movement_analysis['is_approaching'] or movement_analysis['relative_speed'] < 2:
                    is_threat = True
                    threat_type = 'same_lane'
                    # Higher threat if very close or stationary
                    if distance < self.critical_distance:
                        threat_score = 90
                    elif distance < self.high_risk_distance:
                        threat_score = 70
                    else:
                        threat_score = 50
        
        # Case 2: Oncoming traffic (opposite lane)
        elif vehicle_lane == -1:  # Left side (oncoming)
            # Only a threat if we're changing lanes to the left
            if lane_info.lane_change_detected and lane_info.lane_change_direction == 'left':
                if distance < self.high_risk_distance and movement_analysis['is_approaching']:
                    is_threat = True
                    threat_type = 'oncoming'
                    # Very high threat for oncoming during lane change
                    threat_score = 95
        
        # Case 3: Adjacent lane vehicle changing into our lane
        elif abs(vehicle_lane - ego_lane) == 1:  # Adjacent lane
            if movement_analysis['is_changing_lanes']:
                # Check if changing into our lane
                our_lane_direction = 'right' if vehicle_lane < ego_lane else 'left'
                if movement_analysis['lane_change_direction'] == our_lane_direction:
                    if distance < self.medium_risk_distance:
                        is_threat = True
                        threat_type = 'lane_change'
                        threat_score = 60
        
        # Case 4: We're changing lanes into their lane
        elif lane_info.lane_change_detected:
            target_lane = ego_lane + (1 if lane_info.lane_change_direction == 'right' else -1)
            if vehicle_lane == target_lane:
                if distance < self.medium_risk_distance:
                    is_threat = True
                    threat_type = 'lane_change'
                    threat_score = 70
        
        # Adjust threat score based on TTC
        if is_threat and ttc < self.critical_ttc:
            threat_score = min(100, threat_score + 20)
        elif is_threat and ttc < self.high_risk_ttc:
            threat_score = min(100, threat_score + 10)
        
        return {
            'is_threat': is_threat,
            'threat_type': threat_type,
            'threat_score': threat_score
        }
    
    def _estimate_distance_fast(self, obj: Dict, frame_height: int) -> float:
        """Fast distance estimation using object height"""
        try:
            class_name = obj.get('class_name', '').lower()
            bbox = obj.get('bbox', [0, 0, 0, 0])
            
            object_height_pixels = bbox[3] - bbox[1]
            if object_height_pixels <= 0:
                return 50.0
            
            known_height = config.KNOWN_OBJECT_SIZES.get(class_name, {}).get('height', 1.5)
            focal_length = frame_height * 0.8
            distance = (known_height * focal_length) / object_height_pixels
            
            return max(1.0, min(distance, 100.0))
        except:
            return 50.0
    
    def _calculate_intelligent_ttc(self, vehicle: Dict, distance: float, movement_analysis: Dict) -> float:
        """Calculate time-to-collision considering movement direction"""
        try:
            if not movement_analysis['is_approaching']:
                return float('inf')  # Not approaching, no collision risk
            
            speed = movement_analysis['relative_speed']
            if speed < 0.1:
                return float('inf')
            
            # Convert pixel speed to approximate real-world speed
            # This is a rough approximation - could be improved with calibration
            estimated_speed_mps = speed * 0.1  # rough conversion
            
            ttc = distance / estimated_speed_mps
            return max(0.1, ttc)
        except:
            return float('inf')
    
    def _generate_intelligent_recommendations(self, risk_level: str, 
                                           threatening_objects: List[Dict], 
                                           lane_info: LaneInfo) -> List[str]:
        """Generate context-aware recommendations"""
        recommendations = []
        
        if not threatening_objects:
            return recommendations
        
        # Analyze threat types
        same_lane_threats = [t for t in threatening_objects if t['threat_type'] == 'same_lane']
        oncoming_threats = [t for t in threatening_objects if t['threat_type'] == 'oncoming']
        lane_change_threats = [t for t in threatening_objects if t['threat_type'] == 'lane_change']
        
        # Generate specific recommendations
        if risk_level == 'Critical':
            recommendations.append("EMERGENCY BRAKE")
            if same_lane_threats:
                recommendations.append("VEHICLE AHEAD TOO CLOSE")
            if oncoming_threats:
                recommendations.append("ABORT LANE CHANGE - ONCOMING TRAFFIC")
        
        elif risk_level == 'High':
            if same_lane_threats:
                recommendations.append("SLOW DOWN - FOLLOWING TOO CLOSE")
            if lane_change_threats:
                recommendations.append("VEHICLE CHANGING LANES")
            if oncoming_threats:
                recommendations.append("CAUTION - ONCOMING DURING LANE CHANGE")
        
        elif risk_level == 'Medium':
            if same_lane_threats:
                recommendations.append("MAINTAIN SAFE DISTANCE")
            if lane_change_threats:
                recommendations.append("MONITOR ADJACENT LANES")
            if lane_info.lane_change_detected:
                recommendations.append("LANE CHANGE IN PROGRESS")
        
        elif risk_level == 'Low':
            recommendations.append("STAY ALERT")
            if lane_info.lane_change_detected:
                recommendations.append("COMPLETE LANE CHANGE SAFELY")
        
        return recommendations
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            'frame_count': self.frame_count,
            'avg_analysis_time': self.last_analysis_time,
            'vehicle_history_size': len(self.vehicle_history)
        }

# Alias for backward compatibility
CollisionPredictor = IntelligentCollisionPredictor
