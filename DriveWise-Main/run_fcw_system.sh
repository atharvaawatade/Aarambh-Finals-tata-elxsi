#!/bin/bash

# FCW Pro - Enterprise Forward Collision Warning System
# Tata Elxsi Demonstration Script

echo "🚗 Starting FCW Pro - Enterprise Edition"
echo "========================================"
echo "Company: Tata Elxsi"
echo "Version: 2.0.0 Enterprise"
echo "Build: 2024"
echo ""

# Activate virtual environment
echo "📦 Activating Python environment..."
source venv/bin/activate

# Check if all dependencies are installed
echo "🔍 Checking dependencies..."
python -c "import ultralytics, cv2, numpy, google.generativeai, PyQt5; print('✅ All dependencies available')"

# Set Gemini API key if provided
if [ ! -z "$GEMINI_API_KEY" ]; then
    echo "🤖 Gemini API key detected - AI features enabled"
else
    echo "⚠️  Using demo API key - Replace with production key for deployment"
fi

echo ""
echo "🎯 Launching FCW Pro Enterprise System..."
echo "📊 Features: AI-Powered | Real-Time | Enterprise-Grade"
echo ""

# Launch the application
python main.py

echo ""
echo "👋 FCW Pro Enterprise System terminated"
echo "Thank you for the demonstration!" 