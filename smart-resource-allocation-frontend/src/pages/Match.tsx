import { useEffect, useState } from "react";
import api from "../api/client";

type Project = {
  id: string;
  project_name: string;
  required_skills: string[];
  description?: string;
};

type Candidate = {
  id: string;
  name: string;
  role?: string;
  matched_skills: string[];       // only matched skills
  availability?: string;
  availability_dates?: string[];
  score?: number;
  ai_reason?: string;             // short reason (<= 1–2 lines)
};

export default function Match() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState<string>("");
  const [topN, setTopN] = useState<number>(3);
  const [useAI, setUseAI] = useState(true);
  const [loading, setLoading] = useState(false);
  const [candidates, setCandidates] = useState<Candidate[]>([]);

  useEffect(() => {
    (async () => {
      const res = await api.get("/projects", { params: { sort: "-created_at", limit: 200 } });
      const rows: Project[] = res.data?.data ?? [];
      setProjects(rows);
      if (rows[0]) setProjectId(rows[0].id);
    })();
  }, []);

  const selected = projects.find((p) => p.id === projectId);

  const fetchMatches = async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const res = await api.get("/match", {
        params: { project_id: projectId, limit: topN, use_ai: useAI ? 1 : 0 },
      });
      setCandidates(res.data?.candidates ?? []);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <h1 className="text-2xl font-semibold text-slate-900 mb-6">AI Matching</h1>

      <div className="rounded-xl bg-white border border-slate-200 p-4 mb-6">
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex flex-col">
            <label className="text-sm text-slate-700 mb-1">Project</label>
            <select
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              className="h-11 w-72 rounded-lg border border-slate-200 px-3"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.project_name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col">
            <label className="text-sm text-slate-700 mb-1">Top N</label>
            <input
              type="number"
              value={topN}
              onChange={(e) =>
                setTopN(Math.max(1, Number.parseInt(e.target.value || "1", 10) || 1))
              }
              className="h-11 w-24 rounded-lg border border-slate-200 px-3"
            />
          </div>

          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={useAI}
              onChange={(e) => setUseAI(e.target.checked)}
              className="h-4 w-4"
            />
            <span className="text-[15px] text-slate-700">Use AI Re-rank</span>
          </label>

          <button
            onClick={fetchMatches}
            disabled={loading}
            className="h-11 px-5 rounded-lg bg-slate-900 text-white font-semibold"
          >
            {loading ? "Loading..." : "Get Matches"}
          </button>
        </div>
      </div>

      {/* Project summary */}
      {selected && (
        <div className="rounded-xl bg-white border border-slate-200 p-4 mb-4">
          <div className="text-[15px]">
            <div className="font-semibold mb-1">{selected.project_name}</div>
            <div className="text-slate-600">
              <span className="font-medium">Required:</span>{" "}
              {selected.required_skills.join(", ")}
            </div>
            {selected.description && (
              <div className="text-slate-600 mt-1">{selected.description}</div>
            )}
          </div>
        </div>
      )}

      {/* Results table: only Score, Name, Role, Matched Skills, Availability, Short Reason */}
      <div className="rounded-xl bg-white border border-slate-200 overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="text-sm text-slate-600">
              <th className="px-4 py-3">Score</th>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Role</th>
              <th className="px-4 py-3">Matched Skills</th>
              <th className="px-4 py-3">Availability</th>
              <th className="px-4 py-3">AI Reason</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {candidates.map((c) => (
              <tr key={c.id} className="text-[15px] align-top">
                <td className="px-4 py-3">{c.score != null ? c.score.toFixed(2) : "-"}</td>
                <td className="px-4 py-3 font-medium">{c.name}</td>
                <td className="px-4 py-3">{c.role || "-"}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {(c.matched_skills || []).map((s) => (
                      <span key={s} className="inline-flex rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-700">
                        {s}
                      </span>
                    ))}
                    {(c.matched_skills || []).length === 0 && <span className="text-slate-500">-</span>}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {(c.availability_dates || []).map((d) => (
                      <span key={d} className="inline-flex rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-700">
                        {d}
                      </span>
                    ))}
                  </div>
                  <div className="text-xs text-slate-500">{c.availability || ""}</div>
                </td>
                <td className="px-4 py-3">{c.ai_reason || "-"}</td>
              </tr>
            ))}
            {candidates.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-slate-500">
                  No candidates found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
