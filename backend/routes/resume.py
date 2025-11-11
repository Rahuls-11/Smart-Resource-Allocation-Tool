from flask import Blueprint, request, jsonify, current_app
from gridfs import GridFS
from datetime import datetime
from utils.pdf import extract_text_from_pdf_bytes
from config import Config
from bson import ObjectId
import json, traceback

resume_bp = Blueprint("resume", __name__)

def _safe_oid(s):
    try:
        return ObjectId(str(s))
    except Exception:
        return None

def _heuristic_parse(text: str):
    # very light fallback: collect tech keywords + naive projects from headers/bullets
    skills = []
    projects = []
    experience = []

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for l in lines:
        low = l.lower()

        # skills: keywords
        if any(k in low for k in ["react","next","node","python","java","mongodb","flask","django","aws","gcp","azure","docker","kubernetes","typescript"]):
            for w in l.replace(",", " ").split():
                wclean = w.strip().strip("•-").strip()
                if wclean and 1 < len(wclean) < 30:
                    skills.append(wclean)

        # projects: naive capture of lines starting with "project" or bullets with colon
        if low.startswith("project") or "project:" in low:
            projects.append(l.replace("•","").replace("-","").strip())

        # experience: capture lines that look like job titles with a company
        if "@" in l or " at " in low:
            experience.append({"title": l, "duration": None, "tech": []})

    skills = list(dict.fromkeys(skills))[:50]
    projects = list(dict.fromkeys(projects))[:20]

    return {
        "skills": skills,
        "projects": projects,
        "experience": experience[:20],
        "availability": None,
        "role": None
    }

def _call_gemini_extract(text: str):
    if not getattr(Config, "GEMINI_API_KEY", None) or getattr(Config, "SKIP_GEMINI", False):
        return None
    import google.generativeai as genai
    genai.configure(api_key=Config.GEMINI_API_KEY)
    model = genai.GenerativeModel(getattr(Config, "GEMINI_MODEL", "gemini-1.5-pro"))
    prompt = f"""
You are a resume parser. Extract STRICT JSON with keys:
skills: string[]
projects: string[]
experience: [{{title:string, duration:string, tech:string[]}}]
availability: string|null
role: string|null
Return ONLY JSON. No prose.
---
{text}
"""
    try:
        out = model.generate_content(prompt)
        raw = (out.text or "").strip()
        return json.loads(raw)
    except Exception:
        return None

@resume_bp.route("/upload", methods=["POST"])
def upload_resume():
    try:
        db = current_app.config.get("DB")
        if db is None:
            return jsonify({"ok": False, "error": "DB not connected"}), 500

        # Accept 'file' or 'resume'
        file = request.files.get("file") or request.files.get("resume")
        if not file:
            return jsonify({"ok": False, "error": "No file. Expect field 'file' (or 'resume')."}), 400

        filename = file.filename or "resume.bin"
        mimetype = file.mimetype or "application/octet-stream"

        # Save to GridFS
        fs = GridFS(db)
        fid = fs.put(file.stream, filename=filename, contentType=mimetype, uploadDate=datetime.utcnow())

        # Read for parsing
        data = fs.get(fid).read()
        text = ""
        if filename.lower().endswith(".pdf") or mimetype == "application/pdf":
            try:
                text = extract_text_from_pdf_bytes(data) or ""
            except Exception as ex:
                current_app.logger.warning(f"PDF extract failed: {ex}")
                text = ""

        # Extract with Gemini (optional) then fallback
        extracted = _call_gemini_extract(text) or _heuristic_parse(text)

        # Modes:
        # 1) employee_id present -> REPLACE parsed fields + set cv_file_id
        # 2) name present (no employee_id) -> CREATE employee with extracted data
        # 3) else -> just return extracted + file_id

        employee_id = request.form.get("employee_id") or request.args.get("employee_id")
        name = (request.form.get("name") or "").strip()
        role = (request.form.get("role") or "").strip()

        merged_employee = None

        if employee_id:
            oid = _safe_oid(employee_id)
            if not oid:
                return jsonify({"ok": False, "error": "Invalid employee_id"}), 400
            doc = db.employees.find_one({"_id": oid})
            if not doc:
                return jsonify({"ok": False, "error": "employee_id not found"}), 404

            # REPLACE behavior for parsed fields
            update = {
                "skills": extracted.get("skills") or [],
                "projects": extracted.get("projects") or [],
                "experience": extracted.get("experience") or [],
                "cv_file_id": fid,
                "updated_at": datetime.utcnow(),
            }
            # Optionally update role from extracted if sent role empty and extracted has role
            if not doc.get("role") and (extracted.get("role") or role):
                update["role"] = extracted.get("role") or (role or None)

            db.employees.update_one({"_id": oid}, {"$set": update})
            merged_employee = db.employees.find_one({"_id": oid})

        elif name:
            # Create from extracted
            doc = {
                "name": name,
                "role": (role or extracted.get("role")) or None,
                "skills": extracted.get("skills") or [],
                "projects": extracted.get("projects") or [],
                "experience": extracted.get("experience") or [],
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
            merged_employee = doc

        # Response
        out = {
          "ok": True,
          "file_id": str(fid),
          "filename": filename,
          "mimetype": mimetype,
          "extracted": extracted,
          "employee": None if merged_employee is None else {
            "id": str(merged_employee["_id"]),
            "name": merged_employee.get("name"),
            "role": merged_employee.get("role"),
            "skills": merged_employee.get("skills", []),
            "projects": merged_employee.get("projects", []),
            "experience": merged_employee.get("experience", []),
            "availability": merged_employee.get("availability"),
            "availability_dates": merged_employee.get("availability_dates", []),
            "cv_file_id": str(merged_employee.get("cv_file_id")) if merged_employee.get("cv_file_id") else None,
          }
        }
        return jsonify(out), 201

    except Exception as e:
        current_app.logger.error("Resume upload error: %s\n%s", e, traceback.format_exc())
        return jsonify({"ok": False, "error": str(e)}), 500
