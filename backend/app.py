from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from config import Config
from dotenv import load_dotenv
import certifi
import os

# ---- Load .env BEFORE touching Config values ----
load_dotenv()  # makes MONGO_URI, DB_NAME, etc. available to Config

# Blueprints
from routes.employees import employees_bp, ensure_indexes as ensure_employee_indexes
from routes.resume import resume_bp
# from routes.projects import projects_bp, ensure_indexes as ensure_project_indexes
# from routes.match import match_bp


def _make_mongo_client(uri: str, timeout_ms: int) -> MongoClient:
    """
    Use TLS for mongodb+srv URIs (Atlas). Do NOT force TLS for localhost.
    """
    is_srv = uri.startswith("mongodb+srv://")
    kwargs = dict(
        serverSelectionTimeoutMS=timeout_ms,
        connectTimeoutMS=timeout_ms,
        socketTimeoutMS=timeout_ms,
    )
    if is_srv:
        kwargs["tls"] = True
        kwargs["tlsCAFile"] = certifi.where()
    return MongoClient(uri, **kwargs)


def _redact(uri: str) -> str:
    # Hide password if present
    try:
        if "@" in uri:  # guard for odd unicode
            uri = uri.replace("“", '"').replace("”", '"')
        prefix, rest = uri.split("://", 1)
        if "@" in rest:
            creds, host = rest.split("@", 1)
            if ":" in creds:
                user = creds.split(":", 1)[0]
                return f"{prefix}://{user}:***@{host}"
        return uri
    except Exception:
        return uri


def create_app():
    app = Flask(__name__)

    # CORS for Vite dev server
    CORS(
        app,
        resources={r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}},
        supports_credentials=False,
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
        max_age=86400,
    )

    # Upload limit
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_UPLOAD_MB * 1024 * 1024

    # --- Mongo connection ---
    db = None
    try:
        mongo_uri = os.getenv("MONGO_URI", Config.MONGO_URI)
        db_name = os.getenv("DB_NAME", Config.DB_NAME)

        print(f"🔧 Using Mongo URI: {_redact(mongo_uri)}")
        print(f"🔧 Using DB Name : {db_name}")

        client = _make_mongo_client(mongo_uri, Config.MONGO_TIMEOUT_MS)
        client.admin.command("ping")
        db = client[db_name]
        app.config["DB"] = db

        with app.app_context():
            ensure_employee_indexes()
            # ensure_project_indexes()

        print("✅ Connected to MongoDB")
    except Exception as e:
        print("❌ MongoDB Connection Error:", e)
        app.config["DB"] = None

    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok", "db_connected": (app.config.get("DB") is not None)})

    # Routes
    app.register_blueprint(employees_bp, url_prefix="/employees")
    app.register_blueprint(resume_bp, url_prefix="/resume")
    # app.register_blueprint(projects_bp, url_prefix="/projects")
    # app.register_blueprint(match_bp, url_prefix="/match")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)
