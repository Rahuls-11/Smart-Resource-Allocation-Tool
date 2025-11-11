from typing import List, Dict, Any
from datetime import datetime
from config import Config
import json

def score_candidates(db, project: Dict[str, Any]) -> List[Dict[str, Any]]:
    req = set((s or "").lower() for s in project.get("required_skills", []))
    out: List[Dict[str, Any]] = []

    for emp in db.employees.find({}):
        skills = set((s or "").lower() for s in emp.get("skills", []))
        overlap = len(req & skills) / (len(req) or 1)

        role_match = 1.0 if emp.get("role") else 0.1
        availability = 0.5 if emp.get("availability") else 0.0
        freshness = 1.0 if emp.get("updated_at") else 0.5

        base = 0.6*overlap + 0.2*role_match + 0.1*availability + 0.1*freshness

        out.append({
            "id": str(emp["_id"]),
            "name": emp.get("name"),
            "role": emp.get("role"),
            "skills": list(skills),
            "availability": emp.get("availability"),
            "cv_file_id": str(emp.get("cv_file_id")) if emp.get("cv_file_id") else None,
            "_base_score": round(float(base), 4),
        })
    return out

def _format_for_ai(project: Dict[str, Any], ranked: List[Dict[str, Any]]):
    p = {
        "project_name": project.get("project_name"),
        "required_skills": project.get("required_skills", []),
        "timeline": project.get("timeline", {})
    }
    cs = [{"name": c["name"], "role": c["role"], "skills": c["skills"], "availability": c.get("availability")} for c in ranked]
    return json.dumps({"project": p, "candidates": cs}, ensure_ascii=False)

def gemini_rerank(project: Dict[str, Any], ranked: List[Dict[str, Any]], top_k: int = 15) -> List[Dict[str, Any]]:
    if Config.SKIP_GEMINI or not Config.GEMINI_API_KEY:
        return ranked
    import google.generativeai as genai
    genai.configure(api_key=Config.GEMINI_API_KEY)
    model = genai.GenerativeModel(Config.GEMINI_MODEL)
    bundle = _format_for_ai(project, ranked[:top_k])
    prompt = f"""Re-rank candidates for this project. Return STRICT JSON:
{{"order":[0-based indices], "reasons":["short reason per candidate in the same order"]}}
{bundle}"""
    try:
        out = model.generate_content(prompt)
        resp = json.loads(out.text.strip())
        order = resp.get("order", list(range(min(top_k, len(ranked)))))
        reasons = resp.get("reasons", [])
        reordered = [dict(ranked[i]) for i in order] + ranked[top_k:]
        for i, r in enumerate(reordered[:len(reasons)]):
            r["ai_reason"] = reasons[i]
        return reordered
    except Exception:
        return ranked
