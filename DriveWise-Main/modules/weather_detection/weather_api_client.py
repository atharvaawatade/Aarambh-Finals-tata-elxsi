"""
Weather API Client for FCW System
Handles real-time weather data retrieval from weatherapi.com
"""

import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import requests
import config
import asyncio

# The API key is hardcoded as requested.
API_KEY = '936ed81319b24158813100408252206'
BASE_URL = 'http://api.weatherapi.com/v1/current.json'

@dataclass
class WeatherData:
    """Represents weather data from weatherapi.com"""
    location: str
    condition: str
    temperature: float
    humidity: int
    wind_speed: float  # kph
    visibility: float  # km
    is_raining: bool
    air_quality_pm2_5: float
    air_quality_pm10: float
    timestamp: int
    source: str = "weatherapi.com"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converts the dataclass to a dictionary."""
        return {
            'location': self.location,
            'condition': self.condition,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'wind_speed': self.wind_speed,
            'visibility': self.visibility,
            'is_raining': self.is_raining,
            'air_quality_pm2_5': self.air_quality_pm2_5,
            'air_quality_pm10': self.air_quality_pm10,
            'timestamp': self.timestamp,
            'source': self.source
        }

class WeatherApiClient:
    """Client to fetch weather data from weatherapi.com."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def get_weather_data(self, city_name: str) -> Optional[WeatherData]:
        """
        Fetches weather data for a given city name.
        This method is async to fit into the existing architecture.
        """
        params = {
            'key': API_KEY,
            'q': city_name,
            'aqi': 'yes'
        }
        
        try:
            # Using asyncio.to_thread to run the blocking requests call in a non-blocking way
            response = await asyncio.to_thread(requests.get, BASE_URL, params=params, timeout=5)
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
            data = response.json()
            
            self.logger.info(f"Successfully fetched weather data for {data['location']['name']}")
            
            return WeatherData(
                location=data['location']['name'],
                temperature=data['current']['temp_c'],
                condition=data['current']['condition']['text'],
                humidity=data['current']['humidity'],
                visibility=data['current']['vis_km'],
                wind_speed=data['current']['wind_kph'],
                is_raining='rain' in data['current']['condition']['text'].lower(),
                air_quality_pm2_5=data['current']['air_quality'].get('pm2_5', 0.0),
                air_quality_pm10=data['current']['air_quality'].get('pm10', 0.0),
                timestamp=int(time.time())
            )
            
        except requests.exceptions.Timeout:
            self.logger.error(f"Request to WeatherAPI timed out for city: {city_name}")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP Request failed for city {city_name}: {e}")
            return None
        except KeyError:
            self.logger.error("Unexpected response format from WeatherAPI.")
            return None
        except Exception as e:
            self.logger.error(f"An unexpected error occurred in get_weather_data: {e}")
            return None

# Singleton instance
_weather_client_instance = None

def get_weather_client() -> WeatherApiClient:
    """Get the global weather API client instance."""
    global _weather_client_instance
    if _weather_client_instance is None:
        _weather_client_instance = WeatherApiClient()
    return _weather_client_instance 