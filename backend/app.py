from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from config import Config
import certifi

from routes.employees import employees_bp, ensure_indexes as ensure_employee_indexes
from routes.resume import resume_bp
from routes.projects import projects_bp, ensure_indexes as ensure_project_indexes
from routes.match import match_bp
from routes.hr_allocation import hr_allocation_bp  # NEW IMPORT

def create_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True)
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_UPLOAD_MB * 1024 * 1024

    db = None
    try:
        client = MongoClient(
            Config.MONGO_URI,
            tls=True,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=Config.MONGO_TIMEOUT_MS,
            connectTimeoutMS=Config.MONGO_TIMEOUT_MS,
            socketTimeoutMS=Config.MONGO_TIMEOUT_MS,
        )
        client.admin.command("ping")
        db = client[Config.DB_NAME]
        app.config["DB"] = db

        with app.app_context():
            ensure_employee_indexes()
            ensure_project_indexes()

        print("✅ Connected to MongoDB")
    except Exception as e:
        print("❌ MongoDB Connection Error:", e)

    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok", "db_connected": db is not None})

    app.register_blueprint(employees_bp, url_prefix="/employees")
    app.register_blueprint(resume_bp, url_prefix="/resume")
    app.register_blueprint(projects_bp, url_prefix="/projects")
    app.register_blueprint(match_bp, url_prefix="/match")
    app.register_blueprint(hr_allocation_bp, url_prefix="/hr_allocation")  # NEW

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=Config.DEBUG, host=Config.HOST, port=Config.PORT)
