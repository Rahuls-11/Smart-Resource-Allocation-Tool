import { useEffect, useMemo, useRef, useState } from "react";
import {api} from "../api/client";
import { DayPicker } from "react-day-picker";
import "react-day-picker/dist/style.css";

type ExperienceItem = {
  title?: string;       // e.g., "Software Engineer @ ACME"
  duration?: string;    // e.g., "Jan 2023 - Oct 2024"
  tech?: string[];      // e.g., ["React", "Node"]
};

type Employee = {
  id: string;
  name: string;
  role?: string;
  skills: string[];
  projects?: string[];          // "Experience in working in that skill (Project Name)"
  experience?: ExperienceItem[]; // "Previous Experience (Company/Title)"
  availability?: string;
  availability_dates?: string[]; // array of "YYYY-MM-DD"
  portfolio_url?: string;
  cv_file_id?: string | null;    // presence -> "Resume Uploaded" badge
};

function toYMD(d: Date) {
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

export default function Employees() {
  const [list, setList] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(false);

  // filters (server-side)
  const [q, setQ] = useState("");
  const [role, setRole] = useState("");
  const [skill, setSkill] = useState("");

  // create panel visibility
  const [showForm, setShowForm] = useState(false);

  // create refs
  const nameRef = useRef<HTMLInputElement>(null);
  const roleRef = useRef<HTMLInputElement>(null);
  const skillsRef = useRef<HTMLInputElement>(null);
  const availRef = useRef<HTMLInputElement>(null);
  const portfolioRef = useRef<HTMLInputElement>(null);

  // upload (create) refs
  const fileRef = useRef<HTMLInputElement>(null);
  const skipRef = useRef<HTMLInputElement>(null);

  // editing state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editRole, setEditRole] = useState("");
  const [editSkills, setEditSkills] = useState("");
  const [editAvail, setEditAvail] = useState("");
  const [editPortfolio, setEditPortfolio] = useState("");
  const [editDates, setEditDates] = useState<Date[]>([]);
  const [editCvUploaded, setEditCvUploaded] = useState(false); // show badge immediately

  // load data
  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get("/employees", {
        params: { q, role, skill, limit: 200, sort: "-created_at" },
      });
      setList(res.data?.data ?? []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const displayed = useMemo(() => list, [list]);

  const resetCreateForm = () => {
    if (nameRef.current) nameRef.current.value = "";
    if (roleRef.current) roleRef.current.value = "";
    if (skillsRef.current) skillsRef.current.value = "";
    if (availRef.current) availRef.current.value = "";
    if (portfolioRef.current) portfolioRef.current.value = "";
    if (fileRef.current) fileRef.current.value = "";
    if (skipRef.current) skipRef.current.checked = false;
  };

  // ----------------- CRUD -----------------

  const createEmployee = async () => {
    const payload = {
      name: nameRef.current?.value?.trim() || "",
      role: roleRef.current?.value?.trim() || "",
      skills:
        skillsRef.current?.value
          ?.split(",")
          .map((s) => s.trim())
          .filter(Boolean) || [],
      availability: availRef.current?.value?.trim() || "",
      portfolio_url: portfolioRef.current?.value?.trim() || "",
      availability_dates: [] as string[],
    };
    if (!payload.name) {
      alert("Name is required.");
      return;
    }
    await api.post("/employees", payload);
    await load();
    resetCreateForm();
    setShowForm(false);
  };

  const startEdit = (e: Employee) => {
    setEditingId(e.id);
    setEditName(e.name || "");
    setEditRole(e.role || "");
    setEditSkills((e.skills || []).join(", "));
    setEditAvail(e.availability || "");
    setEditPortfolio(e.portfolio_url || "");
    setEditDates(
      (e.availability_dates || []).map((s) => {
        const [y, m, d] = s.split("-").map(Number);
        return new Date(y, (m as number) - 1, d);
      })
    );
    setEditCvUploaded(!!e.cv_file_id);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditDates([]);
    setEditCvUploaded(false);
  };

  const saveEdit = async () => {
    if (!editingId) return;
    const payload = {
      name: editName.trim(),
      role: editRole.trim() || null,
      skills: editSkills.split(",").map((s) => s.trim()).filter(Boolean),
      availability: editAvail.trim() || null,
      portfolio_url: editPortfolio.trim() || null,
      availability_dates: editDates.map(toYMD),
    };
    await api.put(`/employees/${editingId}`, payload);
    await load();
    cancelEdit();
  };

  const deleteEmployee = async (id: string) => {
    if (!confirm("Delete this employee? This cannot be undone.")) return;
    await api.delete(`/employees/${id}`);
    await load();
  };

  // ----------------- Resume Upload -----------------

  // Upload in create panel → creates new employee from extracted data if name/role provided
  const uploadResumeNew = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) {
      alert("Choose a file first.");
      return;
    }
    const name = nameRef.current?.value || "";
    const role = roleRef.current?.value || "";

    const form = new FormData();
    form.append("file", file);
    if (name) form.append("name", name);  // backend will create employee
    if (role) form.append("role", role);
    form.append("skip_ai", skipRef.current?.checked ? "1" : "0");

    const res = await api.post("/resume/upload", form); // no manual Content-Type
    if (res.data?.ok) {
      alert("Resume uploaded.");
      await load();
      resetCreateForm();
      setShowForm(false);
    } else {
      alert(res.data?.error || "Upload failed.");
    }
  };

  // Upload while editing → REPLACE parsed fields in DB for this employee
  const uploadResumeForExisting = async (empId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    form.append("employee_id", empId);
    // replacement mode is default on backend when employee_id is provided
    const res = await api.post("/resume/upload", form);
    if (res.data?.ok) {
      setEditCvUploaded(true); // immediate UI feedback
      await load();
      alert("Resume uploaded & employee data replaced.");
    } else {
      alert(res.data?.error || "Upload failed.");
    }
  };

  // ----------------- Render -----------------

  return (
    <>
      <h1 className="text-2xl font-semibold text-slate-900 mb-6">Employees</h1>

      {/* Filters + New */}
      <div className="rounded-xl bg-white border border-slate-200 p-4 mb-6">
        <div className="flex flex-wrap items-center gap-3">
          <input
            className="h-10 w-64 rounded-lg border border-slate-200 px-3 outline-none focus:ring-2 focus:ring-slate-200"
            placeholder="Search name..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <input
            className="h-10 w-44 rounded-lg border border-slate-200 px-3 outline-none focus:ring-2 focus:ring-slate-200"
            placeholder="Role"
            value={role}
            onChange={(e) => setRole(e.target.value)}
          />
          <input
            className="h-10 w-44 rounded-lg border border-slate-200 px-3 outline-none focus:ring-2 focus:ring-slate-200"
            placeholder="Skill"
            value={skill}
            onChange={(e) => setSkill(e.target.value)}
          />
          <button
            onClick={load}
            className="h-10 px-4 rounded-lg bg-slate-900 text-white font-medium"
          >
            Apply
          </button>

          <div className="ml-auto">
            <button
              onClick={() => {
                if (showForm) resetCreateForm();
                setShowForm((s) => !s);
              }}
              className="h-10 px-4 rounded-lg bg-slate-900 text-white font-semibold"
            >
              {showForm ? "Cancel" : "+ New"}
            </button>
          </div>
        </div>
      </div>

      {/* Create / Upload (hidden by default) */}
      {showForm && (
        <div className="rounded-xl bg-white border border-slate-200 p-4 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-700 mb-1">Name</label>
              <input ref={nameRef} className="w-full h-11 rounded-lg border border-slate-200 px-3" />
            </div>
            <div>
              <label className="block text-sm text-slate-700 mb-1">Role</label>
              <input ref={roleRef} className="w-full h-11 rounded-lg border border-slate-200 px-3" />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm text-slate-700 mb-1">Skills (comma-separated)</label>
              <input ref={skillsRef} className="w-full h-11 rounded-lg border border-slate-200 px-3" />
            </div>
            <div>
              <label className="block text-sm text-slate-700 mb-1">Availability (free text)</label>
              <input ref={availRef} className="w-full h-11 rounded-lg border border-slate-200 px-3" />
            </div>
            <div>
              <label className="block text-sm text-slate-700 mb-1">Portfolio URL</label>
              <input ref={portfolioRef} className="w-full h-11 rounded-lg border border-slate-200 px-3" />
            </div>
          </div>

          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button
              onClick={createEmployee}
              className="h-10 px-4 rounded-lg bg-slate-900 text-white font-semibold"
            >
              Create Employee
            </button>

            <div className="flex items-center gap-3">
              <input ref={fileRef} type="file" accept=".pdf,.doc,.docx" />
              <label className="flex items-center gap-2 text-sm text-slate-700">
                <input ref={skipRef} type="checkbox" className="h-4 w-4" /> Skip AI
              </label>
              <button
                onClick={uploadResumeNew}
                className="h-10 px-3 rounded-lg border border-slate-300 text-slate-700"
              >
                Upload Resume & Create from Extract
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Employees table */}
      <div className="rounded-xl bg-white border border-slate-200 overflow-hidden">
        <table className="w-full text-left">
          <thead>
            <tr className="text-sm text-slate-600">
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Skills</th>
              <th className="px-4 py-3">Experience in working in that skill (Project Name)</th>
              <th className="px-4 py-3">Previous Experience (Company/Title)</th>
              <th className="px-4 py-3">Available Dates</th>
              <th className="px-4 py-3 w-[300px]">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading && (
              <tr>
                <td className="px-4 py-6 text-slate-500" colSpan={6}>
                  Loading…
                </td>
              </tr>
            )}

            {!loading &&
              displayed.map((e) => {
                const isEditing = editingId === e.id;
                return (
                  <tr key={e.id} className="align-top">
                    {/* Name */}
                    <td className="px-4 py-3">
                      {!isEditing ? (
                        <div className="font-medium">{e.name}</div>
                      ) : (
                        <input
                          className="w-full h-10 rounded-lg border border-slate-200 px-3"
                          value={editName}
                          onChange={(ev) => setEditName(ev.target.value)}
                        />
                      )}
                      {/* Small line with role */}
                      <div className="text-xs text-slate-500">{isEditing ? null : (e.role || "")}</div>
                      {/* Resume badge */}
                      {(isEditing ? editCvUploaded : !!e.cv_file_id) && (
                        <div className="mt-1 inline-flex items-center rounded-md bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700 border border-emerald-200">
                          Resume Uploaded
                        </div>
                      )}
                    </td>

                    {/* Skills */}
                    <td className="px-4 py-3">
                      {!isEditing ? (
                        <div className="flex flex-wrap gap-1">
                          {(e.skills || []).map((s) => (
                            <span key={s} className="inline-flex rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-700">
                              {s}
                            </span>
                          ))}
                          {(e.skills || []).length === 0 && <span className="text-slate-500">-</span>}
                        </div>
                      ) : (
                        <input
                          className="w-full h-10 rounded-lg border border-slate-200 px-3"
                          value={editSkills}
                          onChange={(ev) => setEditSkills(ev.target.value)}
                          placeholder="comma-separated"
                        />
                      )}
                    </td>

                    {/* Projects (Experience in skill) */}
                    <td className="px-4 py-3">
                      {!isEditing ? (
                        <div className="flex flex-wrap gap-1">
                          {(e.projects || []).map((p) => (
                            <span key={p} className="inline-flex rounded bg-indigo-50 px-2 py-0.5 text-xs text-indigo-700 border border-indigo-200">
                              {p}
                            </span>
                          ))}
                          {(e.projects || []).length === 0 && <span className="text-slate-500">-</span>}
                        </div>
                      ) : (
                        <div className="text-xs text-slate-500">
                          Projects are replaced when you upload a new resume during edit.
                        </div>
                      )}
                    </td>

                    {/* Previous Experience (Company/Title) */}
                    <td className="px-4 py-3">
                      {!isEditing ? (
                        <ul className="list-disc list-inside text-[13px] text-slate-700 space-y-1">
                          {(e.experience || []).slice(0, 4).map((x, idx) => (
                            <li key={idx}>
                              {x.title || "—"}
                              {x.duration ? ` • ${x.duration}` : ""}
                            </li>
                          ))}
                          {(e.experience || []).length === 0 && <span className="text-slate-500">-</span>}
                        </ul>
                      ) : (
                        <div className="text-xs text-slate-500">
                          Experience list is replaced when you upload a new resume during edit.
                        </div>
                      )}
                    </td>

                    {/* Availability Dates */}
                    <td className="px-4 py-3">
                      {!isEditing ? (
                        <div className="flex flex-wrap gap-1">
                          {(e.availability_dates || []).map((d) => (
                            <span
                              key={d}
                              className="inline-flex items-center rounded-md bg-slate-100 px-2 py-0.5 text-xs text-slate-700"
                            >
                              {d}
                            </span>
                          ))}
                          {(e.availability_dates || []).length === 0 && <span className="text-slate-500">-</span>}
                        </div>
                      ) : (
                        <div className="bg-white rounded-lg border border-slate-200 p-2">
                          <DayPicker
                            mode="multiple"
                            selected={editDates}
                            onSelect={(dates) => setEditDates(dates || [])}
                          />
                          <div className="text-xs text-slate-500 mt-1">
                            Selected: {editDates.map(toYMD).join(", ") || "None"}
                          </div>
                        </div>
                      )}
                    </td>

                    {/* Actions */}
                    <td className="px-4 py-3">
                      {!isEditing ? (
                        <div className="flex flex-wrap items-center gap-2">
                          <button
                            onClick={() => startEdit(e)}
                            className="h-9 px-3 rounded-lg border border-slate-300"
                          >
                            Edit
                          </button>

                          {/* Quick resume badge */}
                          {!!e.cv_file_id && (
                            <span className="inline-flex items-center rounded-md bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700 border border-emerald-200">
                              Resume Uploaded
                            </span>
                          )}

                          <button
                            onClick={() => deleteEmployee(e.id)}
                            className="h-9 px-3 rounded-lg border border-rose-300 text-rose-700"
                          >
                            Delete
                          </button>
                        </div>
                      ) : (
                        <div className="flex flex-col gap-2">
                          {/* Inline editable simple fields */}
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-slate-600">Role:</span>
                            <input
                              className="h-9 rounded-lg border border-slate-200 px-3"
                              value={editRole}
                              onChange={(ev) => setEditRole(ev.target.value)}
                            />
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-slate-600">Availability:</span>
                            <input
                              className="h-9 rounded-lg border border-slate-200 px-3"
                              value={editAvail}
                              onChange={(ev) => setEditAvail(ev.target.value)}
                            />
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-slate-600">Portfolio URL:</span>
                            <input
                              className="h-9 w-full rounded-lg border border-slate-200 px-3"
                              value={editPortfolio}
                              onChange={(ev) => setEditPortfolio(ev.target.value)}
                            />
                          </div>

                          {/* Upload resume to REPLACE parsed fields */}
                          <label className="h-9 px-3 rounded-lg border border-slate-300 cursor-pointer inline-flex items-center w-fit">
                            <input
                              type="file"
                              className="hidden"
                              accept=".pdf,.doc,.docx"
                              onChange={async (ev) => {
                                const f = ev.target.files?.[0];
                                if (f && editingId) {
                                  await uploadResumeForExisting(editingId, f);
                                }
                                ev.currentTarget.value = "";
                              }}
                            />
                            Upload Resume (Replace data)
                          </label>

                          <div className="flex items-center gap-2">
                            <button
                              onClick={saveEdit}
                              className="h-9 px-3 rounded-lg bg-slate-900 text-white"
                            >
                              Save
                            </button>
                            <button
                              onClick={cancelEdit}
                              className="h-9 px-3 rounded-lg border border-slate-300"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}

            {!loading && displayed.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-slate-500">
                  No data.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
