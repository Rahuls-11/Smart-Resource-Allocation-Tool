from typing import Any, Dict, List
from datetime import datetime
from math import exp
from config import Config

# ------------------ Helpers ------------------

def _skill_overlap_list(req: List[str], have: List[str]) -> List[str]:
    rs = {s.strip().lower() for s in req or [] if s}
    hs = {s.strip().lower() for s in have or [] if s}
    inter = rs & hs
    have_map = {s.strip().lower(): s for s in have or []}
    return [have_map.get(k, k) for k in inter]

def _soonest_date_score(iso_dates: List[str]) -> float:
    if not iso_dates:
        return 0.0
    today = datetime.utcnow().date()
    best = 0.0
    for s in iso_dates:
        try:
            y, m, d = map(int, s.split("-"))
            dt = datetime(y, m, d).date()
            delta = (dt - today).days
            best = max(best, exp(-abs(delta) / 7.0))
        except Exception:
            continue
    return best

def _previous_exp_bonus(prev: List[Dict[str, Any]]) -> float:
    if not prev:
        return 0.0
    score = 0.0
    for it in prev:
        if it.get("company") or it.get("title"):
            score += 0.5
    return min(score, 2.0)

# ------------------ Core Scoring ------------------

def score_candidates(db, project: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Compute match % heavily weighted toward skill + project experience."""
    req = project.get("required_skills", []) or []
    ranked: List[Dict[str, Any]] = []

    for emp in db.employees.find({}):
        skills = emp.get("skills", [])
        projects_by_skill = emp.get("projects_by_skill", {}) or {}
        projects_flat = emp.get("projects", []) or []
        availability_dates = emp.get("availability_dates", []) or []
        prev = emp.get("previous_experience", []) or []

        matched_skills = _skill_overlap_list(req, skills)
        s_overlap = len(matched_skills)

        # Experience in those specific skills
        proj_hits = 0
        for r in req:
            rlow = (r or "").strip().lower()
            if rlow in (k.strip().lower() for k in projects_by_skill.keys()):
                proj_hits += len(projects_by_skill.get(r, []) or [])
        if proj_hits == 0 and projects_flat:
            for p in projects_flat:
                for r in req:
                    if r and r.lower() in str(p).lower():
                        proj_hits += 1

        prev_bonus = _previous_exp_bonus(prev)
        avail_bonus = _soonest_date_score(availability_dates)

        # Heavier weights for skills & project experience
        base = (4.0 * s_overlap) + (3.0 * proj_hits) + (1.0 * prev_bonus) + (1.0 * avail_bonus)

        emp["_base_score"] = float(base)
        emp["matched_skills"] = matched_skills
        ranked.append(emp)

    return ranked

# ------------------ Gemini / AI Re-rank ------------------

def gemini_rerank(project: Dict[str, Any], candidates: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Use Gemini (or fallback) to create a single-sentence AI reason.
    Example: "This employee has React and Django skills, has done projects in these areas, and is available soon."
    """
    if Config.SKIP_GEMINI or not Config.GEMINI_API_KEY:
        for c in candidates[:top_k]:
            matched = ", ".join(c.get("matched_skills", []))
            availability = ", ".join(c.get("availability_dates", [])) or c.get("availability", "soon")
            reason = (
                f"This employee has {matched or 'relevant'} skills, "
                f"has done projects in these areas, and is available {availability}. "
                f"Hence the match score is based on strong alignment."
            )
            c["ai_reason"] = reason
        return candidates

    # ----- Gemini path -----
    try:
        import google.generativeai as genai
        import json

        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel(Config.GEMINI_MODEL)

        payload = {
            "project": {
                "name": project.get("project_name"),
                "required_skills": project.get("required_skills", []),
            },
            "candidates": [
                {
                    "id": str(c.get("_id") or c.get("id")),
                    "name": c.get("name"),
                    "role": c.get("role"),
                    "matched_skills": c.get("matched_skills", []),
                    "projects_by_skill": c.get("projects_by_skill", {}),
                    "projects": c.get("projects", []),
                    "previous_experience": c.get("previous_experience", []),
                    "availability": c.get("availability"),
                    "availability_dates": c.get("availability_dates", []),
                    "_base_score": c.get("_base_score", 0),
                }
                for c in candidates[:top_k]
            ],
        }

        prompt = (
            "You are a technical recruiter AI. Analyze each candidate for the given project.\n"
            "Focus mainly on skills and whether they have built projects using those skills.\n"
            "Also lightly consider availability.\n"
            "Return STRICT JSON with this structure:\n"
            "{ \"results\": [ {\"id\": string, \"rerank_score\": float (0-1), \"reason\": string} ] }\n"
            "Each reason must be ONE SENTENCE (<= 180 chars) like:\n"
            "\"This employee has React and Django skills, has done projects in these areas, and is available soon.\"\n"
            "---\n"
            f"{payload}"
        )

        out = model.generate_content(prompt)
        raw = (out.text or "").strip()
        data = json.loads(raw)
        results = {str(x["id"]): x for x in data.get("results", []) if "id" in x}

        for c in candidates[:top_k]:
            cid = str(c.get("_id") or c.get("id"))
            r = results.get(cid)
            if r:
                c["ai_reason"] = r.get("reason") or c.get("ai_reason")
                rs = float(r.get("rerank_score") or 0)
                c["_base_score"] = float(c.get("_base_score") or 0) * (0.8 + 0.4 * rs)

        return candidates
    except Exception:
        # fallback to heuristic
        for c in candidates[:top_k]:
            matched = ", ".join(c.get("matched_skills", []))
            availability = ", ".join(c.get("availability_dates", [])) or c.get("availability", "soon")
            reason = (
                f"This employee has {matched or 'relevant'} skills, "
                f"has done projects in these areas, and is available {availability}. "
                f"Hence the match score is based on strong alignment."
            )
            c["ai_reason"] = reason
        return candidates
