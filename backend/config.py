import os

class Config:
    # --- Server ---
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5001"))
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"

    # --- Mongo ---
    # Example: "mongodb+srv://user:pass@cluster0.mongodb.net/?retryWrites=true&w=majority"
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME = os.getenv("DB_NAME", "resource_allocation")
    MONGO_TIMEOUT_MS = int(os.getenv("MONGO_TIMEOUT_MS", "8000"))

    # --- Uploads ---
    MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "15"))

    # --- Gemini (optional; set SKIP_GEMINI=true to disable) ---
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    SKIP_GEMINI = os.getenv("SKIP_GEMINI", "true").lower() == "true"
