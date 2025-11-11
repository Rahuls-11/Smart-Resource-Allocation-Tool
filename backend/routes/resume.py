from flask import Blueprint, request, jsonify, current_app
from gridfs import GridFS
from datetime import datetime
from utils.pdf import extract_text_from_pdf_bytes
from config import Config
from bson import ObjectId
import json, re, traceback

resume_bp = Blueprint("resume", __name__)

# ========================= Helpers =========================

def _safe_oid(s):
    try:
        return ObjectId(str(s))
    except Exception:
        return None

def _json_from_text(txt: str):
    """
    Extract first JSON object from a text response if the model adds prose.
    """
    if not txt:
        return None
    # Find the first {...} block
    m = re.search(r"\{[\s\S]*\}", txt)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None

def _normalize_extracted(raw: dict):
    """
    Coerce Gemini (or heuristic) output into our canonical shape:
      skills: list[str]
      projects_by_skill: dict[str, list[str]]
      previous_experience: list[{company, title, duration}]
      role: str|None
      availability: str|None

    Also produce a flattened:
      projects: list[str]   # e.g., ["Django — Online Exam Portal", ...]
    """
    skills = []
    pbs = {}    # projects_by_skill
    prev = []   # previous_experience
    role = None
    availability = None

    if not isinstance(raw, dict):
        raw = {}

    # skills
    if isinstance(raw.get("skills"), list):
        skills = [str(s).strip() for s in raw["skills"] if str(s).strip()]

    # projects_by_skill
    if isinstance(raw.get("projects_by_skill"), dict):
        for k, v in raw["projects_by_skill"].items():
            key = str(k).strip()
            if not key:
                continue
            vals = []
            if isinstance(v, list):
                vals = [str(x).strip() for x in v if str(x).strip()]
            elif isinstance(v, str) and v.strip():
                vals = [v.strip()]
            if vals:
                pbs[key] = vals

    # fallback: some models return only projects[] -> try to infer with skills
    if not pbs and isinstance(raw.get("projects"), list) and skills:
        # naive bucket: if project line contains skill word
        pbs = {s: [] for s in skills}
        for proj in raw["projects"]:
            p = str(proj).strip()
            if not p:
                continue
            matched = False
            low = p.lower()
            for s in skills:
                if s and s.lower() in low:
                    pbs[s].append(p)
                    matched = True
            if not matched:
                # dump to a generic bucket
                pbs.setdefault("Projects", []).append(p)

    # previous_experience
    if isinstance(raw.get("previous_experience"), list):
        for item in raw["previous_experience"]:
            if not isinstance(item, dict):
                continue
            company = str(item.get("company") or "").strip()
            title = str(item.get("title") or "").strip()
            duration = str(item.get("duration") or "").strip() or None
            if company or title:
                prev.append({"company": company or None, "title": title or None, "duration": duration})
    # legacy "experience"
    elif isinstance(raw.get("experience"), list) and not prev:
        for item in raw["experience"]:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            duration = str(item.get("duration") or "").strip() or None
            if title:
                prev.append({"company": None, "title": title, "duration": duration})

    role = (raw.get("role") or None) if isinstance(raw.get("role"), str) else None
    availability = (raw.get("availability") or None) if isinstance(raw.get("availability"), str) else None

    # flattened projects array for existing UI compatibility
    projects_flat = []
    if pbs:
        for skill, plist in pbs.items():
            for proj in plist:
                projects_flat.append(f"{skill} — {proj}")
    elif isinstance(raw.get("projects"), list):
        projects_flat = [str(x).strip() for x in raw["projects"] if str(x).strip()]

    # compact unique
    def uniq(seq):
        out = []
        seen = set()
        for x in seq:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    skills = uniq(skills)[:50]
    projects_flat = uniq(projects_flat)[:50]
    # normalize pbs empties
    pbs = {k: uniq(v)[:20] for k, v in pbs.items() if v}

    return {
        "skills": skills,
        "projects_by_skill": pbs,
        "projects": projects_flat,
        "previous_experience": prev[:20],
        "role": role,
        "availability": availability,
    }

def _heuristic_parse(text: str):
    """
    Very light fallback if Gemini fails completely.
    """
    skills, projects, prev = [], [], []
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for l in lines:
        low = l.lower()
        if any(k in low for k in ["react","next","node","python","java","mongodb","flask","django","aws","gcp","azure","docker","kubernetes","typescript"]):
            for w in l.replace(",", " ").split():
                wclean = w.strip("•- ").strip()
                if wclean and 1 < len(wclean) < 30:
                    skills.append(wclean)
        if low.startswith("project") or "project:" in low:
            projects.append(re.sub(r"^(project\s*:?\s*)", "", l, flags=re.I).strip())
        if any(x in low for x in ["company", "experience", "worked at", "at "]):
            prev.append({"company": None, "title": l, "duration": None})

    skills = list(dict.fromkeys(skills))[:50]
    projects = list(dict.fromkeys(projects))[:20]
    normalized = _normalize_extracted({
        "skills": skills,
        "projects": projects,
        "previous_experience": prev,
        "role": None,
        "availability": None,
    })
    return normalized

