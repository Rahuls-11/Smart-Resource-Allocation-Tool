import { useEffect, useRef, useState } from "react";
import  api  from "../api/client";

type Project = {
  id: string;
  project_name: string;
  required_skills: string[];
  description?: string;
  priority?: "Low" | "Medium" | "High";
  status?: "Open" | "Closed";
  start_date?: string;
  end_date?: string;
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

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.get("/projects");
      setList(res.data?.data ?? []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const displayed = list.filter((p) => {
    if (q && !`${p.project_name} ${p.description ?? ""}`.toLowerCase().includes(q.toLowerCase())) return false;
    if (skill && !p.required_skills.join(",").toLowerCase().includes(skill.toLowerCase())) return false;
    if (status !== "All" && (p.status ?? "Open") !== status) return false;
    return true;
  });

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

  const create = async () => {
    const payload: Partial<Project> = {
      project_name: nameRef.current?.value || "",
      required_skills:
        skillsRef.current?.value?.split(",").map((s) => s.trim()).filter(Boolean) || [],
      description: descRef.current?.value || "",
      duration: durRef.current?.value || "",
      start_date: startRef.current?.value || "",
      end_date: endRef.current?.value || "",
      headcount: Number(headRef.current?.value || 0) || undefined,
      priority: (prioRef.current?.value as any) || "Medium",
      status: (statusRef.current?.value as any) || "Open",
    };
    if (!payload.project_name) return;

    await api.post("/projects", payload);
    await load();
    resetForm();
    setShowForm(false);
  };

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
              <label className="block text-sm text-slate-700 mb-1">
                Required Skills (comma-separated)
              </label>
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
              <input ref={startRef} placeholder="dd/mm/yyyy" className="w-full h-11 rounded-lg border border-slate-200 px-3" />
            </div>
            <div>
              <label className="block text-sm text-slate-700 mb-1">End</label>
              <input ref={endRef} placeholder="dd/mm/yyyy" className="w-full h-11 rounded-lg border border-slate-200 px-3" />
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
            <button
              onClick={create}
              className="h-10 px-4 rounded-lg bg-slate-900 text-white font-semibold"
            >
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
              <th className="px-4 py-3">Priority</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-slate-500">
                  Loading…
                </td>
              </tr>
            )}
            {!loading &&
              displayed.map((p) => (
                <tr key={p.id} className="text-[15px]">
                  <td className="px-4 py-3">{p.project_name}</td>
                  <td className="px-4 py-3">{p.required_skills.join(", ")}</td>
                  <td className="px-4 py-3">{p.priority ?? "Medium"}</td>
                  <td className="px-4 py-3">{p.status ?? "Open"}</td>
                </tr>
              ))}
            {!loading && displayed.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-10 text-center text-slate-500">
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
