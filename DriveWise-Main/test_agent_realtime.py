#!/usr/bin/env python3
"""
Real-time Test for Weather AI Agent
This script tests the WeatherAIAgent to ensure it can fetch and analyze
weather data in real-time without blocking.
"""

import sys
import os
import asyncio
import time

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.weather_detection import (
    get_location_service,
    get_weather_client,
    get_weather_agent
)

async def test_agent_realtime():
    """Tests the full, real-time workflow of the weather agent."""
    print("--- 🧪 Starting Real-time Weather AI Agent Test ---")

    # 1. Initialize Services
    print("\n[Step 1/4] Initializing services...")
    try:
        location_service = get_location_service()
        weather_client = get_weather_client()
        weather_agent = get_weather_agent()
        print("✅ Services initialized successfully.")
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return

    # 2. Get Location
    print("\n[Step 2/4] Fetching real-time location...")
    start_time = time.time()
    await location_service.initialize()
    location_data = await location_service.get_current_location(force_update=True)
    location_time = time.time() - start_time

    if location_data:
        print(f"✅ Location found in {location_time:.2f}s: {location_data.address} (Source: {location_data.source})")
    else:
        print("❌ Failed to get location. Aborting test.")
        return

    # 3. Get Weather Data
    print("\n[Step 3/4] Fetching weather data...")
    start_time = time.time()
    location_string = location_service.get_location_string()
    weather_data = await weather_client.get_weather_data(location_string)
    weather_time = time.time() - start_time

    if weather_data:
        print(f"✅ Weather data for '{weather_data.location}' retrieved in {weather_time:.2f}s.")
        print(f"   Condition: {weather_data.condition}, Temp: {weather_data.temperature}°C")
    else:
        print("❌ Failed to get weather data. Aborting test.")
        return

    # 4. Get AI Analysis
    print("\n[Step 4/4] Requesting AI analysis from Gemini...")
    start_time = time.time()
    analysis = await weather_agent.analyze_weather_conditions(weather_data, location_data)
    ai_time = time.time() - start_time

    if analysis:
        print(f"✅ AI analysis received in {ai_time:.2f}s!")
        print("-" * 20)
        print(f"  Condition: {analysis.condition.upper()}")
        print(f"  Visibility: {analysis.visibility_level.replace('_', ' ').title()}")
        print(f"  Road Risk: {analysis.road_risk.upper()}")
        print(f"  Driver Advice: {analysis.driver_advice}")
        print(f"  Risk Multiplier: {analysis.risk_multiplier}x")
        print("-" * 20)
    else:
        print("❌ AI analysis failed or returned no data.")
        return

    print("\n--- ✅ Real-time Weather AI Agent Test PASSED ---")


if __name__ == "__main__":
    try:
        asyncio.run(test_agent_realtime())
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}") 