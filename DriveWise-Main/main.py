"""
FCW System Main - PERFORMANCE OPTIMIZED
Ultra-fast processing for Tata Elxsi Hackathon Competition
"""

import sys
import cv2
import time
import numpy as np
from PyQt5.QtWidgets import QApplication, QDialog
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
import logging
import asyncio
import threading

# Import modules
import config
from modules.gemini import initialize_gemini
from modules.user_interface import (EnhancedRealtimeInterface, OfflineAnalysisInterface, 
                                    ModeSelectionDialog, get_qt_app)
from plugins.yolo_detector import create_detector
from plugins.kalman_tracker import KalmanTracker
from modules.analyzers.collision_predictor import CollisionPredictor
from modules.warning_generator import GeminiWarningGenerator
from utils.helpers import draw_detections, draw_primary_warning
from modules.offline_processor import OfflineVideoProcessor
from modules.analyzers.weather_impact_analyzer import EnhancedWeatherImpactAnalyzer
from modules.gps_service import GPSService

class PerformanceOptimizedProcessor(QThread):
    """Ultra-fast processing thread optimized for competition"""
    frame_processed = pyqtSignal(np.ndarray, dict)
    stats_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, loop: asyncio.AbstractEventLoop):
        super().__init__()
        self.loop = loop
        self.camera = None
        self.running = False
        self._initialize_components()
        
        # Performance tracking
        self.frame_count = 0
        self.start_time = time.perf_counter()
        self.last_fps_time = time.perf_counter()
        self.processing_times = []
        self.current_fps = 0.0

    def _initialize_components(self):
        """Initializes all processing components."""
        self.detector = create_detector(**config.get_detection_config())
        self.tracker = KalmanTracker()
        self.collision_predictor = CollisionPredictor()
        self.warning_generator = GeminiWarningGenerator()
        self.weather_analyzer = EnhancedWeatherImpactAnalyzer()
        print("✅ Core components initialized for real-time processor.")

    def run(self):
        """Main processing loop - OPTIMIZED FOR SPEED"""
        self.logger = logging.getLogger(__name__)
        
        self.camera = cv2.VideoCapture(config.CAMERA_INDEX)
        if not self.camera.isOpened():
            self.error_occurred.emit("Failed to open camera")
            return
        
        # Initialize weather analyzer in this thread's event loop
        future = asyncio.run_coroutine_threadsafe(self.weather_analyzer.initialize(), self.loop)
        future.result(timeout=10) # Wait for initialization
        
        self.running = True
        
        while self.running:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    self.logger.warning("Camera feed ended or failed.")
                    time.sleep(0.5)
                    break
                
                # This is now a non-blocking call
                analysis_data = self._process_frame(frame)

                output_frame = frame.copy()
                output_frame = draw_detections(output_frame, 
                                               analysis_data.get('tracked_objects', []), 
                                               analysis_data.get('collision_analysis', {}))
                
                draw_primary_warning(output_frame, 
                                     analysis_data.get('warning_text', ''), 
                                     analysis_data.get('risk_level', 'None'))

                self.frame_processed.emit(output_frame, analysis_data)
                self._update_performance_metrics()
                
            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}", exc_info=True)
                self.error_occurred.emit(str(e))

        # Shutdown weather analyzer
        if self.weather_analyzer:
            future = asyncio.run_coroutine_threadsafe(self.weather_analyzer.shutdown(), self.loop)
            try:
                future.result(timeout=5)
            except Exception as e:
                self.logger.error(f"Error shutting down weather analyzer: {e}")

        if self.camera:
            self.camera.release()

    def _process_frame(self, frame):
        detections = self.detector.detect(frame)
        tracked_objects = self.tracker.update(detections)
        collision_analysis = self.collision_predictor.analyze_collision_risk(tracked_objects, frame)
        
        # Get the latest non-blocking weather analysis
        weather_analysis = self.weather_analyzer.get_current_analysis() if self.weather_analyzer else None
        
        # The warning generator is now fully sync for the non-AI part
        warning_text = self.warning_generator.generate_warning(collision_analysis, weather_analysis)
        
        # If high risk, we can spawn an async task for a better warning without blocking
        if collision_analysis.get('risk_level') in ['High', 'Critical']:
            asyncio.run_coroutine_threadsafe(
                self._update_warning_async(collision_analysis, weather_analysis), 
                self.loop
            )

        return {
            "tracked_objects": tracked_objects,
            "collision_analysis": collision_analysis,
            "warning_text": warning_text,
            "risk_level": collision_analysis.get('risk_level', 'None'),
            "weather_analysis": weather_analysis
        }

    async def _update_warning_async(self, collision_analysis, weather_analysis):
        """Generates a detailed warning in the background."""
        warning_text = await self.warning_generator.generate_warning_async(collision_analysis, weather_analysis)
        # To push this back to the UI, a new signal would be needed.
        # For now, we log it.
        self.logger.info(f"AI Generated Warning: {warning_text}")

    def _update_performance_metrics(self):
        """Calculates and emits performance metrics."""
        self.frame_count += 1
        now = time.perf_counter()
        
        processing_time = now - self.start_time
        self.start_time = now
        self.processing_times.append(processing_time)
        if len(self.processing_times) > 100:
            self.processing_times.pop(0)

        if (now - self.last_fps_time) >= 1.0:
            self.current_fps = len(self.processing_times) / sum(self.processing_times) if self.processing_times else 0
            avg_latency = (sum(self.processing_times) / len(self.processing_times)) * 1000 if self.processing_times else 0
            
            self.stats_updated.emit({
                'fps': self.current_fps,
                'latency_ms': avg_latency
            })
            self.last_fps_time = now

    def stop(self):
        """Stops the processing thread."""
        self.running = False
        if self.camera:
            self.camera.release()

