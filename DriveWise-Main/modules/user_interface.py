from abc import ABC, abstractmethod
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                             QHBoxLayout, QWidget, QPushButton, QDialog, 
                             QFileDialog, QSlider, QStyle,
                             QButtonGroup, QRadioButton, QTextEdit, QFrame, QGroupBox, QProgressBar)
from PyQt5.QtGui import QImage, QPixmap, QFont, QPalette, QColor, QPainter, QPen, QPolygon, QBrush
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint, QRectF
import sys
import cv2
import time
import config
import random

# Enhanced Style constants for enterprise look with weather themes
WEATHER_THEMES = {
    'sunny': {
        'background': 'qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #f39c12, stop: 1 #e67e22)',
        'accent': '#f1c40f',
        'text': '#2c3e50',
        'icon': '☀️'
    },
    'rainy': {
        'background': 'qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #3498db, stop: 1 #2980b9)',
        'accent': '#5dade2',
        'text': '#ecf0f1',
        'icon': '🌧️'
    },
    'cloudy': {
        'background': 'qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #7f8c8d, stop: 1 #95a5a6)',
        'accent': '#bdc3c7',
        'text': '#2c3e50',
        'icon': '☁️'
    },
    'foggy': {
        'background': 'qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #95a5a6, stop: 1 #7f8c8d)',
        'accent': '#bdc3c7',
        'text': '#2c3e50',
        'icon': '🌫️'
    },
    'snowy': {
        'background': 'qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ecf0f1, stop: 1 #bdc3c7)',
        'accent': '#3498db',
        'text': '#2c3e50',
        'icon': '❄️'
    },
    'stormy': {
        'background': 'qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #2c3e50, stop: 1 #34495e)',
        'accent': '#e74c3c',
        'text': '#ecf0f1',
        'icon': '⛈️'
    },
    'clear': {
        'background': 'qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #2c3e50, stop: 1 #34495e)',
        'accent': '#3498db',
        'text': '#ecf0f1',
        'icon': '🌙'
    }
}

ENTERPRISE_THEME = f"""
    QMainWindow {{
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                   stop: 0 #2c3e50, stop: 1 #34495e);
        color: #ecf0f1;
        font-family: 'Segoe UI', 'Arial', sans-serif;
    }}
    QLabel {{
        color: #ecf0f1;
        font-size: 14px;
        font-weight: 500;
        margin: 3px;
    }}
    QGroupBox {{
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                   stop: 0 #34495e, stop: 1 #2c3e50);
        border: 2px solid #3498db;
        border-radius: 12px;
        font-weight: bold;
        font-size: 15px;
        color: #3498db;
        margin-top: 15px;
        padding-top: 20px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 15px;
        padding: 0 8px 0 8px;
        color: #3498db;
        font-weight: bold;
    }}
    QTextEdit {{
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                   stop: 0 #2c3e50, stop: 1 #1a252f);
        border: 1px solid #34495e;
        border-radius: 8px;
        color: #ecf0f1;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 12px;
        padding: 10px;
        selection-background-color: #3498db;
    }}
    QPushButton {{
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                   stop: 0 #3498db, stop: 1 #2980b9);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 14px;
        min-width: 120px;
    }}
    QPushButton:hover {{
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                   stop: 0 #5dade2, stop: 1 #3498db);
    }}
    QPushButton:pressed {{
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                   stop: 0 #2980b9, stop: 1 #1f618d);
    }}
    QPushButton:disabled {{
        background: #7f8c8d;
        color: #bdc3c7;
    }}
    QProgressBar {{
        border: 2px solid #34495e;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        color: #ecf0f1;
    }}
    QProgressBar::chunk {{
        background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                   stop: 0 #27ae60, stop: 1 #2ecc71);
        border-radius: 6px;
    }}
"""

METRIC_STYLE = "font-size: 12px; margin: 2px; color: #4CAF50;"

GROUP_BOX_STYLE = """
    QGroupBox {
        background-color: #2d2d2d;
        border: 1px solid #404040;
        border-radius: 8px;
        font-weight: bold;
        font-size: 14px;
        margin-top: 10px;
        padding-top: 15px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px 0 5px;
    }
"""

TEXT_EDIT_STYLE = """
    QTextEdit {
        background-color: #1e1e1e;
        border: 1px solid #404040;
        border-radius: 4px;
        color: #ffffff;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 11px;
        padding: 8px;
    }
"""

WARNING_NORMAL_STYLE = """
    QLabel {
        font-size: 14px; 
        padding: 20px; 
        border-radius: 10px;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
"""