def _call_gemini_extract(text: str):
    """
    Ask Gemini for strict JSON in a robust schema.
    """
    if not getattr(Config, "GEMINI_API_KEY", None) or getattr(Config, "SKIP_GEMINI", False):
        return None
    try:
        import google.generativeai as genai
    except Exception:
        return None

    genai.configure(api_key=Config.GEMINI_API_KEY)
    model_name = getattr(Config, "GEMINI_MODEL", "gemini-2.5-pro")
    model = genai.GenerativeModel(model_name)

    prompt = f"""
You are a senior resume parser. Return STRICT JSON only (no prose).
Schema:
{{
  "skills": string[],  // deduplicated canonical skill names (e.g., "Django", "React", "Python")
  "projects_by_skill": {{ [skill: string]: string[] }}, // project names for each skill
  "previous_experience": [{{ "company": string, "title": string, "duration": string }}], // employment history
  "role": string|null,
  "availability": string|null
}}

Guidelines:
- "projects_by_skill" should map each skill to the project names where that skill was *actually used*.
- Use concise project names only (e.g., "Online Examination Portal", "Smart Resource Allocation Tool").
- "previous_experience" should contain real company names and job titles, with brief durations if available.
- Do not invent facts. If unsure, omit entries.
- Return ONLY JSON that conforms to the schema above.

---
RESUME TEXT:
{text}
"""

    try:
        out = model.generate_content(prompt)
        raw_txt = (out.text or "").strip()
        parsed = _json_from_text(raw_txt)
        if not parsed:
            return None
        return _normalize_extracted(parsed)
    except Exception:
        return None

# ========================= Route =========================

@resume_bp.route("/upload", methods=["POST"])
def upload_resume():
    try:
        db = current_app.config.get("DB")
        if db is None:
            return jsonify({"ok": False, "error": "DB not connected"}), 500

        file = request.files.get("file") or request.files.get("resume")
        if not file:
            return jsonify({"ok": False, "error": "No file. Expect 'file' (or 'resume')."}), 400

        filename = file.filename or "resume.bin"
        mimetype = file.mimetype or "application/octet-stream"

        # Save file in GridFS
        fs = GridFS(db)
        fid = fs.put(file.stream, filename=filename, contentType=mimetype, uploadDate=datetime.utcnow())

        # Extract text (pdf only)
        data = fs.get(fid).read()
        text = ""
        if filename.lower().endswith(".pdf") or mimetype == "application/pdf":
            try:
                text = extract_text_from_pdf_bytes(data) or ""
            except Exception as ex:
                current_app.logger.warning(f"PDF extract failed: {ex}")
                text = ""

        # Prefer Gemini; fallback to heuristic
        extracted = _call_gemini_extract(text) or _heuristic_parse(text)

        employee_id = request.form.get("employee_id") or request.args.get("employee_id")
        name = (request.form.get("name") or "").strip()
        role = (request.form.get("role") or "").strip()

        if employee_id:
            oid = _safe_oid(employee_id)
            if oid is None:
                return jsonify({"ok": False, "error": "Invalid employee_id"}), 400
            doc = db.employees.find_one({"_id": oid})
            if doc is None:
                return jsonify({"ok": False, "error": "employee_id not found"}), 404

            update = {
                "skills": extracted["skills"],
                "projects_by_skill": extracted["projects_by_skill"],
                "projects": extracted["projects"],  # flattened for UI compatibility
                "previous_experience": extracted["previous_experience"],
                "cv_file_id": fid,
                "updated_at": datetime.utcnow(),
            }
            # Set role if empty
            if not doc.get("role") and (extracted.get("role") or role):
                update["role"] = extracted.get("role") or (role or None)

            db.employees.update_one({"_id": oid}, {"$set": update})
            doc = db.employees.find_one({"_id": oid})

            return jsonify({
                "ok": True,
                "file_id": str(fid),
                "employee": {
                    "id": str(doc["_id"]),
                    "name": doc.get("name"),
                    "role": doc.get("role"),
                    "skills": doc.get("skills", []),
                    "projects_by_skill": doc.get("projects_by_skill", {}),
                    "projects": doc.get("projects", []),
                    "previous_experience": doc.get("previous_experience", []),
                    "availability": doc.get("availability"),
                    "availability_dates": doc.get("availability_dates", []),
                    "cv_file_id": str(doc.get("cv_file_id")) if doc.get("cv_file_id") else None,
                }
            }), 201

        if name:
            doc = {
                "name": name,
                "role": (role or extracted.get("role")) or None,
                "skills": extracted["skills"],
                "projects_by_skill": extracted["projects_by_skill"],
                "projects": extracted["projects"],
                "previous_experience": extracted["previous_experience"],
                "availability": extracted.get("availability"),
                "availability_dates": [],
                "cv_file_id": fid,
                "cv_url": None,
                "portfolio_url": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            res = db.employees.insert_one(doc)
            doc["_id"] = res.inserted_id
            return jsonify({
                "ok": True,
                "file_id": str(fid),
                "employee": {
                    "id": str(doc["_id"]),
                    "name": doc.get("name"),
                    "role": doc.get("role"),
                    "skills": doc.get("skills", []),
                    "projects_by_skill": doc.get("projects_by_skill", {}),
                    "projects": doc.get("projects", []),
                    "previous_experience": doc.get("previous_experience", []),
                    "availability": doc.get("availability"),
                    "availability_dates": doc.get("availability_dates", []),
                    "cv_file_id": str(doc.get("cv_file_id")) if doc.get("cv_file_id") else None,
                }
            }), 201

        return jsonify({
            "ok": False,
            "error": "Missing 'employee_id' (update) or 'name' (create)."
        }), 400

    except Exception as e:
        current_app.logger.error("Resume upload error: %s\n%s", e, traceback.format_exc())
        return jsonify({"ok": False, "error": str(e)}), 500
