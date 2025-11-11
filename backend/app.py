from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from config import Config
import certifi

# Blueprints
from routes.employees import employees_bp, ensure_indexes as ensure_employee_indexes
from routes.resume import resume_bp
from routes.projects import projects_bp, ensure_indexes as ensure_project_indexes
from routes.match import match_bp


def create_app():
    app = Flask(__name__)

    # --- CORS (explicit origins for dev; tweak for prod as needed) ---
    CORS(
        app,
        resources={r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}},
        supports_credentials=False,  # set True only if you actually use cookies
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["Content-Type"],
        max_age=86400,
    )

    # --- Upload size limit (MB) ---
    app.config["MAX_CONTENT_LENGTH"] = (getattr(Config, "MAX_UPLOAD_MB", 10) or 10) * 1024 * 1024

    # --- Mongo connection ---
    db = None
    try:
        client = MongoClient(
            Config.MONGO_URI,
            tls=True,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=getattr(Config, "MONGO_TIMEOUT_MS", 8000),
            connectTimeoutMS=getattr(Config, "MONGO_TIMEOUT_MS", 8000),
            socketTimeoutMS=getattr(Config, "MONGO_TIMEOUT_MS", 8000),
        )
        client.admin.command("ping")
        db = client[getattr(Config, "DB_NAME", "smart_resource_allocation")]
        app.config["DB"] = db

        with app.app_context():
            # ensure indexes for collections we manage here
            ensure_employee_indexes()
            ensure_project_indexes()

        print("✅ Connected to MongoDB")
    except Exception as e:
        # Don't crash the app, but expose health info
        print("❌ MongoDB Connection Error:", e)
        app.config["DB"] = None

    # --- Health check ---
    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok", "db_connected": app.config.get("DB") is not None})

    # --- Blueprints (paths remain the same to match your frontend) ---
    app.register_blueprint(employees_bp, url_prefix="/employees")
    app.register_blueprint(resume_bp, url_prefix="/resume")
    app.register_blueprint(projects_bp, url_prefix="/projects")
    app.register_blueprint(match_bp, url_prefix="/match")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=getattr(Config, "DEBUG", True), host=getattr(Config, "HOST", "0.0.0.0"), port=getattr(Config, "PORT", 5000))
