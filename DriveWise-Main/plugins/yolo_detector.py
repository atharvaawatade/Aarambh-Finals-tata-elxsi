"""
YOLO Detector Plugin - PERFORMANCE OPTIMIZED
Ultra-fast object detection for Tata Elxsi Hackathon
"""
import cv2
import numpy as np
from ultralytics import YOLO
import torch
from typing import List, Dict, Any, Tuple
import time

import config

class YOLODetector:
    """YOLO-based object detector optimized for maximum speed"""
    
    def __init__(self, model_path: str = 'yolo11n.pt', **kwargs):
        """Initialize YOLO detector with performance optimizations"""
        self.model_path = model_path
        
        # Performance settings from kwargs
        self.confidence_threshold = kwargs.get('confidence_threshold', 0.6)
        self.iou_threshold = kwargs.get('iou_threshold', 0.5)
        self.max_detections = kwargs.get('max_detections', 20)
        self.img_size = kwargs.get('img_size', 416)  # Smaller for speed
        self.half_precision = kwargs.get('half_precision', True)
        
        # Initialize model
        self._load_model()
        
        # Performance tracking
        self.inference_times = []
        
    def _load_model(self):
        """Load YOLO model with optimizations"""
        print(f"🚀 Initializing YOLOv11n detector...")
        print(f"Model path: {self.model_path}")
        
        try:
            # Load model
            self.model = YOLO(self.model_path)
            
            # Performance optimizations
            if torch.cuda.is_available():
                self.device = 'cuda'
                self.model.to('cuda')
                print("🔥 GPU acceleration enabled!")
            else:
                self.device = 'cpu'
                print("⚡ Using CPU (consider GPU for better performance)")
            
            # Enable half precision if supported
            if self.half_precision and torch.cuda.is_available():
                self.model.half()
                print("🚀 Half precision (FP16) enabled!")
            
            # Warmup the model with a dummy inference
            dummy_img = np.zeros((self.img_size, self.img_size, 3), dtype=np.uint8)
            _ = self.model.predict(dummy_img, verbose=False, conf=self.confidence_threshold)
            
            print("✅ YOLOv11n model loaded successfully!")
            
            # Get model info
            if hasattr(self.model.model, 'info'):
                info = self.model.model.info()
                print(f"YOLO11n summary: {info[0]} layers, {info[1]:,} parameters, {info[2]} gradients, {info[3]} GFLOPs")
                print(f"Model info: {info}")
            
            # Print class information
            if hasattr(self.model, 'names'):
                num_classes = len(self.model.names)
                print(f"📋 Detected classes: {num_classes} classes available")
            
        except Exception as e:
            print(f"❌ Error loading YOLO model: {e}")
            raise
    
    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect objects in frame with maximum speed optimizations
        
        Args:
            frame: Input frame (BGR format)
            
        Returns:
            List of detection dictionaries
        """
        start_time = time.perf_counter()
        
        try:
            # Resize frame for faster processing
            if frame.shape[:2] != (self.img_size, self.img_size):
                frame_resized = cv2.resize(frame, (self.img_size, self.img_size))
            else:
                frame_resized = frame
            
            # Run inference with optimizations
            results = self.model.predict(
                frame_resized,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                max_det=self.max_detections,
                verbose=False,
                device=self.device,
                half=self.half_precision,
                imgsz=self.img_size,
                augment=False,  # Disable augmentation for speed
                visualize=False,  # Disable visualization for speed
                save=False,  # Don't save results
                stream=False,  # Don't use streaming
                agnostic_nms=True,  # Faster NMS
            )
            
            # Convert results to our format
            detections = []
            
            if results and len(results) > 0:
                result = results[0]  # Get first result
                
                if result.boxes is not None and len(result.boxes) > 0:
                    boxes = result.boxes.xyxy.cpu().numpy()  # x1, y1, x2, y2
                    confidences = result.boxes.conf.cpu().numpy()
                    class_ids = result.boxes.cls.cpu().numpy().astype(int)
                    
                    # Scale boxes back to original frame size
                    orig_h, orig_w = frame.shape[:2]
                    scale_x = orig_w / self.img_size
                    scale_y = orig_h / self.img_size
                    
                    for i in range(len(boxes)):
                        x1, y1, x2, y2 = boxes[i]
                        
                        # Scale coordinates
                        x1 = int(x1 * scale_x)
                        y1 = int(y1 * scale_y)
                        x2 = int(x2 * scale_x)
                        y2 = int(y2 * scale_y)
                        
                        # Get class name
                        class_name = self.model.names.get(class_ids[i], f'class_{class_ids[i]}')
                        
                        detection = {
                            'bbox': [x1, y1, x2, y2],
                            'confidence': float(confidences[i]),
                            'class_id': int(class_ids[i]),
                            'class_name': class_name,
                            'center': [(x1 + x2) // 2, (y1 + y2) // 2],
                            'area': (x2 - x1) * (y2 - y1)
                        }
                        detections.append(detection)
            
            # Track inference time
            inference_time = (time.perf_counter() - start_time) * 1000  # ms
            self.inference_times.append(inference_time)
            
            # Keep only last 100 times for average calculation
            if len(self.inference_times) > 100:
                self.inference_times = self.inference_times[-100:]
            
            return detections
            
        except Exception as e:
            print(f"❌ Detection error: {e}")
            return []
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics"""
        if not self.inference_times:
            return {'avg_inference_time_ms': 0.0, 'fps': 0.0}
        
        avg_time = np.mean(self.inference_times)
        fps = 1000.0 / avg_time if avg_time > 0 else 0.0
        
        return {
            'avg_inference_time_ms': avg_time,
            'fps': fps,
            'min_time_ms': np.min(self.inference_times),
            'max_time_ms': np.max(self.inference_times)
        }
    
    def get_class_names(self) -> Dict[int, str]:
        """Get mapping of class IDs to names"""
        if hasattr(self.model, 'names'):
            return self.model.names
        return {}
    
    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'model'):
            del self.model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

# Factory function for plugin system
def create_detector(**kwargs) -> YOLODetector:
    """Factory function to create YOLO detector"""
    return YOLODetector(**kwargs)
