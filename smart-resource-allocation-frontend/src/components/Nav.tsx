import { NavLink } from "react-router-dom";

const base =
  "px-3 py-2 rounded-lg text-[15px] font-medium text-slate-700 hover:bg-slate-100";
const active =
  "bg-slate-100 text-slate-900 shadow-[inset_0_0_0_1px_rgba(0,0,0,0.04)]";

export default function Nav() {
  const link = ({ isActive }: { isActive: boolean }) =>
    `${base} ${isActive ? active : ""}`;

  return (
    <nav className="flex items-center gap-1">
      <NavLink to="/" className={link}>
        Home
      </NavLink>
      <NavLink to="/employees" className={link}>
        Employees
      </NavLink>
      <NavLink to="/projects" className={link}>
        Projects
      </NavLink>
      {/* Design shows both "HR Resource Allocation" and "Match".
         Route target is the same (/match). */}
      <NavLink to="/match" className={link}>
        HR Resource Allocation
      </NavLink>
      <NavLink to="/match" className={link}>
        Match
      </NavLink>
    </nav>
  );
}
