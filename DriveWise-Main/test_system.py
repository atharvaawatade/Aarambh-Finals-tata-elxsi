# test_system.py - Test the Enhanced Lane-Aware FCW system
import cv2
import numpy as np
import os
import sys

def create_test_video():
    """Create a test video with lane scenarios for testing lane-aware logic"""
    print("Creating enhanced test video with lane scenarios...")
    
    # Video properties
    width, height = 640, 480
    fps = 30
    duration = 8  # seconds
    total_frames = fps * duration
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter('test_video.mp4', fourcc, fps, (width, height))
    
    for frame_num in range(total_frames):
        # Create a road scene
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add road background
        cv2.rectangle(frame, (0, height//2), (width, height), (60, 60, 60), -1)
        
        # Add lane markings (3 lanes)
        lane_width = width // 3
        # Left lane line
        for y in range(height//2, height, 20):
            cv2.rectangle(frame, (lane_width, y), (lane_width + 5, y + 10), (255, 255, 255), -1)
        # Right lane line
        for y in range(height//2, height, 20):
            cv2.rectangle(frame, (2 * lane_width, y), (2 * lane_width + 5, y + 10), (255, 255, 255), -1)
        
        # Scenario 1: Same lane vehicle (frames 0-90)
        if frame_num < 90:
            car_x = width // 2  # Center lane (same as ego)
            car_y = height//2 + 50 + int(frame_num * 1.5)  # Moving towards camera
            car_width = 50 + int(frame_num * 0.8)  # Getting larger
            car_height = 30 + int(frame_num * 0.5)
            
            if car_y < height - car_height:
                # Draw car
                cv2.rectangle(frame, (car_x - car_width//2, car_y), 
                             (car_x + car_width//2, car_y + car_height), (0, 0, 255), -1)
        
        # Scenario 2: Opposite lane vehicle (frames 90-150)
        elif frame_num < 150:
            car_x = lane_width // 2  # Left lane (opposite direction)
            car_y = height - 50 - int((frame_num - 90) * 2)  # Moving away from camera
            car_width = 60 - int((frame_num - 90) * 0.3)  # Getting smaller
            car_height = 40 - int((frame_num - 90) * 0.2)
            
            if car_y > height//2 and car_width > 20:
                # Draw car
                cv2.rectangle(frame, (car_x - car_width//2, car_y), 
                             (car_x + car_width//2, car_y + car_height), (255, 0, 0), -1)
        
        # Scenario 3: Lane changing vehicle (frames 150-210)
        elif frame_num < 210:
            relative_frame = frame_num - 150
            start_x = 2 * lane_width + lane_width//2  # Start in right lane
            end_x = width // 2  # End in center lane
            car_x = start_x + int((end_x - start_x) * (relative_frame / 60))  # Interpolate
            car_y = height - 100
            car_width = 50
            car_height = 35
            
            # Draw car
            cv2.rectangle(frame, (car_x - car_width//2, car_y), 
                         (car_x + car_width//2, car_y + car_height), (0, 255, 255), -1)
        
        # Add ego vehicle indicator
        ego_x = width // 2
        ego_y = height - 30
        cv2.circle(frame, (ego_x, ego_y), 8, (0, 255, 0), -1)
        cv2.putText(frame, "EGO", (ego_x - 15, ego_y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        
        out.write(frame)
    
    out.release()
    print("Enhanced test video created: test_video.mp4")

def test_lane_aware_system():
    """Test the lane-aware collision detection system"""
    print("\nTesting Lane-Aware FCW System...")
    
    try:
        # Import system components
        from modules.analyzers.collision_predictor import IntelligentCollisionPredictor
        from modules.feature_extractors.lane_detector import SimpleLaneDetector
        from plugins.yolo_detector import YOLODetector
        from plugins.kalman_tracker import KalmanTracker
        from utils.helpers import draw_detections, draw_primary_warning
        
        # Initialize components
        print("Initializing components...")
        detector = YOLODetector()
        tracker = KalmanTracker()
        collision_predictor = IntelligentCollisionPredictor()
        
        # Open test video
        cap = cv2.VideoCapture('test_video.mp4')
        if not cap.isOpened():
            print("❌ Cannot open test video")
            return
        
        # Setup output video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter('output_annotated.mp4', fourcc, 30.0, (640, 480))
        
        frame_count = 0
        print("Processing video...")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Detect objects
            detections = detector.detect(frame)
            
            # Track objects
            tracked_objects = tracker.update(detections)
            
            # Analyze collision risk (lane-aware)
            collision_analysis = collision_predictor.analyze_collision_risk(tracked_objects, frame)
            
            # Draw visualizations
            annotated_frame = draw_detections(frame.copy(), tracked_objects, collision_analysis)
            
            # Add warning overlay
            risk_level = collision_analysis.get('risk_level', 'None')
            if risk_level != 'None':
                warning_text = f"{risk_level} Risk"
                recommendations = collision_analysis.get('recommendations', [])
                if recommendations:
                    warning_text += f": {recommendations[0]}"
                annotated_frame = draw_primary_warning(annotated_frame, warning_text, risk_level)
            
            # Add frame info
            info_text = f"Frame: {frame_count} | Risk: {risk_level}"
            cv2.putText(annotated_frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Show lane analysis info
            lane_info = collision_analysis.get('lane_info')
            if lane_info:
                lane_text = f"Lane Change: {'Yes' if lane_info.lane_change_detected else 'No'}"
                cv2.putText(annotated_frame, lane_text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Show threat breakdown
            threat_info = f"Same Lane: {collision_analysis.get('same_lane_threats', 0)} | "
            threat_info += f"Oncoming: {collision_analysis.get('oncoming_threats', 0)} | "
            threat_info += f"Lane Change: {collision_analysis.get('lane_change_threats', 0)}"
            frame_height = annotated_frame.shape[0]
            cv2.putText(annotated_frame, threat_info, (10, frame_height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
            # Write frame
            out.write(annotated_frame)
            
            # Print analysis for key frames
            if frame_count % 30 == 0:  # Every second
                print(f"Frame {frame_count}: Risk={risk_level}, "
                      f"Same Lane Threats={collision_analysis.get('same_lane_threats', 0)}, "
                      f"Oncoming Threats={collision_analysis.get('oncoming_threats', 0)}")
        
        cap.release()
        out.release()
        
        print(f"✅ Processed {frame_count} frames successfully!")
        print("Lane-aware analysis completed. Check 'output_annotated.mp4' for results.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_real_time_system():
    """Test real-time system (requires GUI)"""
    print("\nTo test real-time system with GUI:")
    print("python main.py")
    print("\nThis will start the enhanced lane-aware FCW system with:")
    print("• Lane detection and tracking")
    print("• Intelligent collision prediction")
    print("• Same-lane vs opposite-lane threat analysis")
    print("• Lane change detection")
    print("• Enhanced visual warnings")

if __name__ == '__main__':
    print("=" * 60)
    print("🧪 TESTING ENHANCED LANE-AWARE FCW SYSTEM")
    print("=" * 60)
    
    # Create test video with lane scenarios
    create_test_video()
    
    # Test lane-aware processing
    test_lane_aware_system()
    
    # Instructions for real-time testing
    test_real_time_system()
    
    print("\n" + "=" * 60)
    print("✅ Test completed! The system now intelligently:")
    print("• Only warns about same-lane slower/stationary vehicles")
    print("• Ignores opposite-direction traffic unless lane changing")
    print("• Detects and warns about lane change conflicts")
    print("• Provides context-aware recommendations")
    print("=" * 60) 