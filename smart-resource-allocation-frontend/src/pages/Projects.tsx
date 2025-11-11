import { useEffect, useRef, useState } from "react";
import api from "../api/client";

type Project = {
  id: string;
  project_name: string;
  required_skills: string[];
  description?: string;
  priority?: "Low" | "Medium" | "High";
  status?: "Open" | "Closed";
  start_date?: string;  // yyyy-mm-dd
  end_date?: string;    // yyyy-mm-dd
  duration?: string;
  headcount?: number;
};

export default function Projects() {
  const [list, setList] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);

  // filters (server-side on Apply)
  const [q, setQ] = useState("");
  const [skill, setSkill] = useState("");
  const [status, setStatus] = useState<"All" | "Open" | "Closed">("All");

  // show/hide create form
  const [showForm, setShowForm] = useState(false);

  // refs for create
  const nameRef = useRef<HTMLInputElement>(null);
  const skillsRef = useRef<HTMLInputElement>(null);
  const descRef = useRef<HTMLTextAreaElement>(null);
  const durRef = useRef<HTMLInputElement>(null);
  const startRef = useRef<HTMLInputElement>(null);
  const endRef = useRef<HTMLInputElement>(null);
  const headRef = useRef<HTMLInputElement>(null);
  const prioRef = useRef<HTMLSelectElement>(null);
  const statusRef = useRef<HTMLSelectElement>(null);

  // edit state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [edit, setEdit] = useState<Project | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get("/projects", {
        params: {
          q: q || undefined,
          skill: skill || undefined,
          status: status === "All" ? undefined : status,
          limit: 200,
          sort: "-created_at",
        },
      });
      setList(res.data?.data ?? []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const displayed = list;

  const resetForm = () => {
    if (nameRef.current) nameRef.current.value = "";
    if (skillsRef.current) skillsRef.current.value = "";
    if (descRef.current) descRef.current.value = "";
    if (durRef.current) durRef.current.value = "";
    if (startRef.current) startRef.current.value = "";
    if (endRef.current) endRef.current.value = "";
    if (headRef.current) headRef.current.value = "";
    if (prioRef.current) prioRef.current.value = "Medium";
    if (statusRef.current) statusRef.current.value = "Open";
  };

  // ---- Create ----
  const create = async () => {
    const payload: Partial<Project> = {
      project_name: nameRef.current?.value?.trim() || "",
      required_skills:
        skillsRef.current?.value
          ?.split(",")
          .map((s) => s.trim())
          .filter(Boolean) || [],
      description: descRef.current?.value?.trim() || "",
      duration: durRef.current?.value?.trim() || "",
      start_date: startRef.current?.value || "", // yyyy-mm-dd from <input type="date">
      end_date: endRef.current?.value || "",
      headcount: Number(headRef.current?.value || 0) || undefined,
      priority: (prioRef.current?.value as any) || "Medium",
      status: (statusRef.current?.value as any) || "Open",
    };
    if (!payload.project_name) return alert("Project name is required");

    await api.post("/projects", payload);
    await load();
    resetForm();
    setShowForm(false);
  };

  // ---- Edit / Save / Delete ----
  const startEdit = (p: Project) => {
    setEditingId(p.id);
    setEdit({ ...p });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEdit(null);
  };

  const saveEdit = async () => {
    if (!editingId || !edit) return;
    const payload: Partial<Project> = {
      project_name: edit.project_name?.trim(),
      required_skills: (edit.required_skills || []).map((s) => s.trim()).filter(Boolean),
      description: edit.description?.trim(),
      priority: edit.priority,
      status: edit.status,
      start_date: startRef.current?.value || undefined,
      end_date: endRef.current?.value || undefined,
      duration: edit.duration?.trim(),
      headcount: edit.headcount,
    };
    await api.put(`/projects/${editingId}`, payload);
    await load();
    cancelEdit();
  };

  const remove = async (id: string) => {
    if (!confirm("Delete this project?")) return;
    await api.delete(`/projects/${id}`);
    await load();
  };

  // ---- UI ----
  return (
    <>
      <h1 className="text-2xl font-semibold text-slate-900 mb-6">Projects</h1>

      {/* Filter row + New */}
      <div className="rounded-xl bg-white border border-slate-200 p-4 mb-6">
        <div className="flex flex-wrap items-center gap-3">
          <input
            className="h-10 w-64 rounded-lg border border-slate-200 px-3 outline-none focus:ring-2 focus:ring-slate-200"
            placeholder="Search name/desc..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <input
            className="h-10 w-44 rounded-lg border border-slate-200 px-3 outline-none focus:ring-2 focus:ring-slate-200"
            placeholder="Skill"
            value={skill}
            onChange={(e) => setSkill(e.target.value)}
          />
          <select
            className="h-10 w-40 rounded-lg border border-slate-200 px-3 outline-none focus:ring-2 focus:ring-slate-200"
            value={status}
            onChange={(e) => setStatus(e.target.value as any)}
          >
            <option>All</option>
            <option>Open</option>
            <option>Closed</option>
          </select>

          <button
            onClick={load}
            className="h-10 px-4 rounded-lg bg-slate-900 text-white font-medium"
          >
            Apply
          </button>

          <div className="ml-auto">
            <button
              onClick={() => {
                if (showForm) resetForm();
                setShowForm((s) => !s);
              }}
              className="h-10 px-4 rounded-lg bg-slate-900 text-white font-semibold"
            >
              {showForm ? "Cancel" : "+ New"}
            </button>
          </div>
        </div>
      </div>

      {/* Create Project (hidden by default) */}
      {showForm && (
        <div className="rounded-xl bg-white border border-slate-200 p-4 mb-6 transition-all duration-200">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-700 mb-1">Project Name</label>
              <input ref={nameRef} className="w-full h-11 rounded-lg border border-slate-200 px-3" />
            </div>
            <div>
              <label className="block text-sm text-slate-700 mb-1">Required Skills (comma-separated)</label>
              <input ref={skillsRef} className="w-full h-11 rounded-lg border border-slate-200 px-3" />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm text-slate-700 mb-1">Description</label>
              <textarea ref={descRef} className="w-full min-h-[90px] rounded-lg border border-slate-200 px-3 py-2" />
            </div>

            <div>
              <label className="block text-sm text-slate-700 mb-1">Duration</label>
              <input ref={durRef} placeholder="e.g., 8 weeks" className="w-full h-11 rounded-lg border border-slate-200 px-3" />
            </div>
            <div>
              <label className="block text-sm text-slate-700 mb-1">Start</label>
              {/* Calendar (native) */}
              <input ref={startRef} type="date" className="w-full h-11 rounded-lg border border-slate-200 px-3" />
            </div>
            <div>
              <label className="block text-sm text-slate-700 mb-1">End</label>
              <input ref={endRef} type="date" className="w-full h-11 rounded-lg border border-slate-200 px-3" />
            </div>
            <div>
              <label className="block text-sm text-slate-700 mb-1">Headcount</label>
              <input ref={headRef} type="number" className="w-full h-11 rounded-lg border border-slate-200 px-3" />
            </div>

            <div>
              <label className="block text-sm text-slate-700 mb-1">Priority</label>
              <select ref={prioRef} defaultValue="Medium" className="w-full h-11 rounded-lg border border-slate-200 px-3">
                <option>Low</option>
                <option>Medium</option>
                <option>High</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-slate-700 mb-1">Status</label>
              <select ref={statusRef} defaultValue="Open" className="w-full h-11 rounded-lg border border-slate-200 px-3">
                <option>Open</option>
                <option>Closed</option>
              </select>
            </div>
          </div>

          <div className="mt-4 flex items-center gap-3">
            <button onClick={create} className="h-10 px-4 rounded-lg bg-slate-900 text-white font-semibold">
              Create Project
            </button>
          </div>
        </div>
      )}

      {/* Projects table (always visible) */}
      <div className="rounded-xl bg-white border border-slate-200">
        <table className="w-full text-left">
          <thead>
            <tr className="text-sm text-slate-600">
              <th className="px-4 py-3">Project</th>
              <th className="px-4 py-3">Skills</th>
              <th className="px-4 py-3">Start</th>
              <th className="px-4 py-3">End</th>
              <th className="px-4 py-3">Priority</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 w-[260px]">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-slate-500">
                  Loading…
                </td>
              </tr>
            )}

            {!loading &&
              displayed.map((p) => {
                const isEditing = editingId === p.id;
                return (
                  <tr key={p.id} className="text-[15px] align-top">
                    <td className="px-4 py-3">
                      {!isEditing ? (
                        <div className="font-medium">{p.project_name}</div>
                      ) : (
                        <input
                          className="w-full h-10 rounded-lg border border-slate-200 px-3"
                          value={edit?.project_name || ""}
                          onChange={(e) => setEdit((prev) => ({ ...(prev as Project), project_name: e.target.value }))}
                        />
                      )}
                      {!isEditing ? (
                        <div className="text-xs text-slate-500 mt-1 line-clamp-2">{p.description || ""}</div>
                      ) : (
                        <textarea
                          className="w-full rounded-lg border border-slate-200 px-3 py-2 mt-2"
                          value={edit?.description || ""}
                          onChange={(e) => setEdit((prev) => ({ ...(prev as Project), description: e.target.value }))}
                        />
                      )}
                    </td>

                    <td className="px-4 py-3">
                      {!isEditing ? (
                        <div className="flex flex-wrap gap-1">
                          {(p.required_skills || []).map((s) => (
                            <span key={s} className="inline-flex rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-700">
                              {s}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <input
                          className="w-full h-10 rounded-lg border border-slate-200 px-3"
                          value={(edit?.required_skills || []).join(", ")}
                          onChange={(e) =>
                            setEdit((prev) => ({
                              ...(prev as Project),
                              required_skills: e.target.value.split(",").map((x) => x.trim()).filter(Boolean),
                            }))
                          }
                          placeholder="comma-separated"
                        />
                      )}
                    </td>

                    <td className="px-4 py-3">
                      {!isEditing ? (
                        p.start_date || "-"
                      ) : (
                        <input
                          type="date"
                          className="h-10 rounded-lg border border-slate-200 px-3"
                          value={edit?.start_date || ""}
                          onChange={(e) => setEdit((prev) => ({ ...(prev as Project), start_date: e.target.value }))}
                        />
                      )}
                    </td>

                    <td className="px-4 py-3">
                      {!isEditing ? (
                        p.end_date || "-"
                      ) : (
                        <input
                          type="date"
                          className="h-10 rounded-lg border border-slate-200 px-3"
                          value={edit?.end_date || ""}
                          onChange={(e) => setEdit((prev) => ({ ...(prev as Project), end_date: e.target.value }))}
                        />
                      )}
                    </td>

                    <td className="px-4 py-3">
                      {!isEditing ? (
                        p.priority || "Medium"
                      ) : (
                        <select
                          className="h-10 rounded-lg border border-slate-200 px-3"
                          value={edit?.priority || "Medium"}
                          onChange={(e) => setEdit((prev) => ({ ...(prev as Project), priority: e.target.value as any }))}
                        >
                          <option>Low</option>
                          <option>Medium</option>
                          <option>High</option>
                        </select>
                      )}
                    </td>

                    <td className="px-4 py-3">
                      {!isEditing ? (
                        p.status || "Open"
                      ) : (
                        <select
                          className="h-10 rounded-lg border border-slate-200 px-3"
                          value={edit?.status || "Open"}
                          onChange={(e) => setEdit((prev) => ({ ...(prev as Project), status: e.target.value as any }))}
                        >
                          <option>Open</option>
                          <option>Closed</option>
                        </select>
                      )}
                    </td>

                    <td className="px-4 py-3">
                      {!isEditing ? (
                        <div className="flex flex-wrap items-center gap-2">
                          <button onClick={() => startEdit(p)} className="h-9 px-3 rounded-lg border border-slate-300">Edit</button>
                          <button onClick={() => remove(p.id)} className="h-9 px-3 rounded-lg border border-rose-300 text-rose-700">Delete</button>
                        </div>
                      ) : (
                        <div className="flex flex-wrap items-center gap-2">
                          <button onClick={saveEdit} className="h-9 px-3 rounded-lg bg-slate-900 text-white">Save</button>
                          <button onClick={cancelEdit} className="h-9 px-3 rounded-lg border border-slate-300">Cancel</button>
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}

            {!loading && displayed.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center text-slate-500">No data.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
