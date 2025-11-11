import { useEffect, useRef, useState } from "react";
import api from "../api/client";

type Employee = { id: string; name: string };
type Project  = { id: string; project_name: string };
type Allocation = {
  id: string;
  employee_id: string;
  employee_name: string;
  project_id: string;
  project_name: string;
  allocated_on: string;
  status: string;
};

export default function HrResourceAllocation() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [allocations, setAllocations] = useState<Allocation[]>([]);
  const [loading, setLoading] = useState(false);

  const empRef = useRef<HTMLSelectElement>(null);
  const projRef = useRef<HTMLSelectElement>(null);

  const load = async () => {
    setLoading(true);
    try {
      const [empRes, projRes, allocRes] = await Promise.all([
        api.get("/employees"),
        api.get("/projects"),
        api.get("/hr_allocation"),
      ]);
      setEmployees(empRes.data?.data ?? []);
      setProjects(projRes.data?.data ?? []);
      setAllocations(allocRes.data?.data ?? []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const allocate = async () => {
    const employee_id = empRef.current?.value || "";
    const project_id  = projRef.current?.value || "";
    if (!employee_id || !project_id) return alert("Select both employee and project");
    await api.post("/hr_allocation", { employee_id, project_id });
    await load();
  };

  const remove = async (id: string) => {
    if (!confirm("Remove this allocation?")) return;
    await api.delete(`/hr_allocation/${id}`);
    await load();
  };

  return (
    <>
      <h1 className="text-2xl font-semibold text-slate-900 mb-6">HR Resource Allocation</h1>

      {/* Allocate */}
      <div className="rounded-xl bg-white border border-slate-200 p-4 mb-6">
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="text-sm text-slate-700 mb-1">Employee</label>
            <select ref={empRef} className="h-11 w-64 rounded-lg border border-slate-200 px-3">
              <option value="">Select Employee</option>
              {employees.map(e => <option key={e.id} value={e.id}>{e.name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-sm text-slate-700 mb-1">Project</label>
            <select ref={projRef} className="h-11 w-64 rounded-lg border border-slate-200 px-3">
              <option value="">Select Project</option>
              {projects.map(p => <option key={p.id} value={p.id}>{p.project_name}</option>)}
            </select>
          </div>
          <button onClick={allocate} className="h-11 px-5 rounded-lg bg-slate-900 text-white font-semibold">
            Allocate
          </button>
        </div>
      </div>

      {/* Allocations */}
      <div className="rounded-xl bg-white border border-slate-200">
        <table className="w-full text-left">
          <thead>
            <tr className="text-sm text-slate-600">
              <th className="px-4 py-3">Employee</th>
              <th className="px-4 py-3">Project</th>
              <th className="px-4 py-3">Allocated On</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-slate-500">Loading…</td></tr>
            )}
            {!loading && allocations.map(a => (
              <tr key={a.id} className="text-[15px]">
                <td className="px-4 py-3">{a.employee_name}</td>
                <td className="px-4 py-3">{a.project_name}</td>
                <td className="px-4 py-3">{new Date(a.allocated_on).toLocaleDateString()}</td>
                <td className="px-4 py-3">{a.status}</td>
                <td className="px-4 py-3">
                  <button onClick={() => remove(a.id)} className="text-rose-600 hover:underline">Remove</button>
                </td>
              </tr>
            ))}
            {!loading && allocations.length === 0 && (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-slate-500">No allocations yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
