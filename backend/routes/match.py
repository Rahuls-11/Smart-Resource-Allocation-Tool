from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
from services.match import score_candidates, gemini_rerank

match_bp = Blueprint("match", __name__)

def _project_public(doc):
    return {
        "id": str(doc["_id"]),
        "project_name": doc.get("project_name"),
        "required_skills": doc.get("required_skills", []),
        "description": doc.get("description"),
        "priority": doc.get("priority", "Medium"),
        "status": doc.get("status", "Open"),
        "start_date": doc.get("start_date"),
        "end_date": doc.get("end_date"),
        "duration": doc.get("duration"),
        "headcount": doc.get("headcount", 1),
    }

def _cand_public(doc):
    return {
        "id": str(doc.get("_id") or doc.get("id") or ""),
        "name": doc.get("name"),
        "role": doc.get("role"),
        # only expose matched skills (not all)
        "matched_skills": doc.get("matched_skills", []),
        # availability
        "availability": doc.get("availability"),
        "availability_dates": doc.get("availability_dates", []),
        # scores & reason
        "score": doc.get("score"),
        "ai_reason": doc.get("ai_reason"),
    }

@match_bp.route("", methods=["GET"])
def match_for_project():
    db = current_app.config.get("DB")
    if db is None:
        return jsonify({"ok": False, "error": "DB not connected"}), 500

    project_id = request.args.get("project_id")
    if not project_id:
        return jsonify({"ok": False, "error": "project_id is required"}), 400

    try:
        proj = db.projects.find_one({"_id": ObjectId(project_id)})
    except Exception:
        proj = None
    if not proj:
        return jsonify({"ok": False, "error": "project not found"}), 404

    top_n = int(request.args.get("limit", "5"))
    use_ai = request.args.get("use_ai", "false").lower() in ("1", "true", "yes")

    ranked = score_candidates(db, proj)
    ranked.sort(key=lambda x: x.get("_base_score", 0), reverse=True)

    if use_ai and len(ranked) > 1:
        ranked = gemini_rerank(proj, ranked, top_k=min(15, len(ranked)))

    top = ranked[:top_n]
    if top:
        max_s = max((x.get("_base_score") or 0) for x in top) or 1e-9
        for x in top:
            x["score"] = round((float(x.get("_base_score") or 0) / max_s) * 100.0, 2)

    return jsonify({
        "ok": True,
        "project": _project_public(proj),
        "candidates": [_cand_public(x) for x in top],
    }), 200
