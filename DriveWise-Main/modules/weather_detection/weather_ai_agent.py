"""
Weather AI Agent for FCW System
Uses Gemini AI to analyze weather conditions and provide driving risk assessments
"""

import asyncio
import logging
import time
import re
from typing import Optional, Dict, Any
from dataclasses import dataclass
from cachetools import TTLCache
from modules.gemini import get_gemini_model, GEMINI_AVAILABLE
from modules.weather_detection.weather_api_client import WeatherData
from modules.weather_detection.location_service import LocationData
import config

@dataclass
class WeatherRiskAnalysis:
    """Weather risk analysis result"""
    condition: str
    visibility_level: str
    road_risk: str
    driver_advice: str
    risk_multiplier: float
    timestamp: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'condition': self.condition,
            'visibility_level': self.visibility_level,
            'road_risk': self.road_risk,
            'driver_advice': self.driver_advice,
            'risk_multiplier': self.risk_multiplier,
            'timestamp': self.timestamp
        }

class WeatherAIAgent:
    """
    AI Agent for weather analysis using Gemini
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize Gemini AI
        self.model = None
        if GEMINI_AVAILABLE:
            try:
                self.model = get_gemini_model()
                if self.model:
                    self.logger.info("WeatherAIAgent is ready to use Gemini model.")
                else:
                    self.logger.warning("WeatherAIAgent could not get Gemini model.")
            except Exception as e:
                self.logger.error(f"Error getting Gemini model for weather agent: {e}")
        else:
            self.logger.warning("Gemini not available for WeatherAIAgent.")
        
        # Setup caching for AI responses
        if config.AGENT_CACHE_ENABLED:
            self.response_cache = TTLCache(
                maxsize=config.AGENT_CACHE_SIZE,
                ttl=config.WEATHER_CACHE_DURATION
            )
        else:
            self.response_cache = None
        
        # Error tracking
        self.consecutive_errors = 0
        self.last_analysis_time = 0
    
    async def analyze_weather_conditions(
        self, 
        weather_data: WeatherData, 
        location_data: Optional[LocationData] = None
    ) -> Optional[WeatherRiskAnalysis]:
        """
        Analyze weather conditions using AI and provide risk assessment
        """
        try:
            if not self.model:
                self.logger.error("Gemini model not available")
                return self._get_fallback_analysis(weather_data)
            
            # Check cache first
            cache_key = self._get_cache_key(weather_data, location_data)
            if self.response_cache and cache_key in self.response_cache:
                self.logger.debug("Weather analysis retrieved from cache")
                return self.response_cache[cache_key]
            
            # Prepare prompt for AI analysis
            prompt = self._create_analysis_prompt(weather_data, location_data)
            
            # Get AI analysis
            analysis = await self._get_ai_analysis(prompt)
            
            if analysis:
                # Cache the result
                if self.response_cache:
                    self.response_cache[cache_key] = analysis
                
                self.consecutive_errors = 0
                self.last_analysis_time = time.time()
                self.logger.info(f"Weather analysis completed: {analysis.road_risk} risk")
                return analysis
            else:
                return self._get_fallback_analysis(weather_data)
                
        except Exception as e:
            self.logger.error(f"Error in weather analysis: {e}")
            return self._get_fallback_analysis(weather_data)
    
    def _create_analysis_prompt(
        self, 
        weather_data: WeatherData, 
        location_data: Optional[LocationData]
    ) -> str:
        """Create analysis prompt for AI"""
        location_info = location_data.address if location_data else weather_data.location
        
        prompt = config.WEATHER_AGENT_PROMPT_TEMPLATE.format(
            weather_data=f"""
            Location: {weather_data.location}
            Condition: {weather_data.condition}
            Temperature: {weather_data.temperature}°C
            Humidity: {weather_data.humidity}%
            Wind Speed: {weather_data.wind_speed} km/h
            Visibility: {weather_data.visibility} km
            Is Raining: {"Yes" if weather_data.is_raining else "No"}
            Air Quality (PM2.5): {weather_data.air_quality_pm2_5:.2f}
            Air Quality (PM10): {weather_data.air_quality_pm10:.2f}
            """,
            location=location_info,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(weather_data.timestamp))
        )
        
        return prompt
    
    async def _get_ai_analysis(self, prompt: str) -> Optional[WeatherRiskAnalysis]:
        """Get analysis from AI model using an async call."""
        if not self.model:
            return None
        try:
            self.logger.debug("Requesting AI weather analysis...")
            response = await self.model.generate_content_async(prompt)
            if response and response.text:
                self.logger.debug(f"Full AI response received: {response.text[:100]}...")
                return self._parse_ai_response(response.text)
            else:
                self.logger.error("Empty response from AI model")
            return None
        except Exception as e:
            self.logger.error(f"AI analysis failed: {e}")
            return None
    
    def _parse_ai_response(self, response_text: str) -> Optional[WeatherRiskAnalysis]:
        """Parse AI response into structured data"""
        try:
            # Extract structured data using regex
            condition_match = re.search(r'CONDITION:\s*(\w+)', response_text, re.IGNORECASE)
            visibility_match = re.search(r'VISIBILITY:\s*(\w+)', response_text, re.IGNORECASE)
            risk_match = re.search(r'ROAD_RISK:\s*(\w+)', response_text, re.IGNORECASE)
            advice_match = re.search(r'DRIVER_ADVICE:\s*([^\n]+)', response_text, re.IGNORECASE)
            
            if not all([condition_match, visibility_match, risk_match, advice_match]):
                self.logger.error("Failed to parse AI response format")
                return None
            
            condition = condition_match.group(1).lower()
            visibility = visibility_match.group(1).lower()
            road_risk = risk_match.group(1).lower()
            advice = advice_match.group(1).strip()
            
            # Get risk multiplier based on condition
            risk_multiplier = config.WEATHER_RISK_MULTIPLIERS.get(condition, 1.0)
            
            return WeatherRiskAnalysis(
                condition=condition,
                visibility_level=visibility,
                road_risk=road_risk,
                driver_advice=advice,
                risk_multiplier=risk_multiplier,
                timestamp=int(time.time())
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing AI response: {e}")
            return None
    
    def _get_fallback_analysis(self, weather_data: WeatherData) -> WeatherRiskAnalysis:
        """Get fallback analysis when AI is not available"""
        condition = weather_data.condition.lower()
        
        # Simple rule-based fallback
        if condition in ['rain', 'rainy', 'drizzle']:
            visibility = 'moderate'
            risk = 'medium'
            advice = 'Reduce speed, increase following distance'
            multiplier = 1.5
        elif condition in ['snow', 'ice', 'sleet']:
            visibility = 'poor'
            risk = 'high'
            advice = 'Drive very carefully, consider staying home'
            multiplier = 2.5
        elif condition in ['fog', 'mist', 'haze']:
            visibility = 'poor'
            risk = 'high'
            advice = 'Use fog lights, drive slowly'
            multiplier = 2.0
        elif condition in ['storm', 'thunderstorm']:
            visibility = 'very_poor'
            risk = 'critical'
            advice = 'Avoid driving if possible'
            multiplier = 3.0
        else:
            visibility = 'good'
            risk = 'low'
            advice = 'Normal driving conditions'
            multiplier = 1.0
        
        self.logger.info(f"Using fallback weather analysis: {risk} risk")
        
        return WeatherRiskAnalysis(
            condition=condition,
            visibility_level=visibility,
            road_risk=risk,
            driver_advice=advice,
            risk_multiplier=multiplier,
            timestamp=int(time.time())
        )
    
    def _get_cache_key(
        self, 
        weather_data: WeatherData, 
        location_data: Optional[LocationData]
    ) -> str:
        """Generate cache key for weather analysis"""
        location_key = location_data.address if location_data else weather_data.location
        return f"weather_{weather_data.location}_{weather_data.condition}"
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            'model': self.model,
            'model_available': self.model is not None,
            'cache_size': len(self.response_cache) if self.response_cache else 0,
            'cache_max_size': config.AGENT_CACHE_SIZE if config.AGENT_CACHE_ENABLED else 0,
            'consecutive_errors': self.consecutive_errors,
            'last_analysis_time': self.last_analysis_time
        }
    
    def clear_cache(self):
        """Clear analysis cache"""
        if self.response_cache:
            self.response_cache.clear()
            self.logger.info("Weather AI agent cache cleared")

# Global weather AI agent instance
_weather_agent = None

def get_weather_agent() -> WeatherAIAgent:
    """Get global weather agent instance"""
    global _weather_agent
    if _weather_agent is None:
        _weather_agent = WeatherAIAgent()
    return _weather_agent 