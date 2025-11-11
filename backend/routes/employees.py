from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
from datetime import datetime
from typing import Dict, Any, List, Optional

employees_bp = Blueprint("employees", __name__)

# ---------- Indexes ----------

def ensure_indexes():
    db = current_app.config["DB"]
    if db is None:
        return
    db.employees.create_index([("name", 1)])
    db.employees.create_index("role")
    db.employees.create_index("skills")


# ---------- Helpers ----------

def _public(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc["_id"]),
        "name": doc.get("name"),
        "role": doc.get("role"),
        "skills": doc.get("skills", []),
        "experience": doc.get("experience", []),
        "projects": doc.get("projects", []),
        "availability": doc.get("availability"),  # optional free-text
        "availability_dates": doc.get("availability_dates", []),  # list of 'YYYY-MM-DD'
        "cv_url": doc.get("cv_url"),
        "portfolio_url": doc.get("portfolio_url"),
        "cv_file_id": str(doc.get("cv_file_id")) if doc.get("cv_file_id") else None,
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }

def _coerce_skills(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(s).strip() for s in value if str(s).strip()]
    if isinstance(value, str):
        return [s.strip() for s in value.split(",") if s.strip()]
    return []

def _coerce_dates(value: Any) -> List[str]:
    """
    Accepts list[str|date-like] or CSV; normalizes to 'YYYY-MM-DD' strings.
    """
    if value is None:
        return []
    if isinstance(value, list):
        out = []
        for v in value:
            s = str(v).strip()
            if not s:
                continue
            # accept full ISO and truncate to date
            if "T" in s:
                s = s.split("T", 1)[0]
            out.append(s)
        # de-dup and sort
        return sorted(list(dict.fromkeys(out)))
    if isinstance(value, str):
        return _coerce_dates([x for x in value.split(",") if x.strip()])
    return []

def _safe_oid(id_str: Any) -> Optional[ObjectId]:
    try:
        return ObjectId(str(id_str))
    except Exception:
        return None


# ---------- Routes ----------

@employees_bp.route("", methods=["POST"])
def create_employee():
    db = current_app.config.get("DB")
    if db is None:
        return jsonify({"ok": False, "error": "DB not connected"}), 500

    body = request.get_json(force=True, silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"ok": False, "error": "name is required"}), 400

    role = (body.get("role") or "").strip() or None
    skills = _coerce_skills(body.get("skills"))
    experience = body.get("experience") or []
    projects = body.get("projects") or []
    availability = (body.get("availability") or "").strip() or None
    availability_dates = _coerce_dates(body.get("availability_dates"))
    cv_url = (body.get("cv_url") or "").strip() or None
    portfolio_url = (body.get("portfolio_url") or "").strip() or None
    cv_file_id = body.get("cv_file_id")
    if isinstance(cv_file_id, str):
        cv_file_id = _safe_oid(cv_file_id) or cv_file_id

    doc = {
        "name": name,
        "role": role,
        "skills": skills,
        "experience": experience,
        "projects": projects,
        "availability": availability,
        "availability_dates": availability_dates,
        "cv_url": cv_url,
        "portfolio_url": portfolio_url,
        "cv_file_id": cv_file_id,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    res = db.employees.insert_one(doc)
    doc["_id"] = res.inserted_id
    return jsonify({"ok": True, "employee": _public(doc)}), 201


@employees_bp.route("", methods=["GET"])
def list_employees():
    db = current_app.config.get("DB")
    if db is None:
        return jsonify({"ok": False, "error": "DB not connected"}), 500

    role = request.args.get("role")
    role_like = request.args.get("role_like")
    skill = request.args.get("skill")
    skills_csv = request.args.get("skills")
    q = request.args.get("q")
    page = int(request.args.get("page", "1") or "1")
    limit = int(request.args.get("limit", "10") or "10")
    sort = (request.args.get("sort") or "").strip()

    query: Dict[str, Any] = {}

    if q:
        query["name"] = {"$regex": q, "$options": "i"}

    if role_like:
        query["role"] = {"$regex": role_like, "$options": "i"}
    elif role:
        query["role"] = role

    if skills_csv:
        skill_list = [s.strip() for s in skills_csv.split(",") if s.strip()]
        if skill_list:
            query["skills"] = {"$in": skill_list}
    elif skill:
        query["skills"] = skill

    sort_spec = None
    if sort:
        direction = -1 if sort.startswith("-") else 1
        field = sort[1:] if sort.startswith("-") else sort
        sort_spec = [(field, direction)]

    cur = db.employees.find(query)
    if sort_spec:
        cur = cur.sort(sort_spec)

    total = db.employees.count_documents(query)
    cur = cur.skip(max(page - 1, 0) * max(limit, 1)).limit(max(limit, 1))
    data = [_public(x) for x in cur]

    return jsonify({
        "ok": True,
        "data": data,
        "pagination": {"page": page, "limit": limit, "total": total},
        "query": query
    })


@employees_bp.route("/<id>", methods=["GET"])
def get_employee(id):
    db = current_app.config.get("DB")
    if db is None:
        return jsonify({"ok": False, "error": "DB not connected"}), 500
    oid = _safe_oid(id)
    if not oid:
        return jsonify({"ok": False, "error": "Invalid id"}), 400
    doc = db.employees.find_one({"_id": oid})
    if not doc:
        return jsonify({"ok": False, "error": "Not found"}), 404
    return jsonify({"ok": True, "employee": _public(doc)}), 200


@employees_bp.route("/<id>", methods=["PUT", "PATCH"])
def update_employee(id):
    db = current_app.config.get("DB")
    if db is None:
        return jsonify({"ok": False, "error": "DB not connected"}), 500
    oid = _safe_oid(id)
    if not oid:
        return jsonify({"ok": False, "error": "Invalid id"}), 400

    body = request.get_json(force=True, silent=True) or {}
    body.pop("_id", None)

    # normalize fields when present
    if "skills" in body:
        body["skills"] = _coerce_skills(body.get("skills"))
    if "availability_dates" in body:
        body["availability_dates"] = _coerce_dates(body.get("availability_dates"))
    if "cv_file_id" in body and isinstance(body["cv_file_id"], str):
        body["cv_file_id"] = _safe_oid(body["cv_file_id"]) or body["cv_file_id"]

    body["updated_at"] = datetime.utcnow()
    db.employees.update_one({"_id": oid}, {"$set": body})
    doc = db.employees.find_one({"_id": oid})
    if not doc:
        return jsonify({"ok": False, "error": "Not found after update"}), 404
    return jsonify({"ok": True, "employee": _public(doc)}), 200


@employees_bp.route("/<id>", methods=["DELETE"])
def delete_employee(id):
    db = current_app.config.get("DB")
    if db is None:
        return jsonify({"ok": False, "error": "DB not connected"}), 500
    oid = _safe_oid(id)
    if not oid:
        return jsonify({"ok": False, "error": "Invalid id"}), 400
    res = db.employees.delete_one({"_id": oid})
    if res.deleted_count == 0:
        return jsonify({"ok": False, "error": "Not found"}), 404
    return jsonify({"ok": True, "deleted": id}), 200
