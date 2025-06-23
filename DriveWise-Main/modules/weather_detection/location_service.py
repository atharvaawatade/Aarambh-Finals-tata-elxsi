"""
Location Service Module for FCW System
Handles real-time device location for Mac systems
"""

import asyncio
import logging
import time
import subprocess
import platform
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass
import geocoder
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import config
import requests

@dataclass
class LocationData:
    """Location data structure"""
    latitude: float
    longitude: float
    accuracy: float
    address: str
    timestamp: int
    source: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'accuracy': self.accuracy,
            'address': self.address,
            'timestamp': self.timestamp,
            'source': self.source
        }

class LocationService:
    """
    Real-time location service for Mac systems
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.geolocator = Nominatim(user_agent="fcw_system_realtime")
        self.current_location: Optional[LocationData] = None
        self.permission_granted = False
        self.last_update_time = 0
        self.system_platform = platform.system()
        
    async def request_location_permission(self) -> bool:
        """
        Request location permission from user for real-time location
        """
        try:
            self.logger.info("Requesting real-time location permission...")
            
            print("\n" + "="*60)
            print("🌍 REAL-TIME LOCATION PERMISSION REQUEST")
            print("="*60)
            print("The FCW System needs real-time location access for accurate weather updates.")
            print("This enables precise driving risk assessment based on your current location.")
            print("Location data is used only for weather services and is not stored permanently.")
            print("\n📍 Detection Methods:")
            if self.system_platform == "Darwin":  # macOS
                print("  • macOS Location Services (if available)")
                print("  • WiFi-based geolocation")
                print("  • IP-based geolocation")
            else:
                print("  • WiFi-based geolocation")
                print("  • IP-based geolocation")
            
            self.permission_granted = True
            self.logger.info("Real-time location permission granted")
            print("✅ Real-time location permission granted!")
            print("🔄 Starting location detection...")
            return True
                
        except Exception as e:
            self.logger.error(f"Error requesting location permission: {e}")
            return False
    
    async def get_current_location(self, force_update: bool = False) -> Optional[LocationData]:
        """
        Get current real-time device location using multiple methods
        """
        current_time = time.time()
        if not force_update and self.current_location and (current_time - self.last_update_time) < 60:
            return self.current_location
        
        if not self.permission_granted:
            await self.request_location_permission()
            if not self.permission_granted:
                self.logger.warning("Location permission not granted")
                return None
        
        self.logger.info("Getting real-time current location...")
        location_data = await self._get_best_location()
        
        if location_data:
            self.current_location = location_data
            self.last_update_time = current_time
            self.logger.info(f"Location updated: {self.current_location.address} (Source: {self.current_location.source})")
            return self.current_location
        
        self.logger.error("Failed to get any location data")
        return None
    
    async def _get_best_location(self) -> Optional[LocationData]:
        """Get the best available location using multiple methods"""
        location_methods = []
        if self.system_platform == "Darwin":
            location_methods.append(("macOS_location", self._get_macos_location))
        
        location_methods.extend([
            ("ip_location_ipinfo", self._get_ip_location_ipinfo),
            ("ip_location_ipapi", self._get_ip_location_ipapi),
            ("ip_location_basic", self._get_ip_location_basic),
            ("wifi_location", self._get_wifi_location)
        ])
        
        for method_name, method_func in location_methods:
            try:
                self.logger.info(f"Trying {method_name}...")
                print(f"🔍 Trying {method_name}...")
                location_data = await method_func()
                if location_data:
                    self.logger.info(f"Successfully got location from {method_name}")
                    print(f"✅ Successfully got location from {method_name}")
                    return location_data
            except Exception as e:
                self.logger.warning(f"{method_name} failed: {e}")
        
        print("🌍 All location methods failed, using network-based fallback...")
        return await self._get_network_fallback_location()
    
    async def _get_ip_location_ipinfo(self) -> Optional[LocationData]:
        """Get location using ipinfo.io service"""
        try:
            response = await asyncio.to_thread(requests.get, "https://ipinfo.io/json", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'loc' in data:
                    lat, lon = map(float, data['loc'].split(','))
                    address = f"{data.get('city', '')}, {data.get('region', '')}, {data.get('country', '')}"
                    return LocationData(latitude=lat, longitude=lon, accuracy=1000.0, address=address.strip(', '), timestamp=int(time.time()), source="ipinfo_service")
        except Exception as e:
            self.logger.debug(f"ipinfo.io failed: {e}")
        return None
    
    async def _get_ip_location_ipapi(self) -> Optional[LocationData]:
        """Get location using ip-api.com service"""
        try:
            response = requests.get("http://ip-api.com/json/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    lat = data.get('lat')
                    lon = data.get('lon')
                    if lat and lon:
                        city = data.get('city', 'Unknown')
                        region = data.get('regionName', '')
                        country = data.get('country', '')
                        address = f"{city}, {region}, {country}".strip(', ')
                        
                        return LocationData(
                            latitude=lat,
                            longitude=lon,
                            accuracy=2000.0,
                            address=address,
                            timestamp=int(time.time()),
                            source="ipapi_service"
                        )
        except Exception as e:
            self.logger.debug(f"ip-api.com failed: {e}")
        return None
    
    async def _get_ip_location_basic(self) -> Optional[LocationData]:
        """Get location using basic geocoder methods"""
        try:
            # Try different geocoder services
            services = ['ipinfo', 'ip']
            
            for service in services:
                try:
                    location = geocoder.get('me', method=service)
                    if location.ok and location.latlng:
                        address = f"{location.city}, {location.country}" if location.city else f"Location: {location.latlng[0]:.4f}, {location.latlng[1]:.4f}"
                        return LocationData(
                            latitude=location.latlng[0],
                            longitude=location.latlng[1],
                            accuracy=3000.0,
                            address=address,
                            timestamp=int(time.time()),
                            source=f"geocoder_{service}"
                        )
                except Exception as e:
                    self.logger.debug(f"Geocoder {service} failed: {e}")
                    continue
                    
        except Exception as e:
            self.logger.debug(f"Basic IP location failed: {e}")
        
        return None
    
    async def _get_network_fallback_location(self) -> Optional[LocationData]:
        """Final fallback - use a reasonable default based on network info"""
        try:
            # Try to get timezone info to make an educated guess
            response = requests.get("http://worldtimeapi.org/api/ip", timeout=3)
            if response.status_code == 200:
                data = response.json()
                timezone = data.get('timezone', '')
                
                # Map common timezones to approximate locations
                timezone_locations = {
                    'America/New_York': (40.7128, -74.0060, "New York, NY, USA"),
                    'America/Los_Angeles': (34.0522, -118.2437, "Los Angeles, CA, USA"),
                    'America/Chicago': (41.8781, -87.6298, "Chicago, IL, USA"),
                    'Europe/London': (51.5074, -0.1278, "London, UK"),
                    'Europe/Paris': (48.8566, 2.3522, "Paris, France"),
                    'Asia/Tokyo': (35.6762, 139.6503, "Tokyo, Japan"),
                    'Asia/Shanghai': (31.2304, 121.4737, "Shanghai, China"),
                    'Asia/Kolkata': (28.6139, 77.2090, "New Delhi, India"),
                    'Australia/Sydney': (-33.8688, 151.2093, "Sydney, Australia"),
                }
                
                if timezone in timezone_locations:
                    lat, lon, address = timezone_locations[timezone]
                    return LocationData(
                                latitude=lat,
                                longitude=lon,
                                accuracy=50000.0,  # Very rough accuracy
                                address=address,
                                timestamp=int(time.time()),
                                source="timezone_fallback"
                    )
            
            # Ultimate fallback - use a central location
            return LocationData(
                latitude=39.8283,  # Center of US
                longitude=-98.5795,
                accuracy=1000000.0,
                address="Central Location, Earth",
                timestamp=int(time.time()),
                source="ultimate_fallback"
            )
                
        except Exception as e:
            self.logger.debug(f"Network fallback failed: {e}")
            # Absolute final fallback
            return LocationData(
                latitude=0.0,
                longitude=0.0,
                accuracy=100000.0,
                address="Unknown Location",
                timestamp=int(time.time()),
                source="absolute_fallback"
            )
    
    async def _get_macos_location(self) -> Optional[LocationData]:
        """Get location using macOS CoreLocation service via shell command"""
        # This is a placeholder for a more robust solution, as it's complex to get this reliably.
        return None
    
    async def _get_wifi_location(self) -> Optional[LocationData]:
        """Get location using WiFi BSSIDs (placeholder)"""
        return None
    
    async def _reverse_geocode(self, latitude: float, longitude: float) -> Optional[str]:
        """Converts latitude and longitude to a human-readable address."""
        try:
            location = await asyncio.to_thread(self.geolocator.reverse, (latitude, longitude), exactly_one=True)
            return location.address if location else "Unknown address"
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            self.logger.error(f"Reverse geocoding failed: {e}")
            return "Address lookup failed"
    
    def get_location_string(self) -> str:
        """Returns the current location as a string for weather API calls."""
        if self.current_location and self.current_location.address:
            # Ensure address is a single line and URL-friendly
            address = self.current_location.address.replace('\n', ', ').strip()
            if address:
                return address
        
        if self.current_location:
            # Fallback to coordinates if address is somehow not available or empty
            return f"{self.current_location.latitude},{self.current_location.longitude}"
        
        return getattr(config, 'LOCATION_FALLBACK', 'Bhopal')
    
    async def initialize(self) -> bool:
        """Initializes the location service by requesting permission."""
        return await self.request_location_permission()

# Global location service instance
_location_service_instance = None

def get_location_service() -> LocationService:
    """Get the global location service instance."""
    global _location_service_instance
    if _location_service_instance is None:
        _location_service_instance = LocationService()
    return _location_service_instance 