WARNING_CRITICAL_STYLE = """
    QLabel {
        font-size: 14px; 
        padding: 20px; 
        border-radius: 10px;
        background-color: #f44336;
        color: white;
        font-weight: bold;
    }
"""

BUTTON_STYLE = """
    QPushButton {
        background-color: #0078d4;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-weight: bold;
        font-size: 14px;
    }
    QPushButton:hover {
        background-color: #106ebe;
    }
    QPushButton:pressed {
        background-color: #005a9e;
    }
    QPushButton:disabled {
        background-color: #333333;
        color: #888888;
    }
"""

class UserInterface(ABC):
    @abstractmethod
    def display_frame(self, frame: np.ndarray):
        """
        Displays a single frame to the user.
        """
        pass

    @abstractmethod
    def run(self):
        """
        Starts the UI event loop.
        """
        pass

class ModeSelectionDialog(QDialog):
    """Dialog to select the application mode."""
    # Signal now emits mode and an optional filepath
    mode_selected = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FCW System - Select Mode")
        self.setFixedSize(450, 250)
        self.setStyleSheet(ENTERPRISE_THEME)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel("Select Operating Mode", self)
        title.setFont(QFont('Segoe UI', 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        button_layout = QHBoxLayout()
        
        # Real-time button
        self.realtime_button = QPushButton("🚀 Real-time System", self)
        self.realtime_button.clicked.connect(lambda: self.select_mode('realtime'))
        button_layout.addWidget(self.realtime_button)
        
        # Offline button
        self.offline_button = QPushButton("🎬 Analyze Recorded Video", self)
        self.offline_button.clicked.connect(lambda: self.select_mode('offline'))
        button_layout.addWidget(self.offline_button)
        
        layout.addLayout(button_layout)
        
    def select_mode(self, mode):
        filepath = ""
        if mode == 'offline':
            # Open file dialog to select a video
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            filepath, _ = QFileDialog.getOpenFileName(
                self, 
                "Select Video File", 
                "", 
                "Video Files (*.mp4 *.avi *.mov *.mkv);;All Files (*)", 
                options=options
            )
            if not filepath:
                # User cancelled the dialog
                return
        
        self.mode_selected.emit(mode, filepath)
        self.accept()

class EnhancedRealtimeInterface(QMainWindow):
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚗 FCW System - Real-Time Dashboard")
        self.setGeometry(100, 100, 1600, 900)
        self.setStyleSheet(ENTERPRISE_THEME)
        
        # Add title bar with system info
        self.setWindowTitle(f"{config.SYSTEM_NAME} v{config.VERSION} - {config.COMPANY}")
        
        # Weather state tracking
        self.current_weather_condition = 'clear'
        self.weather_animation_timer = QTimer()
        self.weather_animation_timer.timeout.connect(self._animate_weather_effects)
        
        # Main layout
        main_layout = QHBoxLayout()
        
        # --- Left Panel: Video Feed & Controls ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # System header with weather indicator
        header_layout = QHBoxLayout()
        
        system_title = QLabel(f"🚗 {config.SYSTEM_NAME}")
        system_title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #3498db;
                margin: 10px;
            }
        """)
        header_layout.addWidget(system_title)
        
        # Weather indicator
        self.weather_indicator = QLabel("🔄 Fetching...")
        self.weather_indicator.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #bdc3c7;
                margin: 10px;
                padding: 8px 16px;
                border-radius: 20px;
                background-color: rgba(127, 140, 141, 0.2);
            }
        """)
        header_layout.addWidget(self.weather_indicator)
        
        header_layout.addStretch()
        
        # Status indicator
        self.status_indicator = QLabel("● OFFLINE")
        self.status_indicator.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #e74c3c;
                margin: 10px;
                padding: 8px 16px;
                border-radius: 20px;
                background-color: rgba(231, 76, 60, 0.2);
            }
        """)
        header_layout.addWidget(self.status_indicator)
        
        left_layout.addLayout(header_layout)

        # Video display label with enhanced styling and weather overlay
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("""
            QLabel {
                border: 3px solid #3498db;
                border-radius: 12px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #2c3e50, stop: 1 #1a252f);
                color: #bdc3c7;
                font-size: 16px;
                font-weight: 500;
                padding: 30px;
            }
        """)
        self.video_label.setText("📹 Camera Ready\n\nPress 'Start System' to begin real-time analysis")
        self.video_label.setMinimumSize(960, 540)
        
        # Weather overlay for video (initially hidden)
        self.weather_overlay = QLabel(self.video_label)
        self.weather_overlay.setGeometry(0, 0, 960, 540)
        self.weather_overlay.setStyleSheet("background: transparent;")
        self.weather_overlay.hide()
        
        left_layout.addWidget(self.video_label, 1)
        
        # --- Enhanced Control Panel ---
        control_panel = QWidget()
        control_panel.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #34495e, stop: 1 #2c3e50);
                border-radius: 12px;
                margin: 5px;
                padding: 10px;
            }
        """)
        control_layout = QHBoxLayout(control_panel)
        
        self.start_button = QPushButton("🚀 START SYSTEM")
        self.start_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #27ae60, stop: 1 #229954);
                font-size: 16px;
                font-weight: bold;
                padding: 15px 30px;
                min-width: 150px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #2ecc71, stop: 1 #27ae60);
            }
        """)
        self.start_button.clicked.connect(self.start_requested.emit)
        control_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("🛑 STOP SYSTEM")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #e74c3c, stop: 1 #c0392b);
                font-size: 16px;
                font-weight: bold;
                padding: 15px 30px;
                min-width: 150px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #ec7063, stop: 1 #e74c3c);
            }
        """)
        self.stop_button.clicked.connect(self.stop_requested.emit)
        control_layout.addWidget(self.stop_button)

        # Add system info
        info_label = QLabel(f"v{config.VERSION} | Build {config.BUILD_DATE}")
        info_label.setStyleSheet("""
            QLabel {
                color: #95a5a6;
                font-size: 12px;
                margin: 10px;
            }
        """)
        control_layout.addStretch()
        control_layout.addWidget(info_label)

        left_layout.addWidget(control_panel)
        main_layout.addWidget(left_panel, 3)

        # --- Right Panel: Enhanced Information Dashboard ---
        right_panel = QWidget()
        right_panel.setMaximumWidth(450)
        info_layout = QVBoxLayout(right_panel)
        
        # Performance metrics with progress bars
        metrics_group = QGroupBox("📊 System Performance")
        metrics_layout = QVBoxLayout(metrics_group)
        
        # FPS with progress bar
        fps_container = QHBoxLayout()
        self.fps_label = QLabel("FPS: --")
        self.fps_label.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 14px;")
        self.fps_progress = QProgressBar()
        self.fps_progress.setRange(0, 60)
        self.fps_progress.setTextVisible(False)
        self.fps_progress.setMaximumHeight(8)
        fps_container.addWidget(self.fps_label)
        fps_container.addWidget(self.fps_progress)
        metrics_layout.addLayout(fps_container)
        
        # Latency with progress bar
        latency_container = QHBoxLayout()
        self.latency_label = QLabel("Latency: -- ms")
        self.latency_label.setStyleSheet("color: #f39c12; font-weight: bold; font-size: 14px;")
        self.latency_progress = QProgressBar()
        self.latency_progress.setRange(0, 100)
        self.latency_progress.setTextVisible(False)
        self.latency_progress.setMaximumHeight(8)
        latency_container.addWidget(self.latency_label)
        latency_container.addWidget(self.latency_progress)
        
        # Speedometer Widget
        self.speedometer = SpeedometerWidget()
        self.speedometer.setMinimumHeight(150)
        metrics_layout.addWidget(self.speedometer)

        # Digital Speed Display
        self.digital_speed_label = QLabel("0")
        self.digital_speed_label.setAlignment(Qt.AlignCenter)
        self.digital_speed_label.setStyleSheet("""
            QLabel {
                font-size: 48px;
                font-weight: bold;
                color: #ecf0f1;
                margin-top: -30px; /* Overlap with speedometer slightly */
                margin-bottom: 10px;
            }
        """)
        metrics_layout.addWidget(self.digital_speed_label)
        
        # Frame count
        self.frame_count_label = QLabel("Frames Processed: 0")
        self.frame_count_label.setStyleSheet("color: #3498db; font-weight: bold; font-size: 14px;")
        metrics_layout.addWidget(self.frame_count_label)
        
        info_layout.addWidget(metrics_group)

        # Object detection info with enhanced display
        detection_group = QGroupBox("🎯 Object Detection & Tracking")
        detection_layout = QVBoxLayout(detection_group)
        self.detection_text = QTextEdit()
        self.detection_text.setReadOnly(True)
        self.detection_text.setText("System ready. No objects detected.")
        self.detection_text.setMaximumHeight(180)
        detection_layout.addWidget(self.detection_text)
        info_layout.addWidget(detection_group)
        
        # Enhanced warning system
        warning_group = QGroupBox("⚠️ Collision Warning System")
        warning_layout = QVBoxLayout(warning_group)
        self.warning_label = QLabel("System Standby")
        self.warning_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                padding: 25px;
                border-radius: 12px;
                color: white;
                font-weight: bold;
                text-align: center;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #27ae60, stop: 1 #229954);
            }
        """)
        self.warning_label.setAlignment(Qt.AlignCenter)
        self.warning_label.setWordWrap(True)
        self.warning_label.setMinimumHeight(120)
        warning_layout.addWidget(self.warning_label)
        info_layout.addWidget(warning_group)
        
        # Enhanced system log with AI insights
        status_group = QGroupBox("🤖 AI Analysis & System Log")
        status_layout = QVBoxLayout(status_group)
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setText(f"🎯 {config.SYSTEM_NAME} Ready\n📡 Gemini AI Integration Active\n⚡ Press 'Start System' to begin analysis...")
        status_layout.addWidget(self.status_text)
        info_layout.addWidget(status_group)
        
        info_layout.addStretch()

        main_layout.addWidget(right_panel, 1)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.stop_button.setEnabled(False)

    def set_start_button_enabled(self, enabled):
        self.start_button.setEnabled(enabled)
        self.stop_button.setEnabled(not enabled)
        
        # Update status indicator
        if not enabled:  # System is running
            self.status_indicator.setText("● ACTIVE")
            self.status_indicator.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    font-weight: bold;
                    color: #27ae60;
                    margin: 10px;
                    padding: 8px 16px;
                    border-radius: 20px;
                    background-color: rgba(39, 174, 96, 0.2);
                }
            """)
        else:  # System is stopped
            self.status_indicator.setText("● OFFLINE")
            self.status_indicator.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    font-weight: bold;
                    color: #e74c3c;
                    margin: 10px;
                    padding: 8px 16px;
                    border-radius: 20px;
                    background-color: rgba(231, 76, 60, 0.2);
                }
            """)

    def update_status_log(self, message):
        # Add timestamp and format message
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.status_text.append(formatted_message)
        
        # Keep log manageable (last 100 lines)
        text = self.status_text.toPlainText()
        lines = text.split('\n')
        if len(lines) > 100:
            self.status_text.setPlainText('\n'.join(lines[-100:]))

    def display_frame(self, frame: np.ndarray):
        if frame is None:
            self.video_label.setText("🚫 Camera feed lost\n\nPress 'Stop' and restart the system")
            return
            
        # Convert BGR (OpenCV) to RGB
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        
        # Scale to fit the label while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_label.setPixmap(scaled_pixmap)

    def update_performance_metrics(self, stats: dict):
        """Update performance metric labels from a dictionary."""
        self.fps_label.setText(f"FPS: {stats.get('fps', 0):.1f}")
        self.latency_label.setText(f"Latency: {stats.get('latency_ms', 0):.1f} ms")
        self.frame_count_label.setText(f"Frames Processed: {stats.get('frames_processed', 0)}")
        
        # Update progress bars
        self.fps_progress.setValue(min(60, int(stats.get('fps', 0))))
        self.latency_progress.setValue(min(100, int(stats.get('latency_ms', 0))))
        
        # Color code performance indicators
        if stats.get('fps', 0) >= 25:
            fps_color = "#27ae60"  # Green
        elif stats.get('fps', 0) >= 15:
            fps_color = "#f39c12"  # Orange
        else:
            fps_color = "#e74c3c"  # Red
            
        if stats.get('latency_ms', 0) <= 50:
            latency_color = "#27ae60"  # Green
        elif stats.get('latency_ms', 0) <= 100:
            latency_color = "#f39c12"  # Orange
        else:
            latency_color = "#e74c3c"  # Red
            
        self.fps_label.setStyleSheet(f"color: {fps_color}; font-weight: bold; font-size: 14px;")
        self.latency_label.setStyleSheet(f"color: {latency_color}; font-weight: bold; font-size: 14px;")
    
    def update_vehicle_speed(self, speed_kmh: float):
        """Updates the vehicle speed display on both widgets."""
        self.speedometer.set_speed(speed_kmh)
        if speed_kmh < 0:
            self.digital_speed_label.setText("--")
        else:
            self.digital_speed_label.setText(f"{speed_kmh:.0f}")

    def update_detection_info(self, analysis_data: dict):
        """Updates the detection info panel with formatted data."""
        
        info_text = "📊 DETECTION STATUS\n"
        info_text += f"  - Objects Detected: {analysis_data.get('detections', 0)}\n"
        info_text += f"  - Objects Tracked: {len(analysis_data.get('tracked_objects', []))}\n"
        info_text += f"  - Risk Level: {analysis_data.get('risk_level', 'N/A')}\n\n"

        primary_threat = analysis_data.get('primary_threat')
        if primary_threat:
            info_text += "🎯 PRIMARY THREAT\n"
            info_text += f"  - Vehicle ID: {primary_threat.get('id', 'N/A')}\n"
            info_text += f"  - Class: {primary_threat.get('class_name', 'N/A')}\n"
            info_text += f"  - Distance: {primary_threat.get('distance', 0):.1f} m\n"
            info_text += f"  - Speed: {primary_threat.get('speed', 0):.1f} km/h\n"
            ttc = primary_threat.get('ttc', float('inf'))
            info_text += f"  - TTC: {ttc:.1f} s\n" if ttc != float('inf') else "  - TTC: N/A\n"

        self.detection_text.setText(info_text)

    def update_warning_status(self, warning_text, risk_level):
        """Updates the warning status display."""
        self.warning_label.setText(warning_text)

        # Enhanced styling based on risk level
        if risk_level == "Critical":
            style = """
                QLabel {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                               stop: 0 #e74c3c, stop: 1 #c0392b);
                    animation: blink 1s infinite;
                }
            """
        elif risk_level == "High":
            style = """
                QLabel {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                               stop: 0 #e67e22, stop: 1 #d35400);
                }
            """
        elif risk_level == "Medium":
            style = """
                QLabel {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                               stop: 0 #f39c12, stop: 1 #e67e22);
                }
            """
        elif risk_level == "Low":
            style = """
                QLabel {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                               stop: 0 #f1c40f, stop: 1 #f39c12);
                }
            """
        else:  # None or safe
            style = """
                QLabel {
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                               stop: 0 #27ae60, stop: 1 #229954);
                }
            """

        full_style = f"""
            QLabel {{
                font-size: 18px;
                padding: 25px;
                border-radius: 12px;
                color: white;
                font-weight: bold;
                text-align: center;
                {style.split('{')[1].split('}')[0] if '{' in style else ''}
            }}
        """
        self.warning_label.setStyleSheet(full_style)

    def update_weather_display(self, weather_condition: str, weather_data: dict = None):
        """Update weather display and UI theme based on current weather"""
        try:
            # Normalize weather condition
            condition = weather_condition.lower()
            
            # Map weather conditions to our themes
            if condition in ['sunny', 'clear', 'sun']:
                theme_key = 'sunny'
            elif condition in ['rainy', 'rain', 'light_rain', 'heavy_rain', 'drizzle']:
                theme_key = 'rainy'
            elif condition in ['cloudy', 'overcast', 'partly_cloudy']:
                theme_key = 'cloudy'
            elif condition in ['foggy', 'fog', 'mist', 'haze']:
                theme_key = 'foggy'
            elif condition in ['snowy', 'snow', 'sleet']:
                theme_key = 'snowy'
            elif condition in ['stormy', 'thunderstorm', 'storm']:
                theme_key = 'stormy'
            else:
                theme_key = 'clear'
            
            self.current_weather_condition = theme_key
            theme = WEATHER_THEMES[theme_key]
            
            # Update weather indicator
            weather_text = f"{theme['icon']} {condition.title()}"
            if weather_data:
                temp = weather_data.get('temperature', 0)
                weather_text += f" {temp:.0f}°C"
            
            self.weather_indicator.setText(weather_text)
            self.weather_indicator.setStyleSheet(f"""
                QLabel {{
                    font-size: 18px;
                    font-weight: bold;
                    color: {theme['text']};
                    margin: 10px;
                    padding: 8px 16px;
                    border-radius: 20px;
                    background: {theme['background']};
                    border: 2px solid {theme['accent']};
                }}
            """)
            
            # Update video border to match weather theme
            self.video_label.setStyleSheet(f"""
                QLabel {{
                    border: 3px solid {theme['accent']};
                    border-radius: 12px;
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                               stop: 0 #2c3e50, stop: 1 #1a252f);
                    color: #bdc3c7;
                    font-size: 16px;
                    font-weight: 500;
                    padding: 30px;
                }}
            """)
            
            # Start weather animations
            self._start_weather_animation(theme_key)
            
        except Exception as e:
            print(f"Error updating weather display: {e}")

    def _start_weather_animation(self, weather_type: str):
        """Start weather-specific animations"""
        try:
            self.weather_overlay.show()
            
            if weather_type == 'rainy':
                self._create_rain_effect()
                self.weather_animation_timer.start(100)  # Update every 100ms
            elif weather_type == 'snowy':
                self._create_snow_effect()
                self.weather_animation_timer.start(150)  # Update every 150ms
            elif weather_type == 'foggy':
                self._create_fog_effect()
                self.weather_animation_timer.start(200)  # Update every 200ms
            elif weather_type == 'stormy':
                self._create_storm_effect()
                self.weather_animation_timer.start(50)   # Update every 50ms for lightning
            else:
                # Clear weather - no animation
                self.weather_overlay.hide()
                self.weather_animation_timer.stop()
                
        except Exception as e:
            print(f"Error starting weather animation: {e}")

    def _create_rain_effect(self):
        """Create rain effect overlay"""
        rain_style = """
            QLabel {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(52, 152, 219, 0.1),
                    stop: 0.3 rgba(52, 152, 219, 0.05),
                    stop: 0.7 rgba(52, 152, 219, 0.1),
                    stop: 1 rgba(52, 152, 219, 0.2));
                border: none;
            }
        """
        self.weather_overlay.setStyleSheet(rain_style)
        self.weather_overlay.setText("🌧️ 🌧️ 🌧️\n💧 💧 💧\n🌧️ 🌧️ 🌧️")
        self.weather_overlay.setAlignment(Qt.AlignCenter)

    def _create_snow_effect(self):
        """Create snow effect overlay"""
        snow_style = """
            QLabel {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(255, 255, 255, 0.1),
                    stop: 0.5 rgba(255, 255, 255, 0.05),
                    stop: 1 rgba(255, 255, 255, 0.15));
                border: none;
                color: white;
            }
        """
        self.weather_overlay.setStyleSheet(snow_style)
        self.weather_overlay.setText("❄️ ❄️ ❄️\n🌨️ 🌨️ 🌨️\n❄️ ❄️ ❄️")
        self.weather_overlay.setAlignment(Qt.AlignCenter)

    def _create_fog_effect(self):
        """Create fog effect overlay"""
        fog_style = """
            QLabel {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(149, 165, 166, 0.2),
                    stop: 0.5 rgba(149, 165, 166, 0.3),
                    stop: 1 rgba(149, 165, 166, 0.2));
                border: none;
                color: #7f8c8d;
            }
        """
        self.weather_overlay.setStyleSheet(fog_style)
        self.weather_overlay.setText("🌫️ 🌫️ 🌫️\n🌫️ 🌫️ 🌫️\n🌫️ 🌫️ 🌫️")
        self.weather_overlay.setAlignment(Qt.AlignCenter)

    def _create_storm_effect(self):
        """Create storm effect overlay"""
        storm_style = """
            QLabel {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 rgba(44, 62, 80, 0.3),
                    stop: 0.5 rgba(231, 76, 60, 0.1),
                    stop: 1 rgba(44, 62, 80, 0.3));
                border: none;
                color: #e74c3c;
            }
        """
        self.weather_overlay.setStyleSheet(storm_style)
        self.weather_overlay.setText("⚡ ⚡ ⚡\n⚡ ⚡ ⚡\n⚡ ⚡ ⚡")
        self.weather_overlay.setAlignment(Qt.AlignCenter)

    def _animate_weather_effects(self):
        """Animate weather effects"""
        try:
            if self.current_weather_condition == 'rainy':
                # Animate rain by changing opacity
                current_text = self.weather_overlay.text()
                if "💧" in current_text:
                    self.weather_overlay.setText("🌧️ 🌧️ 🌧️\n🌧️ 🌧️ 🌧️\n💧 💧 💧")
                else:
                    self.weather_overlay.setText("🌧️ 🌧️ 🌧️\n💧 💧 💧\n🌧️ 🌧️ 🌧️")
                    
            elif self.current_weather_condition == 'snowy':
                # Animate snow falling
                current_text = self.weather_overlay.text()
                if "🌨️" in current_text:
                    self.weather_overlay.setText("❄️ ❄️ ❄️\n❄️ ❄️ ❄️\n🌨️ 🌨️ 🌨️")
                else:
                    self.weather_overlay.setText("❄️ ❄️ ❄️\n🌨️ 🌨️ 🌨️\n❄️ ❄️ ❄️")
                    
            elif self.current_weather_condition == 'stormy':
                # Animate lightning flashes
                if random.random() < 0.3:  # 30% chance of lightning flash
                    flash_style = """
                        QLabel {
                            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                stop: 0 rgba(241, 196, 15, 0.4),
                                stop: 0.5 rgba(255, 255, 255, 0.3),
                                stop: 1 rgba(241, 196, 15, 0.4));
                            border: none;
                            color: #f1c40f;
                        }
                    """
                    self.weather_overlay.setStyleSheet(flash_style)
                    self.weather_overlay.setText("⚡ ⚡ ⚡\n⚡ ⚡ ⚡\n⚡ ⚡ ⚡")
                else:
                    self._create_storm_effect()
                    
        except Exception as e:
            print(f"Error animating weather: {e}")

    def run(self):
        self.show()
        app = get_qt_app()
        app.exec_()

    def closeEvent(self, event):
        print("Realtime UI closing, requesting system stop.")
        self.stop_requested.emit()
        event.accept()

class SpeedometerWidget(QWidget):
    """A custom widget to display speed like a car speedometer."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._speed = 0
        self.max_speed = 220  # km/h

    def set_speed(self, speed: float):
        if speed < 0:
            speed = 0
        if speed > self.max_speed:
            speed = self.max_speed
        self._speed = speed
        self.update()  # Trigger a repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        side = min(self.width(), self.height())
        painter.translate(self.width() / 2, self.height() / 2)
        painter.scale(side / 200.0, side / 200.0)

        self._draw_background(painter)
        self._draw_ticks(painter)
        self._draw_needle(painter)
        self._draw_text(painter)

    def _draw_background(self, painter):
        painter.save()
        painter.setPen(Qt.NoPen)
        
        # Outer dial
        painter.setBrush(QColor("#34495e"))
        painter.drawEllipse(-95, -95, 190, 190)

        # Inner dial
        painter.setBrush(QColor("#2c3e50"))
        painter.drawEllipse(-85, -85, 170, 170)
        painter.restore()

    def _draw_ticks(self, painter):
        painter.save()
        painter.setPen(QColor("#ecf0f1"))
        start_angle = -120  # Corresponds to 210 degrees on a standard circle
        angle_range = 240   # -120 to +120
        
        # Major ticks
        for i in range(self.max_speed // 20 + 1):
            angle = start_angle + (i * 20 / self.max_speed) * angle_range
            painter.save()
            painter.rotate(angle)
            painter.drawLine(70, 0, 85, 0)
            
            # Draw text
            font = painter.font()
            font.setPointSize(8)
            painter.setFont(font)
            text_point = QPoint(60, 0)
            painter.drawText(text_point, str(i * 20))
            painter.restore()
        painter.restore()

    def _draw_needle(self, painter):
        painter.save()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#e74c3c"))

        # Rotate painter to the correct angle for the speed
        start_angle = -120
        angle_range = 240
        angle = start_angle + (self._speed / self.max_speed) * angle_range
        
        painter.rotate(angle)

        # Define the needle shape
        needle_poly = QPolygon([
            QPoint(0, -5),
            QPoint(0, 5),
            QPoint(70, 0)
        ])
        painter.drawPolygon(needle_poly)
        
        # Center hub
        painter.setBrush(QColor("#bdc3c7"))
        painter.drawEllipse(-6, -6, 12, 12)
        painter.restore()

    def _draw_text(self, painter):
        # This is now handled by the separate QLabel, so we can remove the digital text from the widget itself
        # to avoid visual clutter. We'll just keep the units.
        painter.save()
        painter.setPen(QColor("#bdc3c7"))
        font = painter.font()
        font.setPointSize(10)
        font.setBold(False)
        painter.setFont(font)
        units_rect = QRectF(-50, 40, 100, 20)
        painter.drawText(units_rect, Qt.AlignCenter, "km/h")
        painter.restore()

class OfflineAnalysisInterface(QMainWindow):
    """UI for offline video analysis and accuracy testing."""
    play_requested = pyqtSignal()
    pause_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    seek_requested = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{config.SYSTEM_NAME} - Offline Analysis")
        self.setGeometry(100, 100, 1600, 900)
        self.setStyleSheet(ENTERPRISE_THEME)

        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Left side for video
        left_layout = QVBoxLayout()
        
        self.video_label = QLabel("Video will be displayed here.")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(800, 600)
        self.video_label.setStyleSheet("background-color: black; border: 2px solid #3498db; border-radius: 8px;")
        left_layout.addWidget(self.video_label)
        
        # Playback controls
        controls_layout = QHBoxLayout()
        self.play_pause_button = QPushButton()
        self.play_pause_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_pause_button.clicked.connect(self._toggle_play_pause)
        
        self.stop_button = QPushButton()
        self.stop_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stop_button.clicked.connect(self.stop_requested)
        
        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.sliderMoved.connect(self.seek_requested)

        self.time_label = QLabel("00:00 / 00:00")

        controls_layout.addWidget(self.play_pause_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.seek_slider)
        controls_layout.addWidget(self.time_label)
        left_layout.addLayout(controls_layout)

        # Right side for analysis data (similar to realtime UI)
        right_layout = QVBoxLayout()
        self._create_info_panels(right_layout)
        
        main_layout.addLayout(left_layout, 2) # Video takes 2/3 of space
        main_layout.addLayout(right_layout, 1) # Info takes 1/3 of space
        
        self.is_playing = False

    def _create_info_panels(self, parent_layout):
        """Create panels for displaying analysis data."""
        # Performance Metrics Box
        performance_box = QGroupBox("Performance Metrics")
        performance_layout = QVBoxLayout(performance_box)
        self.fps_label = QLabel("FPS: N/A")
        self.latency_label = QLabel("Latency: N/A")
        self.frame_count_label = QLabel("Frame: N/A")
        self.inference_time_label = QLabel("Inference Time: N/A")
        performance_layout.addWidget(self.fps_label)
        performance_layout.addWidget(self.latency_label)
        performance_layout.addWidget(self.frame_count_label)
        performance_layout.addWidget(self.inference_time_label)
        parent_layout.addWidget(performance_box)
        
        # Detection Info Box
        detection_box = QGroupBox("Object Detections")
        detection_layout = QVBoxLayout(detection_box)
        self.detection_info_text = QTextEdit()
        self.detection_info_text.setReadOnly(True)
        detection_layout.addWidget(self.detection_info_text)
        parent_layout.addWidget(detection_box)

        # Warning Status Box
        warning_box = QGroupBox("System Warnings")
        warning_layout = QVBoxLayout(warning_box)
        self.warning_label = QLabel("STATUS: All Clear")
        self.warning_label.setAlignment(Qt.AlignCenter)
        self.warning_label.setStyleSheet(WARNING_NORMAL_STYLE)
        warning_layout.addWidget(self.warning_label)
        parent_layout.addWidget(warning_box)
        
        parent_layout.addStretch()

    def _toggle_play_pause(self):
        if self.is_playing:
            self.pause_requested.emit()
        else:
            self.play_requested.emit()

    def set_playing_state(self, playing):
        self.is_playing = playing
        if self.is_playing:
            self.play_pause_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.play_pause_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def update_frame_position(self, frame_num, total_frames, elapsed_time_secs):
        self.seek_slider.setValue(frame_num)
        total_time_secs = (total_frames / (config.CAMERA_FPS or 30))
        
        elapsed_str = time.strftime('%M:%S', time.gmtime(elapsed_time_secs))
        total_str = time.strftime('%M:%S', time.gmtime(total_time_secs))
        
        self.time_label.setText(f"{elapsed_str} / {total_str}")
        self.frame_count_label.setText(f"Frame: {frame_num} / {total_frames}")

    def set_total_frames(self, total_frames):
        self.seek_slider.setRange(0, total_frames)

    def display_frame(self, frame: np.ndarray):
        """Displays a single video frame."""
        if frame is None:
            return
        
        image = QImage(frame.data, frame.shape[1], frame.shape[0], QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(image)
        self.video_label.setPixmap(pixmap.scaled(self.video_label.size(), 
                                                  Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def update_performance_metrics(self, stats: dict):
        """Update performance metrics from a dictionary for consistency."""
        self.fps_label.setText(f"Processing FPS: {stats.get('fps', 0):.2f}")
        self.latency_label.setText(f"Frame Latency: {stats.get('latency_ms', 0):.2f} ms")
        self.inference_time_label.setText(f"Inference Time: {stats.get('inference_time_ms', 0):.2f} ms")

    def update_detection_info(self, analysis_data: dict):
        self.detection_info_text.clear()
        tracked_objects = analysis_data.get('tracked_objects', [])
        for obj in tracked_objects:
            ttc = obj.get('ttc', float('inf'))
            ttc_text = f"{ttc:.1f}s" if ttc != float('inf') else "N/A"
            info = (f"ID: {obj.get('track_id', 'N/A')} | "
                    f"Class: {obj.get('class_name', 'N/A')} | "
                    f"Dist: {obj.get('distance', 0):.1f}m | "
                    f"TTC: {ttc_text}")
            self.detection_info_text.append(info)

    def update_warning_status(self, warning_text, risk_level):
        self.warning_label.setText(warning_text or "All Clear")
        if risk_level in ['Critical', 'High']:
            self.warning_label.setStyleSheet(WARNING_CRITICAL_STYLE)
        else:
            self.warning_label.setStyleSheet(WARNING_NORMAL_STYLE)
    
    def run(self):
        self.show()
        app = get_qt_app()
        app.exec_()

    def closeEvent(self, event):
        print("Offline UI closing, requesting processor stop.")
        self.stop_requested.emit()
        event.accept()

def get_qt_app():
    """Returns the singleton QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app
