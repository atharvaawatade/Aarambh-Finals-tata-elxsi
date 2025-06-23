"""
Warning Generator - PERFORMANCE OPTIMIZED
Fast warning generation with LLM integration
"""
import time
import config
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import asyncio
from modules.gemini import get_gemini_model, GEMINI_AVAILABLE

# Try to import Gemini, but don't fail if not available
# try:
#     import google.generativeai as genai
#     GEMINI_AVAILABLE = True
# except ImportError:
#     GEMINI_AVAILABLE = False
#     print("⚠️  Gemini not available - using fallback warnings")

class WarningGenerator(ABC):
    @abstractmethod
    def generate_warning(self, collision_analysis: Dict[str, Any], weather_analysis: Optional[Dict[str, Any]] = None) -> str:
        pass

    @abstractmethod
    async def generate_warning_async(self, collision_analysis: Dict[str, Any], weather_analysis: Optional[Dict[str, Any]] = None) -> str:
        pass

class GeminiWarningGenerator(WarningGenerator):
    """Fast LLM-powered warning generator with fallback"""
    
    def __init__(self):
        self.model = None
        self.cache = {}  # Simple warning cache for speed
        
        if not GEMINI_AVAILABLE:
            print("⚠️  Gemini features disabled.")
            return

        try:
            self.model = get_gemini_model()
            if self.model:
                print("✅ GeminiWarningGenerator is ready.")
            else:
                 print("⚠️  Gemini model not available to WarningGenerator.")

        except Exception as e:
            print(f"⚠️  Error getting Gemini model for warnings: {e}")
            self.model = None

    def generate_warning(self, collision_analysis: Dict[str, Any], weather_analysis: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a simple, non-LLM warning message.
        """
        if not collision_analysis:
            return ""
        
        risk_level = collision_analysis.get('risk_level', 'None')
        return self._generate_simple_warning(risk_level)

    async def generate_warning_async(self, collision_analysis: Dict[str, Any], weather_analysis: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a warning using Gemini, with a simple fallback.
        """
        if not self.model or not collision_analysis:
            return self.generate_warning(collision_analysis)

        risk_level = collision_analysis.get('risk_level', 'None')
        if risk_level not in ['High', 'Critical']:
             return "" # No warning for low risk

        prompt = self._build_prompt(collision_analysis, weather_analysis)

        if prompt in self.cache:
            return self.cache[prompt]

        try:
            response = await self.model.generate_content_async(
                prompt,
                request_options={'timeout': config.GEMINI_TIMEOUT}
            )
            warning = response.text.strip().replace('"', '').replace('\n', ' ')
            self.cache[prompt] = warning
            return warning
        except Exception as e:
            print(f"Gemini API error: {e}")
            return self.generate_warning(collision_analysis)

    def _build_prompt(self, collision_analysis: Dict[str, Any], weather_analysis: Optional[Dict[str, Any]] = None) -> str:
        """Builds a detailed prompt for the Gemini API."""
        
        primary_threat = collision_analysis.get('primary_threat')
        if not primary_threat:
            return "" # Cannot generate a good prompt without a threat

        prompt = "You are an expert automotive safety assistant. "
        prompt += "Generate a very short, clear, and urgent warning message for a driver. "
        prompt += "Maximum 7 words.\n\n"
        prompt += f"## Situation:\n"
        prompt += f"- **Risk Level:** {collision_analysis.get('risk_level', 'N/A')}\n"

        if primary_threat:
            prompt += f"- **Primary Threat:** A {primary_threat.get('class_name', 'vehicle')} is "
            prompt += f"{primary_threat.get('distance', 0):.1f}m ahead.\n"
            if primary_threat.get('ttc', float('inf')) != float('inf'):
                prompt += f"- **Time to Collision:** {primary_threat.get('ttc', 0):.1f} seconds.\n"

        if weather_analysis and weather_analysis.ai_analysis:
            prompt += f"- **Weather Conditions:** {weather_analysis.ai_analysis.driver_advice}\n"

        prompt += "\n## Warning:"
        return prompt

    def _generate_simple_warning(self, risk_level: str) -> str:
        """Fast fallback warnings"""
        warnings = {
            'Critical': 'Immediate brake. Collision imminent.',
            'High': 'Brake now. High collision risk.',
            'Medium': 'Slow down. Object ahead.',
            'Low': 'Stay alert.'
        }
        return warnings.get(risk_level, '')
