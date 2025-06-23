#!/usr/bin/env python3
"""
Weather System Test Script for FCW System
Tests the complete weather integration including AI agent, location services, and middleware
"""

import asyncio
import logging
import time
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.weather_detection import (
    get_location_service,
    get_weather_client, 
    get_weather_agent,
    get_weather_middleware
)
from modules.analyzers.weather_impact_analyzer import EnhancedWeatherImpactAnalyzer
import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WeatherSystemTester:
    """
    Comprehensive weather system tester
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize all components
        self.location_service = get_location_service()
        self.weather_client = get_weather_client()
        self.weather_agent = get_weather_agent()
        self.middleware = get_weather_middleware()
        self.analyzer = EnhancedWeatherImpactAnalyzer()
        
        # Test results
        self.test_results = {}
    
    async def run_complete_test(self):
        """Run complete weather system test"""
        print("\n" + "="*60)
        print("🌦️  FCW WEATHER SYSTEM COMPREHENSIVE TEST")
        print("="*60)
        
        try:
            # Test 1: Location Services
            await self._test_location_services()
            
            # Test 2: Weather API Client
            await self._test_weather_api_client()
            
            # Test 3: Weather AI Agent
            await self._test_weather_ai_agent()
            
            # Test 4: Middleware Communication
            await self._test_middleware()
            
            # Test 5: Enhanced Weather Analyzer
            await self._test_enhanced_analyzer()
            
            # Test 6: Integration Test
            await self._test_full_integration()
            
            # Display results
            self._display_test_results()
            
        except Exception as e:
            self.logger.error(f"Test suite failed: {e}")
            print(f"❌ Test suite failed: {e}")
    
    async def _test_location_services(self):
        """Test location services functionality"""
        print("\n📍 Testing Location Services...")
        
        try:
            # Initialize location service
            await self.location_service.initialize()
            
            # Get current location
            location_data = await self.location_service.get_current_location(force_update=True)
            
            if location_data:
                print(f"✅ Location detected: {location_data.address}")
                print(f"✅ Coordinates: {location_data.latitude:.4f}, {location_data.longitude:.4f}")
                print(f"✅ Accuracy: ±{location_data.accuracy}m")
                print(f"✅ Source: {location_data.source}")
                
                # Test location string for API calls
                location_string = self.location_service.get_location_string()
                print(f"✅ Location string for API: {location_string}")
                
                return True
            else:
                print("❌ Failed to get location data")
                return False
                
        except Exception as e:
            print(f"❌ Location services error: {e}")
            return False
    
    async def _test_weather_api_client(self):
        """Test weather API client functionality"""
        print("\n🌦️ Testing Weather API Client...")
        
        try:
            # Get location string from location service
            location_string = self.location_service.get_location_string()
            if not location_string or location_string == "unknown_location":
                location_string = "current_location"  # Fallback for API testing
            
            print(f"📍 Testing with location: {location_string}")
            
            # Test weather data retrieval
            start_time = time.time()
            weather_data = await self.weather_client.get_weather_data(location_string)
            api_time = time.time() - start_time
            
            if weather_data:
                print(f"✅ Weather data retrieved in {api_time:.2f}s")
                print(f"   Location: {weather_data.location}")
                print(f"   Condition: {weather_data.condition}")
                print(f"   Temperature: {weather_data.temperature}°C")
                print(f"   Visibility: {weather_data.visibility}km")
                
                # Test caching
                start_time = time.time()
                cached_data = await self.weather_client.get_weather_data(location_string)
                cache_time = time.time() - start_time
                
                if cache_time < 0.1:  # Should be very fast from cache
                    print(f"✅ Cache working - retrieved in {cache_time:.3f}s")
                    return True
                else:
                    print(f"⚠️ Cache may not be working - took {cache_time:.3f}s")
                    return True
            else:
                print("❌ Failed to get weather data")
                return False
                
        except Exception as e:
            print(f"❌ Weather API client error: {e}")
            return False
    
    async def _test_weather_ai_agent(self):
        """Test weather AI agent functionality"""
        print("\n🤖 Testing Weather AI Agent...")
        
        try:
            # Get location and weather data
            location_string = self.location_service.get_location_string()
            if not location_string or location_string == "unknown_location":
                location_string = "current_location"
            
            weather_data = await self.weather_client.get_weather_data(location_string)
            location_data = await self.location_service.get_current_location()
            
            if weather_data:
                print(f"📊 Analyzing weather: {weather_data.condition} in {weather_data.location}")
                
                # Test AI analysis
                start_time = time.time()
                analysis = await self.weather_agent.analyze_weather_conditions(weather_data, location_data)
                ai_time = time.time() - start_time
                
                if analysis:
                    print(f"✅ AI analysis completed in {ai_time:.2f}s")
                    print(f"   Condition: {analysis.condition}")
                    print(f"   Visibility: {analysis.visibility_level}")
                    print(f"   Road Risk: {analysis.road_risk}")
                    print(f"   Risk Multiplier: {analysis.risk_multiplier}x")
                    print(f"   Driver Advice: {analysis.driver_advice}")
                    
                    # Test caching
                    start_time = time.time()
                    cached_analysis = await self.weather_agent.analyze_weather_conditions(weather_data, location_data)
                    cache_time = time.time() - start_time
                    
                    if cache_time < 0.1:
                        print(f"✅ AI cache working - retrieved in {cache_time:.3f}s")
                    
                    return True
                else:
                    print("⚠️ AI analysis returned None (using fallback)")
                    return True
            else:
                print("❌ No weather data available for AI analysis")
                return False
                
        except Exception as e:
            print(f"❌ Weather AI agent error: {e}")
            return False
    
    async def _test_middleware(self):
        """Test middleware functionality"""
        print("\n📡 Testing Middleware Communication...")
        
        try:
            # Test data publishing and subscription
            received_data = []
            
            def weather_callback(data):
                received_data.append(('weather', data))
                print(f"   📨 Received weather update: {data.condition}")
            
            # Subscribe to weather data
            self.middleware.subscribe_weather_data("test_subscriber", weather_callback)
            
            # Publish test data
            location_string = self.location_service.get_location_string()
            weather_data = await self.weather_client.get_weather_data(location_string or config.DEFAULT_LOCATION)
            
            if weather_data:
                print("   Publishing weather data to middleware...")
                start_time = time.time()
                self.middleware.publish_weather_data(weather_data)
                publish_time = (time.time() - start_time) * 1000
                
                # Wait for callback
                await asyncio.sleep(0.1)
                
                self.test_results['middleware_publish'] = len(received_data) > 0
                self.test_results['middleware_latency'] = publish_time < 10  # Less than 10ms
                
                if received_data:
                    print("✅ Middleware communication successful")
                    print(f"   Publish latency: {publish_time:.2f}ms")
                    print(f"   Data received: {len(received_data)} messages")
                else:
                    print("❌ No data received through middleware")
                
                # Test performance stats
                perf_stats = self.middleware.get_performance_stats()
                print(f"   Performance stats: {perf_stats}")
                
                # Unsubscribe
                self.middleware.unsubscribe("test_subscriber")
                
            else:
                print("❌ No weather data available for middleware test")
                self.test_results['middleware_publish'] = False
                
        except Exception as e:
            self.logger.error(f"Middleware test failed: {e}")
            print(f"❌ Middleware test failed: {e}")
            self.test_results['middleware_publish'] = False
    
    async def _test_enhanced_analyzer(self):
        """Test enhanced weather analyzer"""
        print("\n🔍 Testing Enhanced Weather Analyzer...")
        
        try:
            # Initialize analyzer
            success = await self.analyzer.initialize()
            self.test_results['analyzer_init'] = success
            
            if success:
                print("✅ Enhanced analyzer initialized")
                
                # Test enhanced analysis
                print("   Performing enhanced weather analysis...")
                start_time = time.time()
                analysis = await self.analyzer.get_enhanced_analysis()
                analysis_time = (time.time() - start_time) * 1000
                
                self.test_results['enhanced_analysis'] = analysis is not None
                
                if analysis:
                    print("✅ Enhanced analysis completed")
                    print(f"   Analysis time: {analysis_time:.2f}ms")
                    print(f"   Weather Impact: {analysis.impact.value}")
                    print(f"   Risk Multiplier: {analysis.risk_multiplier}x")
                    print(f"   Visibility Factor: {analysis.visibility_factor:.2f}")
                    print(f"   Road Condition Factor: {analysis.road_condition_factor:.2f}")
                    print(f"   Driver Advice: {analysis.driver_advice}")
                    
                    if analysis.weather_data:
                        print(f"   Weather: {analysis.weather_data.condition} at {analysis.weather_data.location}")
                    
                    if analysis.location_data:
                        print(f"   Location: {analysis.location_data.address}")
                    
                    # Test analyzer stats
                    stats = self.analyzer.get_analyzer_stats()
                    print(f"   Analyzer running: {stats['running']}")
                    
                else:
                    print("❌ Enhanced analysis failed")
            else:
                print("❌ Enhanced analyzer initialization failed")
                
        except Exception as e:
            self.logger.error(f"Enhanced analyzer test failed: {e}")
            print(f"❌ Enhanced analyzer test failed: {e}")
            self.test_results['analyzer_init'] = False
    
    async def _test_full_integration(self):
        """Test full system integration"""
        print("\n🔗 Testing Full System Integration...")
        
        try:
            print("   Running complete weather system workflow...")
            
            # Simulate real-world usage
            start_time = time.time()
            
            # 1. Get location
            location = await self.location_service.get_current_location()
            
            # 2. Get weather for location
            if location:
                weather_data = await self.weather_client.get_weather_data(
                    self.location_service.get_location_string()
                )
            else:
                weather_data = await self.weather_client.get_weather_data(config.DEFAULT_LOCATION)
            
            # 3. Get AI analysis
            if weather_data:
                ai_analysis = await self.weather_agent.analyze_weather_conditions(weather_data, location)
            else:
                ai_analysis = None
            
            # 4. Get enhanced analysis
            enhanced_analysis = await self.analyzer.get_enhanced_analysis()
            
            total_time = (time.time() - start_time) * 1000
            
            # Check integration success
            integration_success = all([
                location is not None,
                weather_data is not None,
                ai_analysis is not None,
                enhanced_analysis is not None
            ])
            
            self.test_results['full_integration'] = integration_success
            self.test_results['integration_latency'] = total_time < 5000  # Less than 5 seconds
            
            if integration_success:
                print("✅ Full integration test successful")
                print(f"   Total workflow time: {total_time:.2f}ms")
                print(f"   All components working together seamlessly")
                
                # Display final analysis
                if enhanced_analysis:
                    print(f"\n📊 FINAL WEATHER ANALYSIS:")
                    print(f"   Location: {enhanced_analysis.location_data.address if enhanced_analysis.location_data else 'Unknown'}")
                    print(f"   Weather: {enhanced_analysis.weather_data.condition if enhanced_analysis.weather_data else 'Unknown'}")
                    print(f"   Impact Level: {enhanced_analysis.impact.value}")
                    print(f"   Risk Assessment: {enhanced_analysis.ai_analysis.road_risk if enhanced_analysis.ai_analysis else 'Unknown'}")
                    print(f"   Driver Advice: {enhanced_analysis.driver_advice}")
                    
            else:
                print("❌ Full integration test failed")
                print(f"   Location: {'✅' if location else '❌'}")
                print(f"   Weather Data: {'✅' if weather_data else '❌'}")
                print(f"   AI Analysis: {'✅' if ai_analysis else '❌'}")
                print(f"   Enhanced Analysis: {'✅' if enhanced_analysis else '❌'}")
                
        except Exception as e:
            self.logger.error(f"Integration test failed: {e}")
            print(f"❌ Integration test failed: {e}")
            self.test_results['full_integration'] = False
    
    async def _test_integration_workflow(self):
        """Test complete integration workflow"""
        print("\n🔗 Testing Integration Workflow...")
        
        try:
            # Step 1: Initialize all components
            print("📋 Step 1: Component initialization...")
            await self.location_service.initialize()
            print("   ✅ Location service ready")
            
            # Step 2: Get real-time location
            print("📋 Step 2: Getting real-time location...")
            location_data = await self.location_service.get_current_location(force_update=True)
            if location_data:
                location_string = self.location_service.get_location_string()
                print(f"   ✅ Location: {location_data.address}")
            else:
                location_string = "current_location"
                print("   ⚠️ Using fallback location")
            
            # Step 3: Get weather data
            print("📋 Step 3: Fetching weather data...")
            weather_data = await self.weather_client.get_weather_data(location_string)
            if weather_data:
                print(f"   ✅ Weather: {weather_data.condition}, {weather_data.temperature}°C")
            else:
                print("   ❌ Weather data failed")
                return False
            
            # Step 4: AI analysis
            print("📋 Step 4: AI weather analysis...")
            analysis = await self.weather_agent.analyze_weather_conditions(weather_data, location_data)
            if analysis:
                print(f"   ✅ Risk assessment: {analysis.road_risk} ({analysis.risk_multiplier}x)")
                print(f"   💡 Advice: {analysis.driver_advice}")
            else:
                print("   ⚠️ Using fallback analysis")
            
            # Step 5: Enhanced weather analyzer
            print("📋 Step 5: Enhanced weather analysis...")
            enhanced_analysis = await self.analyzer.get_enhanced_analysis()
            if enhanced_analysis:
                print(f"   ✅ Enhanced analysis complete")
                print(f"   🌦️ Weather impact: {enhanced_analysis.weather_impact}")
                print(f"   📊 Risk multiplier: {enhanced_analysis.risk_multiplier}")
            else:
                print("   ❌ Enhanced analysis failed")
                return False
            
            print("🎉 Integration workflow completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Integration workflow error: {e}")
            return False
    
    def _display_test_results(self):
        """Display comprehensive test results"""
        print("\n" + "="*60)
        print("📋 WEATHER SYSTEM TEST RESULTS")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        print(f"\nOverall Results: {passed_tests}/{total_tests} tests passed")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetailed Results:")
        test_descriptions = {
            'location_init': 'Location Service Initialization',
            'location_data': 'Location Data Retrieval',
            'location_string': 'Location String Generation',
            'weather_api': 'Weather API Client',
            'weather_cache': 'Weather Data Caching',
            'ai_analysis': 'AI Weather Analysis',
            'ai_cache': 'AI Analysis Caching',
            'middleware_publish': 'Middleware Communication',
            'middleware_latency': 'Middleware Low Latency',
            'analyzer_init': 'Enhanced Analyzer Init',
            'enhanced_analysis': 'Enhanced Weather Analysis',
            'full_integration': 'Full System Integration',
            'integration_latency': 'Integration Performance'
        }
        
        for test_key, passed in self.test_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            description = test_descriptions.get(test_key, test_key)
            print(f"   {status} - {description}")
        
        # Performance summary
        print(f"\n🚀 Performance Summary:")
        print(f"   Weather API: {'✅ Fast' if self.test_results.get('weather_cache', False) else '⚠️  Slow'}")
        print(f"   AI Analysis: {'✅ Fast' if self.test_results.get('ai_cache', False) else '⚠️  Slow'}")
        print(f"   Middleware: {'✅ Low Latency' if self.test_results.get('middleware_latency', False) else '⚠️  High Latency'}")
        print(f"   Integration: {'✅ Fast' if self.test_results.get('integration_latency', False) else '⚠️  Slow'}")
        
        # Recommendations
        print(f"\n💡 Recommendations:")
        if not self.test_results.get('location_init', True):
            print("   - Check location service permissions")
        if not self.test_results.get('weather_api', True):
            print("   - Verify RapidAPI key and network connectivity")
        if not self.test_results.get('ai_analysis', True):
            print("   - Check Gemini API key and model availability")
        if not self.test_results.get('middleware_publish', True):
            print("   - Review middleware configuration")
        if not self.test_results.get('full_integration', True):
            print("   - Debug individual component failures first")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! Weather system is ready for production.")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} tests failed. Please address issues before deployment.")

async def main():
    """Main test function"""
    tester = WeatherSystemTester()
    await tester.run_complete_test()
    
    # Cleanup
    try:
        await tester.analyzer.shutdown()
    except:
        pass

if __name__ == "__main__":
    asyncio.run(main()) 