from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
from services.match import score_candidates, gemini_rerank

match_bp = Blueprint("match", __name__)

def _project_public(doc):
    return {
        "id": str(doc["_id"]),
        "project_name": doc.get("project_name"),
        "required_skills": doc.get("required_skills", []),
        "duration": doc.get("duration"),
        "timeline": doc.get("timeline", {}),
        "priority": doc.get("priority", "Medium"),
        "headcount": doc.get("headcount", 1),
        "status": doc.get("status", "Open"),
    }

def _cand_public(doc):
    d = {k: doc.get(k) for k in ["id","name","role","skills","availability","cv_file_id","ai_reason"]}
    d["score"] = doc.get("score")
    return d

@match_bp.route("", methods=["GET"])
def match_for_project():
    db = current_app.config["DB"]
    project_id = request.args.get("project_id")
    top_n = int(request.args.get("limit", "5"))
    use_ai = request.args.get("use_ai", "false").lower() in ("1","true","yes")

    proj = db.projects.find_one({"_id": ObjectId(project_id)})
    if not proj:
        return jsonify({"ok": False, "error": "project not found"}), 404

    ranked = score_candidates(db, proj)
    ranked.sort(key=lambda x: x["_base_score"], reverse=True)

    if use_ai:
        ranked = gemini_rerank(proj, ranked, top_k=min(15, len(ranked)))

    top = ranked[:top_n]
    if top:
        max_s = max(x["_base_score"] for x in top) or 1e-9
        for x in top:
            x["score"] = round((x["_base_score"] / max_s) * 100.0, 1)

    return jsonify({
        "ok": True,
        "project": _project_public(proj),
        "candidates": [_cand_public(x) for x in top]
    })
