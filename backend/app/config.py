import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "")

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
OUTPUT_DIR = STATIC_DIR / "output"
TEMP_DIR = STATIC_DIR / "temp"
AUDIO_DIR = STATIC_DIR / "audio"

# Ensure directories exist
STATIC_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)

# API URLs
GROQ_API_URL = "https://api.groq.com/openai/v1"
PEXELS_API_URL = "https://api.pexels.com/videos"
PIXABAY_API_URL = "https://pixabay.com/api/"

# App settings
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB
ALLOWED_AUDIO_TYPES = ["audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav"] 

# Translation settings
DEFAULT_SOURCE_LANGUAGE = "auto"  # Auto-detect source language
TARGET_LANGUAGE = "en"  # English as target language 