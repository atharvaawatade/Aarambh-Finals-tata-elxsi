"""
GPS Service for FCW System
Connects to a TCP stream of NMEA sentences from a GPS provider app (e.g., NetGPS)
and calculates the vehicle's speed.
"""

import socket
import json
import math
import logging
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal
import config
import time

# Configure logging for this module
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the distance between two points on Earth using the Haversine formula."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class GPSService(QThread):
    """
    A QThread that connects to a GPS data stream, processes JSON data,
    and emits the current speed and status.
    """
    speed_updated = pyqtSignal(float)
    status_updated = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.sock = None

    def stop(self):
        """Stops the GPS service thread."""
        self.running = False
        if self.sock:
            try:
                # This helps break the sock.recv() blocking call
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass  # Ignore errors on shutdown, as the socket might already be closed
            finally:
                self.sock.close()
                self.sock = None

        self.logger.info("GPS service stopped.")
        self.quit()

    def run(self):
        """Main loop for the GPS service thread."""
        self.logger.info("GPS thread started.")
        if not config.GPS_ENABLED:
            self.logger.info("GPS service is disabled in the config.")
            return

        self.running = True
        
        while self.running:
            try:
                self.logger.info(f"Connecting to GPS stream at {config.GPS_SERVER_IP}:{config.GPS_SERVER_PORT}…")
                self.status_updated.emit("Connecting...")
                
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.sock:
                    self.sock.settimeout(10.0)
                    self.sock.connect((config.GPS_SERVER_IP, config.GPS_SERVER_PORT))
                    self.logger.info("Successfully connected to GPS stream.")
                    self.status_updated.emit("Connected")
                    
                    buffer = ""
                    
                    while self.running:
                        raw_data = self.sock.recv(1024)
                        if not raw_data:
                            self.logger.warning("GPS stream connection closed by server. Reconnecting...")
                            break

                        buffer += raw_data.decode('utf-8', errors='ignore')
                        self.logger.debug(f"GPS Raw Data Chunk Received: '{buffer.strip()}'")

                        # The server sends JSON objects that are not newline-separated.
                        # We need to find valid JSON objects in the stream.
                        try:
                            # This is a simple way to handle the stream; it assumes one object per chunk for now.
                            # A more robust solution would find the start and end braces {}.
                            # Also, the log shows "8080" appearing in the stream, which corrupts the JSON.
                            # We'll clean that up.
                            clean_buffer = buffer.replace("8080", "").strip()
                            if clean_buffer:
                                data = json.loads(clean_buffer)
                                speed_ms = data.get('speed', 0.0)
                                
                                # Convert speed from m/s to km/h
                                speed_kmh = speed_ms * 3.6
                                
                                self.speed_updated.emit(speed_kmh)
                                self.logger.info(f"Speed updated: {speed_kmh:.2f} km/h")
                            
                            buffer = "" # Clear buffer after processing

                        except json.JSONDecodeError:
                            self.logger.warning(f"Incomplete or invalid JSON in buffer. Waiting for more data.")
                            # Don't clear the buffer, wait for the rest of the object
                            continue

            except socket.timeout:
                self.logger.warning("Connection to GPS server timed out. Retrying in 10s...")
                self.status_updated.emit("Timeout")
                time.sleep(10)
            except (socket.error, ConnectionRefusedError) as e:
                self.logger.error(f"GPS socket error: {e}. Retrying in 10s...")
                self.status_updated.emit("Error")
                time.sleep(10)
            except Exception as e:
                self.logger.error(f"An unexpected error occurred in GPS service: {e}", exc_info=True)
                self.status_updated.emit("Crashed")
                time.sleep(10) 