"""
Enhanced Weather Impact Analyzer for FCW System
Integrates with AI agent, location services, and middleware for comprehensive weather analysis
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass

from modules.feature_extractors.weather_detector import WeatherCondition
from modules.weather_detection import (
    get_location_service, LocationData,
    get_weather_client, WeatherData,
    get_weather_agent, WeatherRiskAnalysis,
    get_weather_middleware
)
import config

class WeatherImpact(Enum):
    NORMAL = "Normal Conditions"
    REDUCED_VISIBILITY = "Reduced Visibility"
    SLIPPERY_ROAD = "Slippery Road"
    SEVERE_CONDITIONS = "Severe Weather Conditions"
    CRITICAL_CONDITIONS = "Critical Weather Conditions"

@dataclass
class EnhancedWeatherAnalysis:
    """Enhanced weather analysis result"""
    impact: WeatherImpact
    risk_multiplier: float
    visibility_factor: float
    road_condition_factor: float
    driver_advice: str
    ai_analysis: Optional[WeatherRiskAnalysis]
    weather_data: Optional[WeatherData]
    location_data: Optional[LocationData]
    timestamp: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'impact': self.impact.value,
            'risk_multiplier': self.risk_multiplier,
            'visibility_factor': self.visibility_factor,
            'road_condition_factor': self.road_condition_factor,
            'driver_advice': self.driver_advice,
            'ai_analysis': self.ai_analysis.to_dict() if self.ai_analysis else None,
            'weather_data': self.weather_data.to_dict() if self.weather_data else None,
            'location_data': self.location_data.to_dict() if self.location_data else None,
            'timestamp': self.timestamp
        }

class WeatherImpactAnalyzer(ABC):
    @abstractmethod
    async def analyze_weather(self, weather: WeatherCondition) -> WeatherImpact:
        """
        Analyzes the impact of weather conditions on driving.
        """
        pass

class EnhancedWeatherImpactAnalyzer(WeatherImpactAnalyzer):
    """
    Enhanced weather impact analyzer with AI integration
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize services
        self.location_service = get_location_service()
        self.weather_client = get_weather_client()
        self.weather_agent = get_weather_agent()
        self.middleware = get_weather_middleware()
        
        # Cache and state management
        self.last_analysis: Optional[EnhancedWeatherAnalysis] = None
        self.last_update_time = 0
        self.analysis_cache = {}
        
        # Initialize middleware subscriptions
        self._setup_middleware_subscriptions()
        
        # Background task for periodic updates
        self.update_task = None
        self.running = False
        
    def _setup_middleware_subscriptions(self):
        """Setup middleware subscriptions for real-time updates"""
        try:
            # Subscribe to weather data updates
            self.middleware.subscribe_weather_data(
                "weather_analyzer",
                self._on_weather_data_update
            )
            
            self.logger.info("Weather impact analyzer subscribed to middleware")
        except Exception as e:
            self.logger.error(f"Failed to setup middleware subscriptions: {e}")
    
    def _on_weather_data_update(self, weather_data: WeatherData):
        """Handle weather data updates from middleware"""
        try:
            self.logger.debug(f"Received weather update: {weather_data.condition}")
            # Trigger analysis update if needed
            if self._should_update_analysis(weather_data):
                asyncio.create_task(self._update_analysis_async(weather_data))
        except Exception as e:
            self.logger.error(f"Error handling weather data update: {e}")
    
    def _should_update_analysis(self, weather_data: Optional[WeatherData] = None) -> bool:
        """Check if analysis should be updated"""
        current_time = time.time()
        
        # Update if no previous analysis
        if not self.last_analysis:
            return True
        
        # Update if weather conditions changed significantly
        if weather_data and self.last_analysis.weather_data and \
           self.last_analysis.weather_data.condition != weather_data.condition:
            return True
        
        # Update based on time interval
        if (current_time - self.last_update_time) > config.WEATHER_UPDATE_INTERVAL:
            return True
        
        return False
    
    async def _update_analysis_async(self, weather_data: WeatherData):
        """Update analysis asynchronously"""
        try:
            location_data = await self.location_service.get_current_location()
            analysis = await self._perform_enhanced_analysis(weather_data, location_data)
            
            if analysis:
                self.last_analysis = analysis
                self.last_update_time = time.time()
                
                # Publish to middleware
                if analysis.ai_analysis:
                    self.middleware.publish_risk_analysis(analysis.ai_analysis)
                
                self.logger.info(f"Weather analysis updated: {analysis.impact.value}")
            else:
                self.logger.warning("Failed to update weather analysis.")
                
        except Exception as e:
            self.logger.error(f"Error updating analysis: {e}")
    
    async def analyze_weather(self, weather: WeatherCondition) -> WeatherImpact:
        """
        Basic weather analysis for compatibility
        """
        try:
            # Get enhanced analysis
            enhanced_analysis = await self.get_enhanced_analysis()
            
            if enhanced_analysis:
                return enhanced_analysis.impact
            else:
                # Fallback to simple analysis
                return self._simple_weather_analysis(weather)
                
        except Exception as e:
            self.logger.error(f"Error in weather analysis: {e}")
            return self._simple_weather_analysis(weather)
    
    async def get_enhanced_analysis(self) -> Optional[EnhancedWeatherAnalysis]:
        """
        Get comprehensive weather analysis with AI integration
        """
        # This check is now crucial to avoid repeated work
        if not self._should_update_analysis():
            return self.last_analysis

        try:
            # Get current location
            location_data = await self.location_service.get_current_location()
            if not location_data:
                self.logger.warning("No location data available")
                return None
            
            # Get weather data
            location_string = self.location_service.get_location_string()
            weather_data = await self.weather_client.get_weather_data(location_string)
            
            if not weather_data:
                self.logger.warning("No weather data available")
                return None
            
            # Publish weather data to middleware
            self.middleware.publish_weather_data(weather_data)
            
            # Perform enhanced analysis
            analysis = await self._perform_enhanced_analysis(weather_data, location_data)
            
            if analysis:
                self.last_analysis = analysis
                self.last_update_time = time.time()
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error getting enhanced analysis: {e}")
            return None
    
    async def _perform_enhanced_analysis(
        self, 
        weather_data: WeatherData, 
        location_data: Optional[LocationData]
    ) -> Optional[EnhancedWeatherAnalysis]:
        """Perform comprehensive weather analysis"""
        try:
            # Get AI analysis
            ai_analysis = await self.weather_agent.analyze_weather_conditions(
                weather_data, location_data
            )
            
            # --- 🚀 DIAGNOSTIC LOGGING START ---
            self.logger.debug("--- WEATHER DATA DEBUG ---")
            self.logger.debug(f"RAW API DATA: {weather_data}")
            self.logger.debug(f"AI ANALYSIS: {ai_analysis}")
            self.logger.debug("--------------------------")
            # --- 🚀 DIAGNOSTIC LOGGING END ---

            if not ai_analysis:
                self.logger.warning("AI analysis not available, using fallback")
                ai_analysis = self._get_fallback_ai_analysis(weather_data)
            
            # Calculate impact factors
            impact = self._determine_weather_impact(ai_analysis)
            risk_multiplier = ai_analysis.risk_multiplier
            visibility_factor = self._calculate_visibility_factor(weather_data, ai_analysis)
            road_condition_factor = self._calculate_road_condition_factor(weather_data, ai_analysis)
            
            return EnhancedWeatherAnalysis(
                impact=impact,
                risk_multiplier=risk_multiplier,
                visibility_factor=visibility_factor,
                road_condition_factor=road_condition_factor,
                driver_advice=ai_analysis.driver_advice,
                ai_analysis=ai_analysis,
                weather_data=weather_data,
                location_data=location_data,
                timestamp=int(time.time())
            )
            
        except Exception as e:
            self.logger.error(f"Error during weather analysis: {e}")
            return None
    
    def _analyze_weather_impact(self, weather_data: WeatherData) -> Optional[WeatherRiskAnalysis]:
        """Perform the actual weather analysis using the AI agent."""
        if not self.weather_agent:
            self.logger.error("Weather agent not available.")
            return None

        # Schedule the coroutine on the main event loop
        future = asyncio.run_coroutine_threadsafe(
            self.weather_agent.analyze_weather_conditions(weather_data),
            self.loop
        )

        try:
            # Wait for the result with a timeout
            ai_analysis = future.result(timeout=5.0)

            if ai_analysis:
                self.logger.debug("--- WEATHER DATA DEBUG ---")
                self.logger.debug(f"RAW API DATA: {weather_data}")
                self.logger.debug(f"AI ANALYSIS: {ai_analysis}")
                self.logger.debug("--------------------------")
                return ai_analysis
            else:
                self.logger.warning("Weather AI analysis returned no result.")
                return None
        except asyncio.TimeoutError:
            self.logger.error("Weather AI analysis timed out.")
            return None
        except Exception as e:
            self.logger.error(f"An error occurred during weather analysis: {e}")
            return None
    
    def _determine_weather_impact(self, ai_analysis: WeatherRiskAnalysis) -> WeatherImpact:
        """Determine weather impact level from AI analysis"""
        risk_level = ai_analysis.road_risk.lower()
        
        if risk_level == 'critical':
            return WeatherImpact.CRITICAL_CONDITIONS
        elif risk_level == 'high':
            return WeatherImpact.SEVERE_CONDITIONS
        elif risk_level == 'medium':
            if 'visibility' in ai_analysis.driver_advice.lower():
                return WeatherImpact.REDUCED_VISIBILITY
            else:
                return WeatherImpact.SLIPPERY_ROAD
        else:
            return WeatherImpact.NORMAL
    
    def _calculate_visibility_factor(
        self, 
        weather_data: WeatherData, 
        ai_analysis: WeatherRiskAnalysis
    ) -> float:
        """Calculate visibility impact factor"""
        base_visibility = weather_data.visibility
        
        # Normalize visibility (10km = 1.0, 0km = 0.0)
        visibility_factor = min(base_visibility / 10.0, 1.0)
        
        # Apply AI analysis adjustments
        visibility_level = ai_analysis.visibility_level.lower()
        if visibility_level == 'very_poor':
            visibility_factor *= 0.2
        elif visibility_level == 'poor':
            visibility_factor *= 0.4
        elif visibility_level == 'moderate':
            visibility_factor *= 0.7
        elif visibility_level == 'good':
            visibility_factor *= 0.9
        # excellent = no change
        
        return max(0.1, visibility_factor)  # Minimum 0.1
    
    def _calculate_road_condition_factor(
        self, 
        weather_data: WeatherData, 
        ai_analysis: WeatherRiskAnalysis
    ) -> float:
        """Calculate road condition impact factor"""
        condition = weather_data.condition.lower()
        
        # Base road condition factor
        if condition in ['ice', 'snow', 'sleet']:
            road_factor = 0.3
        elif condition in ['rain', 'drizzle', 'thunderstorm']:
            road_factor = 0.6
        elif condition in ['fog', 'mist']:
            road_factor = 0.8
        else:
            road_factor = 1.0
        
        # Apply AI risk multiplier
        road_factor *= (2.0 - ai_analysis.risk_multiplier) / 2.0
        
        return max(0.2, road_factor)  # Minimum 0.2
    
    def _get_fallback_ai_analysis(self, weather_data: WeatherData) -> WeatherRiskAnalysis:
        """Get fallback AI analysis when agent is not available"""
        from utils.weather_ai_agent import WeatherRiskAnalysis
        
        condition = weather_data.condition.lower()
        
        if condition in ['rain', 'drizzle']:
            return WeatherRiskAnalysis(
                condition=condition,
                visibility_level='moderate',
                road_risk='medium',
                driver_advice='Reduce speed, increase following distance',
                risk_multiplier=1.5,
                timestamp=int(time.time())
            )
        elif condition in ['snow', 'ice']:
            return WeatherRiskAnalysis(
                condition=condition,
                visibility_level='poor',
                road_risk='high',
                driver_advice='Drive very carefully',
                risk_multiplier=2.5,
                timestamp=int(time.time())
            )
        else:
            return WeatherRiskAnalysis(
                condition=condition,
                visibility_level='good',
                road_risk='low',
                driver_advice='Normal driving conditions',
                risk_multiplier=1.0,
                timestamp=int(time.time())
            )
    
    def _simple_weather_analysis(self, weather: WeatherCondition) -> WeatherImpact:
        """Simple fallback weather analysis"""
        if weather == WeatherCondition.RAINY:
            return WeatherImpact.SLIPPERY_ROAD
        elif weather == WeatherCondition.FOGGY:
            return WeatherImpact.REDUCED_VISIBILITY
        else:
            return WeatherImpact.NORMAL
    
    async def initialize(self):
        """Initializes the analyzer and starts the background update task."""
        self.running = True
        self.update_task = asyncio.create_task(self._background_update_loop())
        self.logger.info("Weather Impact Analyzer initialized with background updates.")
        return True
    
    async def _background_update_loop(self):
        """Periodically updates weather analysis in the background."""
        while self.running:
            try:
                self.logger.debug("Performing background weather analysis update...")
                await self.get_enhanced_analysis()
            except Exception as e:
                self.logger.error(f"Error in background weather update loop: {e}")
            
            await asyncio.sleep(config.WEATHER_UPDATE_INTERVAL)
    
    async def shutdown(self):
        """Stops the background update task."""
        self.running = False
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                self.logger.info("Weather background task cancelled.")
        self.logger.info("Weather Impact Analyzer shut down.")
    
    def get_current_analysis(self) -> Optional[EnhancedWeatherAnalysis]:
        """Returns the latest analysis without blocking."""
        return self.last_analysis
    
    def get_analyzer_stats(self) -> Dict[str, Any]:
        """Get analyzer statistics"""
        return {
            'last_update_time': self.last_update_time,
            'has_current_analysis': self.last_analysis is not None,
            'running': self.running,
            'location_service_stats': self.location_service.__dict__ if hasattr(self.location_service, '__dict__') else {},
            'weather_client_stats': self.weather_client.get_cache_stats(),
            'weather_agent_stats': self.weather_agent.get_agent_stats()
        }

# Global analyzer instance
_analyzer_instance = None