class FCWApplication:
    """Orchestrates the REAL-TIME application."""
    def __init__(self):
        self.app = get_qt_app()
        self.loop = asyncio.get_event_loop()
        self.ui = EnhancedRealtimeInterface()
        self.processor = PerformanceOptimizedProcessor(loop=self.loop)
        if config.GPS_ENABLED:
            self.gps_service = GPSService()
        else:
            self.gps_service = None
        self.stopping = False
        self._connect_signals()

    def _connect_signals(self):
        self.processor.frame_processed.connect(self._handle_frame)
        self.processor.stats_updated.connect(self.ui.update_performance_metrics)
        if self.gps_service:
            self.gps_service.speed_updated.connect(self.ui.update_vehicle_speed)
            self.gps_service.status_updated.connect(lambda status: self.ui.update_status_log(f"GPS: {status}"))
        self.ui.start_button.clicked.connect(self.start_system)
        self.ui.stop_button.clicked.connect(self.stop_system)
        self.ui.stop_requested.connect(self.stop_system)

    def _handle_frame(self, frame, analysis_data):
        self.ui.display_frame(frame)
        self.ui.update_detection_info(analysis_data)
        self.ui.update_warning_status(analysis_data.get('warning_text'), analysis_data.get('risk_level'))
        if analysis_data.get('weather_analysis'):
            weather_data = analysis_data['weather_analysis']
            if weather_data.weather_data:
                self.ui.update_weather_display(
                    weather_data.weather_data.condition,
                    weather_data.weather_data.to_dict()
                )

    def run(self):
        self.ui.show()
        self.loop_thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.loop_thread.start()
        self.app.exec_()
        self.stop_system()

    def start_system(self):
        self.ui.set_start_button_enabled(False)
        self.processor.start()
        if self.gps_service:
            self.gps_service.start()
        self.ui.update_status_log("🚀 FCW System Started")

    def stop_system(self):
        if self.stopping: return
        self.stopping = True
        print("Stopping real-time system...")
        if self.gps_service:
            self.gps_service.stop()
            self.gps_service.wait(2000) # Wait for GPS thread to finish
        self.processor.stop()
        self.processor.wait(2000)
        if self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if hasattr(self, 'loop_thread') and self.loop_thread.is_alive():
            self.loop_thread.join()
        
        self.ui.set_start_button_enabled(True)
        self.ui.close()

class OfflineApplication:
    """Orchestrates the OFFLINE analysis application."""
    def __init__(self, filepath):
        self.app = get_qt_app()
        self.ui = OfflineAnalysisInterface()
        # In offline mode, we don't need a separate asyncio loop thread
        self.processor = OfflineVideoProcessor(
            video_path=filepath,
            detector=create_detector(**config.get_detection_config()),
            tracker=KalmanTracker(),
            collision_predictor=CollisionPredictor(),
            warning_generator=GeminiWarningGenerator(),
            loop=None 
        )
        self._connect_signals()

    def _connect_signals(self):
        self.processor.frame_processed.connect(self._handle_frame)
        self.processor.stats_updated.connect(self.ui.update_performance_metrics)
        self.processor.position_updated.connect(self.ui.update_frame_position)
        self.processor.total_frames_ready.connect(self.ui.set_total_frames)
        self.ui.play_requested.connect(self.processor.play)
        self.ui.pause_requested.connect(self.processor.pause)
        self.ui.stop_requested.connect(self.stop_system)
        self.ui.seek_requested.connect(self.processor.seek)

    def _handle_frame(self, frame, analysis_data):
        processed_frame = draw_detections(frame, analysis_data.get('tracked_objects', []), analysis_data.get('collision_analysis', {}))
        self.ui.display_frame(processed_frame)
        self.ui.update_detection_info(analysis_data)
        self.ui.update_warning_status(analysis_data.get('warning_text'), analysis_data.get('risk_level'))

    def run(self):
        self.ui.show()
        self.processor.start()
        self.app.exec_()
        self.stop_system()
        
    def stop_system(self):
        print("Stopping offline processor...")
        self.processor.stop()
        self.processor.wait(2000)
        self.ui.close()

def main():
    initialize_gemini()
    logging.basicConfig(level=config.LOG_LEVEL.upper(), format='%(asctime)s - %(levelname)s - %(message)s')
    
    app = get_qt_app()
    
    class DialogResult:
        def __init__(self):
            self.mode = None
            self.filepath = None
        def set_selection(self, mode, filepath):
            self.mode = mode
            self.filepath = filepath
    
    result = DialogResult()
    dialog = ModeSelectionDialog()
    dialog.mode_selected.connect(result.set_selection)
    
    if dialog.exec_() != QDialog.Accepted or not result.mode:
        print("No mode selected. Exiting.")
        sys.exit(0)

    if result.mode == 'realtime':
        app_instance = FCWApplication()
    else:
        app_instance = OfflineApplication(result.filepath)
        
    app_instance.run()

if __name__ == "__main__":
    main()