from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
from datetime import datetime

hr_allocation_bp = Blueprint("hr_allocation", __name__)

def _public(doc):
    return {
        "id": str(doc["_id"]),
        "employee_id": str(doc.get("employee_id")),
        "employee_name": doc.get("employee_name"),
        "project_id": str(doc.get("project_id")),
        "project_name": doc.get("project_name"),
        "allocated_on": doc.get("allocated_on"),
        "status": doc.get("status", "Active"),
    }

@hr_allocation_bp.route("", methods=["GET"])
def list_allocations():
    db = current_app.config["DB"]
    cur = db.hr_allocations.find({}).sort("allocated_on", -1)
    return jsonify({"ok": True, "data": [_public(x) for x in cur]})

@hr_allocation_bp.route("", methods=["POST"])
def create_allocation():
    db = current_app.config["DB"]
    body = request.get_json(force=True)

    emp_id = body.get("employee_id")
    proj_id = body.get("project_id")

    emp = db.employees.find_one({"_id": ObjectId(emp_id)}) if emp_id else None
    proj = db.projects.find_one({"_id": ObjectId(proj_id)}) if proj_id else None

    if not emp or not proj:
        return jsonify({"ok": False, "error": "Invalid employee or project"}), 400

    doc = {
        "employee_id": emp_id,
        "employee_name": emp.get("name"),
        "project_id": proj_id,
        "project_name": proj.get("project_name"),
        "allocated_on": datetime.utcnow(),
        "status": "Active",
    }

    db.hr_allocations.insert_one(doc)
    return jsonify({"ok": True, "allocation": _public(doc)}), 201

@hr_allocation_bp.route("/<id>", methods=["DELETE"])
def delete_allocation(id):
    db = current_app.config["DB"]
    db.hr_allocations.delete_one({"_id": ObjectId(id)})
    return jsonify({"ok": True, "message": "Allocation deleted"})
