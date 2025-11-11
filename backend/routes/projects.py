from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from bson import ObjectId
from typing import Any, Dict, List, Optional

projects_bp = Blueprint("projects", __name__)

# ---------- Helpers ----------
def _coerce_skills(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(s).strip() for s in value if str(s).strip()]
    if isinstance(value, str):
        return [s.strip() for s in value.split(",") if s.strip()]
    return []

def _oid(s: str) -> Optional[ObjectId]:
    try:
        return ObjectId(str(s))
    except Exception:
        return None

def _public(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc["_id"]),
        "project_name": doc.get("project_name"),
        "required_skills": doc.get("required_skills", []),
        "description": doc.get("description"),
        "priority": doc.get("priority", "Medium"),
        "status": doc.get("status", "Open"),
        "start_date": doc.get("start_date"),   # ISO (yyyy-mm-dd) as string
        "end_date": doc.get("end_date"),       # ISO (yyyy-mm-dd) as string
        "duration": doc.get("duration"),
        "headcount": doc.get("headcount", 1),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }

def ensure_indexes():
    db = current_app.config.get("DB")
    if db is None:
        return
    db.projects.create_index([("project_name", 1)])
    db.projects.create_index("required_skills")
    db.projects.create_index("status")
    db.projects.create_index("priority")
    db.projects.create_index("start_date")
    db.projects.create_index("end_date")

# ---------- Routes ----------
@projects_bp.route("", methods=["POST"])
def create_project():
    db = current_app.config.get("DB")
    if db is None:
        return jsonify({"ok": False, "error": "DB not connected"}), 500

    body = request.get_json(force=True, silent=True) or {}
    name = (body.get("project_name") or "").strip()
    if not name:
        return jsonify({"ok": False, "error": "project_name is required"}), 400

    doc = {
        "project_name": name,
        "required_skills": _coerce_skills(body.get("required_skills")),
        "description": (body.get("description") or "").strip() or None,
        "priority": (body.get("priority") or "Medium"),
        "status": (body.get("status") or "Open"),
        "start_date": (body.get("start_date") or "").strip() or None,  # expect "YYYY-MM-DD"
        "end_date": (body.get("end_date") or "").strip() or None,
        "duration": (body.get("duration") or "").strip() or None,
        "headcount": int(body.get("headcount") or 0) or None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    res = db.projects.insert_one(doc)
    doc["_id"] = res.inserted_id
    return jsonify({"ok": True, "project": _public(doc)}), 201

@projects_bp.route("", methods=["GET"])
def list_projects():
    db = current_app.config.get("DB")
    if db is None:
        return jsonify({"ok": False, "error": "DB not connected"}), 500

    # Optional server-side filters
    q = request.args.get("q")
    skill = request.args.get("skill")
    status = request.args.get("status")
    page = int(request.args.get("page", "1") or "1")
    limit = int(request.args.get("limit", "50") or "50")
    sort = (request.args.get("sort") or "-created_at").strip()

    query: Dict[str, Any] = {}
    if q:
        query["$or"] = [
            {"project_name": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
        ]
    if skill:
        query["required_skills"] = {"$regex": skill, "$options": "i"}
    if status and status in ("Open", "Closed"):
        query["status"] = status

    sort_spec = [("created_at", -1)]
    if sort:
        direction = -1 if sort.startswith("-") else 1
        field = sort[1:] if sort.startswith("-") else sort
        sort_spec = [(field, direction)]

    cur = db.projects.find(query).sort(sort_spec)
    total = db.projects.count_documents(query)
    cur = cur.skip(max(page - 1, 0) * max(limit, 1)).limit(max(limit, 1))

    data = [_public(x) for x in cur]
    return jsonify({"ok": True, "data": data, "pagination": {"page": page, "limit": limit, "total": total}}), 200

@projects_bp.route("/<id>", methods=["GET"])
def get_project(id):
    db = current_app.config.get("DB")
    if db is None:
        return jsonify({"ok": False, "error": "DB not connected"}), 500
    oid = _oid(id)
    if oid is None:
        return jsonify({"ok": False, "error": "Invalid id"}), 400
    doc = db.projects.find_one({"_id": oid})
    if not doc:
        return jsonify({"ok": False, "error": "Not found"}), 404
    return jsonify({"ok": True, "project": _public(doc)}), 200

@projects_bp.route("/<id>", methods=["PUT", "PATCH"])
def update_project(id):
    db = current_app.config.get("DB")
    if db is None:
        return jsonify({"ok": False, "error": "DB not connected"}), 500
    oid = _oid(id)
    if oid is None:
        return jsonify({"ok": False, "error": "Invalid id"}), 400

    body = request.get_json(force=True, silent=True) or {}
    body.pop("_id", None)

    update: Dict[str, Any] = {}
    if "project_name" in body:
        update["project_name"] = (body.get("project_name") or "").strip() or None
    if "required_skills" in body:
        update["required_skills"] = _coerce_skills(body.get("required_skills"))
    if "description" in body:
        update["description"] = (body.get("description") or "").strip() or None
    if "priority" in body:
        update["priority"] = body.get("priority") or "Medium"
    if "status" in body:
        update["status"] = body.get("status") or "Open"
    if "start_date" in body:
        update["start_date"] = (body.get("start_date") or "").strip() or None
    if "end_date" in body:
        update["end_date"] = (body.get("end_date") or "").strip() or None
    if "duration" in body:
        update["duration"] = (body.get("duration") or "").strip() or None
    if "headcount" in body:
        try:
            update["headcount"] = int(body.get("headcount"))
        except Exception:
            update["headcount"] = None

    update["updated_at"] = datetime.utcnow()

    db.projects.update_one({"_id": oid}, {"$set": update})
    doc = db.projects.find_one({"_id": oid})
    if not doc:
        return jsonify({"ok": False, "error": "Not found after update"}), 404
    return jsonify({"ok": True, "project": _public(doc)}), 200

@projects_bp.route("/<id>", methods=["DELETE"])
def delete_project(id):
    db = current_app.config.get("DB")
    if db is None:
        return jsonify({"ok": False, "error": "DB not connected"}), 500
    oid = _oid(id)
    if oid is None:
        return jsonify({"ok": False, "error": "Invalid id"}), 400
    res = db.projects.delete_one({"_id": oid})
    if res.deleted_count == 0:
        return jsonify({"ok": False, "error": "Not found"}), 404
    return jsonify({"ok": True, "deleted": id}), 200
