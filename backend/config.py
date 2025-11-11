import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Mongo
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME = os.getenv("DB_NAME", "smart_resource_allocation")
    MONGO_TIMEOUT_MS = int(os.getenv("MONGO_TIMEOUT_MS", "5000"))

    # App
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5001"))
    MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "15"))

    # Gemini / AI
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    SKIP_GEMINI = os.getenv("SKIP_GEMINI", "false").lower() == "true"
