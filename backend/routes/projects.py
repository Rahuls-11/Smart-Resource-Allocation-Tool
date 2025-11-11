from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from bson import ObjectId

projects_bp = Blueprint("projects", __name__)

def ensure_indexes():
    db = current_app.config["DB"]
    db.projects.create_index([("project_name", 1)])
    db.projects.create_index("required_skills")

def _public(doc):
    return {
        "id": str(doc["_id"]),
        "project_name": doc.get("project_name"),
        "required_skills": doc.get("required_skills", []),
        "duration": doc.get("duration"),
        "timeline": doc.get("timeline", {}),
        "priority": doc.get("priority", "Medium"),
        "headcount": doc.get("headcount", 1),
        "status": doc.get("status", "Open"),
        "created_at": doc.get("created_at"),
    }

@projects_bp.route("", methods=["POST"])
def create_project():
    db = current_app.config["DB"]
    body = request.get_json(force=True)
    doc = {
        "project_name": body["project_name"],
        "required_skills": body.get("required_skills", []),
        "duration": body.get("duration"),
        "timeline": body.get("timeline", {}),
        "priority": body.get("priority", "Medium"),
        "headcount": body.get("headcount", 1),
        "status": "Open",
        "created_at": datetime.utcnow(),
    }
    res = db.projects.insert_one(doc)
    doc["_id"] = res.inserted_id
    return jsonify({"ok": True, "project": _public(doc)}), 201

@projects_bp.route("", methods=["GET"])
def list_projects():
    db = current_app.config["DB"]
    cur = db.projects.find({}).sort("created_at", -1)
    return jsonify({"ok": True, "data": [_public(x) for x in cur]})

@projects_bp.route("/<id>", methods=["GET"])
def get_project(id):
    db = current_app.config["DB"]
    doc = db.projects.find_one({"_id": ObjectId(id)})
    if not doc:
        return jsonify({"ok": False, "error": "Not found"}), 404
    return jsonify({"ok": True, "project": _public(doc)})
