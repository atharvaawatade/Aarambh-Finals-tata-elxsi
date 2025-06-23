"""
Centralized Gemini API Initializer for FCW System
"""
import logging
import threading
import config

# Try to import Gemini, but don't fail if not available
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

_gemini_initialized = False
_init_lock = threading.Lock()
_gemini_model = None

def initialize_gemini():
    """
    Initializes the Gemini client if not already done.
    This function is thread-safe.
    """
    global _gemini_initialized, _gemini_model, GEMINI_AVAILABLE

    if not GEMINI_AVAILABLE:
        logging.warning("Gemini library not installed. AI features will be disabled.")
        return

    with _init_lock:
        if _gemini_initialized:
            return

        api_key = config.GEMINI_API_KEY
        if not api_key or "YOUR_GEMINI_API_KEY" in api_key or "AIzaSyBuppTQO6Wt2saLnUF8tFrip9Ih4DFBuo4" in api_key:
            logging.warning("Gemini API key not configured. AI features will be disabled.")
            GEMINI_AVAILABLE = False
            _gemini_initialized = True # Mark as initialized to prevent re-attempts
            return

        try:
            genai.configure(api_key=api_key)
            # Use a versatile and fast model
            model_name = config.GEMINI_MODEL if hasattr(config, 'GEMINI_MODEL') else 'gemini-2.5-flash'
            _gemini_model = genai.GenerativeModel(model_name)
            logging.info(f"✅ Gemini client initialized successfully with model '{model_name}'.")
            _gemini_initialized = True
        except Exception as e:
            logging.error(f"❌ Failed to initialize Gemini client: {e}")
            GEMINI_AVAILABLE = False # Disable on failure
            _gemini_initialized = True # Mark as initialized to prevent re-attempts


def get_gemini_model():
    """
    Returns the initialized Gemini model.
    Will initialize on first call if needed.
    """
    if not _gemini_initialized:
        initialize_gemini()
    
    return _gemini_model if GEMINI_AVAILABLE else None 