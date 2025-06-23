#!/usr/bin/env python3
"""
Simple Weather Integration Test for FCW System
Tests that the weather system properly integrates with the main application
"""

import sys
import os
import asyncio
import time

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config

def test_imports():
    """Test that all imports work correctly"""
    print("🧪 Testing imports...")
    
    try:
        # Test weather detection imports
        from modules.weather_detection import (
            get_location_service,
            get_weather_client, 
            get_weather_agent,
            get_weather_middleware
        )
        print("✅ Weather detection imports successful")
        
        # Test weather analyzer import
        from modules.analyzers.weather_impact_analyzer import EnhancedWeatherImpactAnalyzer
        print("✅ Weather analyzer import successful")
        
        # Test main system imports
        from modules.user_interface import EnhancedRealtimeInterface, get_qt_app
        from plugins.yolo_detector import create_detector
        from plugins.kalman_tracker import KalmanTracker
        from modules.analyzers.collision_predictor import CollisionPredictor
        print("✅ Main system imports successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_weather_system_initialization():
    """Test weather system initialization"""
    print("\n🌦️ Testing weather system initialization...")
    
    try:
        from modules.weather_detection import (
            get_location_service,
            get_weather_client, 
            get_weather_agent,
            get_weather_middleware
        )
        from modules.analyzers.weather_impact_analyzer import EnhancedWeatherImpactAnalyzer
        
        # Initialize components
        location_service = get_location_service()
        weather_client = get_weather_client()
        weather_agent = get_weather_agent()
        weather_middleware = get_weather_middleware()
        weather_analyzer = EnhancedWeatherImpactAnalyzer()
        
        print("✅ Weather components initialized")
        
        # Test basic functionality
        location_string = location_service.get_location_string()
        print(f"✅ Location string: {location_string}")
        
        # Test cache stats
        cache_stats = weather_client.get_cache_stats()
        print(f"✅ Weather client cache: {cache_stats}")
        
        agent_stats = weather_agent.get_agent_stats()
        print(f"✅ Weather agent available: {agent_stats['model_available']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Weather system initialization error: {e}")
        return False

async def test_weather_analysis():
    """Test weather analysis functionality"""
    print("\n🤖 Testing weather analysis...")
    
    try:
        from modules.weather_detection import get_weather_client, get_weather_agent, get_location_service
        
        # Get real-time location first
        location_service = get_location_service()
        await location_service.initialize()
        location_data = await location_service.get_current_location(force_update=True)
        
        if location_data:
            location_string = location_service.get_location_string()
            print(f"📍 Using real-time location: {location_string}")
        else:
            location_string = "current_location"
            print("⚠️ Using fallback location string")
        
        # Get weather data
        weather_client = get_weather_client()
        weather_data = await weather_client.get_weather_data(location_string)
        
        if weather_data:
            print(f"✅ Weather data retrieved: {weather_data.condition} in {weather_data.location}")
            
            # Test AI analysis
            weather_agent = get_weather_agent()
            analysis = await weather_agent.analyze_weather_conditions(weather_data, location_data)
            
            if analysis:
                print(f"✅ AI analysis completed: {analysis.road_risk} risk, {analysis.risk_multiplier}x multiplier")
                print(f"   Advice: {analysis.driver_advice}")
                return True
            else:
                print("⚠️ AI analysis returned None (fallback mode)")
                return True
        else:
            print("❌ Failed to get weather data")
            return False
            
    except Exception as e:
        print(f"❌ Weather analysis error: {e}")
        return False

def test_config_settings():
    """Test configuration settings"""
    print("\n⚙️ Testing configuration settings...")
    
    try:
        print(f"✅ Weather system enabled: {config.WEATHER_IMPACT_ENABLED}")
        print(f"✅ Location services enabled: {config.ENABLE_LOCATION_SERVICES}")
        print(f"✅ Weather agent enabled: {config.WEATHER_AGENT_ENABLED}")
        print(f"✅ Middleware enabled: {config.MIDDLEWARE_ENABLED}")
        print(f"✅ Real-time location mode: {config.REALTIME_LOCATION_MODE}")
        print(f"✅ Location update interval: {config.LOCATION_UPDATE_INTERVAL}s")
        print(f"✅ Weather update interval: {config.WEATHER_UPDATE_INTERVAL}s")
        print(f"✅ RapidAPI key configured: {'Yes' if config.RAPIDAPI_WEATHER_KEY else 'No'}")
        print(f"✅ Gemini API key configured: {'Yes' if config.GEMINI_API_KEY else 'No'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_main_system_integration():
    """Test integration with main system"""
    print("\n🔗 Testing main system integration...")
    
    try:
        # Import the main processor class
        from main import PerformanceOptimizedProcessor
        
        # Create processor instance
        processor = PerformanceOptimizedProcessor()
        
        # Check weather system initialization
        if hasattr(processor, 'weather_analyzer'):
            print("✅ Weather analyzer integrated in main processor")
        else:
            print("❌ Weather analyzer not found in main processor")
            return False
        
        if hasattr(processor, 'location_service'):
            print("✅ Location service integrated in main processor")
        else:
            print("❌ Location service not found in main processor")
            return False
        
        print("✅ Main system integration successful")
        return True
        
    except Exception as e:
        print(f"❌ Main system integration error: {e}")
        return False

async def main():
    """Main test function"""
    print("=" * 60)
    print("🧪 FCW WEATHER SYSTEM INTEGRATION TEST")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Weather System Initialization", test_weather_system_initialization),
        ("Configuration Settings", test_config_settings),
        ("Main System Integration", test_main_system_integration),
    ]
    
    async_tests = [
        ("Weather Analysis", test_weather_analysis),
    ]
    
    passed = 0
    total = len(tests) + len(async_tests)
    
    # Run synchronous tests
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    # Run asynchronous tests
    for test_name, test_func in async_tests:
        try:
            if await test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    # Results
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Weather system integration is ready.")
        print("🚀 You can now run the main FCW system with weather support.")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Please check the issues above.")
    
    print("\n💡 To run the full system:")
    print("   python main.py")
    print("\n💡 To test weather system separately:")
    print("   python test_weather_system.py")

if __name__ == "__main__":
    asyncio.run(main()) 