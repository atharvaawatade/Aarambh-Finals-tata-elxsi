"""
Offline Video Processor for FCW System
Handles video file processing, playback control, and analysis for accuracy testing.
"""

import cv2
import time
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
import logging

class OfflineVideoProcessor(QThread):
    """
    Processes a video file offline, frame by frame, and emits results.
    Includes playback controls like play, pause, and seek.
    """
    # Signals for UI updates
    frame_processed = pyqtSignal(np.ndarray, dict)
    stats_updated = pyqtSignal(dict)
    position_updated = pyqtSignal(int, int, float) # current_frame, total_frames, elapsed_time
    total_frames_ready = pyqtSignal(int)
    playback_finished = pyqtSignal()

    def __init__(self, video_path, detector, tracker, collision_predictor, warning_generator, loop):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.video_path = video_path
        
        # Core analysis components
        self.detector = detector
        self.tracker = tracker
        self.collision_predictor = collision_predictor
        self.warning_generator = warning_generator
        self.loop = loop
        
        # Playback state
        self.cap = None
        self._running = False
        self._paused = True
        self.total_frames = 0
        self.current_frame_num = 0
        
        # Performance tracking
        self.start_time = 0
        self.processing_times = []

    def run(self):
        """Main processing loop."""
        if not self._initialize_capture():
            return

        self._running = True
        self.start_time = time.time()

        while self._running and self.current_frame_num < self.total_frames:
            if not self._paused:
                loop_start_time = time.perf_counter()
                
                ret, frame = self.cap.read()
                if not ret:
                    self.logger.info("End of video file reached.")
                    break

                # Process the frame
                analysis_data = self._process_frame(frame)
                
                # Emit results for the UI
                self.frame_processed.emit(frame, analysis_data)
                
                # Update performance metrics
                processing_time_ms = (time.perf_counter() - loop_start_time) * 1000
                self.processing_times.append(processing_time_ms)
                if len(self.processing_times) > 100:
                    self.processing_times.pop(0)
                
                avg_latency = np.mean(self.processing_times) if self.processing_times else 0
                fps = 1000 / avg_latency if avg_latency > 0 else 0

                self.stats_updated.emit({'fps': fps, 'latency_ms': avg_latency})
                self.position_updated.emit(self.current_frame_num, self.total_frames, time.time() - self.start_time)

                self.current_frame_num += 1
            else:
                # In a paused state, sleep briefly to avoid busy-waiting
                self.msleep(50)
        
        self.playback_finished.emit()
        self.logger.info("Offline processing finished.")

    def _initialize_capture(self):
        """Opens the video file and gets properties."""
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            self.logger.error(f"Failed to open video file: {self.video_path}")
            return False
        
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.total_frames_ready.emit(self.total_frames)
        self.logger.info(f"Video loaded: {self.video_path} ({self.total_frames} frames)")
        return True

    def _process_frame(self, frame):
        """Runs a single frame through the analysis pipeline."""
        detections = self.detector.detect(frame)
        tracked_objects = self.tracker.update(detections)
        collision_analysis = self.collision_predictor.analyze_collision_risk(tracked_objects, frame)
        
        # Note: Using synchronous warning generation for simplicity in offline mode
        warning_text = self.warning_generator.generate_warning(collision_analysis)

        return {
            "tracked_objects": tracked_objects,
            "collision_analysis": collision_analysis,
            "warning_text": warning_text,
            "risk_level": collision_analysis.get('risk_level', 'None')
        }

    def play(self):
        self._paused = False

    def pause(self):
        self._paused = True

    def stop(self):
        self._running = False

    def seek(self, frame_number):
        if self.cap and 0 <= frame_number < self.total_frames:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            self.current_frame_num = frame_number
            # Update time based on new frame number
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            elapsed_time = frame_number / fps if fps > 0 else 0
            self.start_time = time.time() - elapsed_time 