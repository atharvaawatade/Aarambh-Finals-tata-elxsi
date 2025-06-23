"""
gRPC Middleware for FCW System
Handles low-latency data sharing for weather and location information
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, Callable
from concurrent import futures
import threading
from dataclasses import asdict

from .weather_api_client import WeatherData
from .location_service import LocationData
from .weather_ai_agent import WeatherRiskAnalysis
import config

class WeatherMiddleware:
    """
    Middleware for weather data sharing with low latency
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Data storage for sharing
        self.current_weather: Optional[WeatherData] = None
        self.current_location: Optional[LocationData] = None
        self.current_risk: Optional[WeatherRiskAnalysis] = None
        
        # Subscribers for data updates
        self.weather_subscribers: Dict[str, Callable] = {}
        self.location_subscribers: Dict[str, Callable] = {}
        self.risk_subscribers: Dict[str, Callable] = {}
        
        # Performance metrics
        self.message_count = 0
        self.last_update_time = 0
        self.latency_stats = []
        
    def publish_weather_data(self, weather_data: WeatherData):
        """Publish weather data to subscribers"""
        try:
            start_time = time.time()
            
            self.current_weather = weather_data
            self.last_update_time = time.time()
            self.message_count += 1
            
            # Notify all subscribers
            for subscriber_id, callback in self.weather_subscribers.items():
                try:
                    callback(weather_data)
                except Exception as e:
                    self.logger.error(f"Error notifying weather subscriber {subscriber_id}: {e}")
            
            # Track latency
            latency = (time.time() - start_time) * 1000  # Convert to ms
            self.latency_stats.append(latency)
            
            # Keep only last 100 latency measurements
            if len(self.latency_stats) > 100:
                self.latency_stats = self.latency_stats[-100:]
            
            self.logger.debug(f"Weather data published with {latency:.2f}ms latency")
            
        except Exception as e:
            self.logger.error(f"Error publishing weather data: {e}")
    
    def publish_risk_analysis(self, risk_analysis: 'WeatherRiskAnalysis'):
        """Publish risk analysis to subscribers"""
        try:
            start_time = time.time()
            
            self.current_risk = risk_analysis
            self.last_update_time = time.time()
            self.message_count += 1
            
            # Notify all subscribers
            for subscriber_id, callback in self.risk_subscribers.items():
                try:
                    callback(risk_analysis)
                except Exception as e:
                    self.logger.error(f"Error notifying risk subscriber {subscriber_id}: {e}")
            
            # Track latency
            latency = (time.time() - start_time) * 1000  # Convert to ms
            self.latency_stats.append(latency)
            
            # Keep only last 100 latency measurements
            if len(self.latency_stats) > 100:
                self.latency_stats = self.latency_stats[-100:]
            
            self.logger.debug(f"Risk analysis published with {latency:.2f}ms latency")
            
        except Exception as e:
            self.logger.error(f"Error publishing risk analysis: {e}")
    
    def subscribe_weather_data(self, subscriber_id: str, callback: Callable[[WeatherData], None]):
        """Subscribe to weather data updates"""
        self.weather_subscribers[subscriber_id] = callback
        self.logger.info(f"Weather subscriber added: {subscriber_id}")
        
        # Send current data if available
        if self.current_weather:
            try:
                callback(self.current_weather)
            except Exception as e:
                self.logger.error(f"Error sending current weather to {subscriber_id}: {e}")

# Global middleware instance
_weather_middleware = None

def get_weather_middleware():
    """Get global weather middleware instance"""
    global _weather_middleware
    if _weather_middleware is None:
        _weather_middleware = WeatherMiddleware()
    return _weather_middleware 