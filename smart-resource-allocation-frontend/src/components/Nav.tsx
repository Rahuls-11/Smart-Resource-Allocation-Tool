import { NavLink } from "react-router-dom";

export default function Nav() {
  const item = (to: string, label: string) => (
    <NavLink
      to={to}
      end
      className={({ isActive }) =>
        [
          "px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap",
          "transition-colors duration-150",
          isActive
            ? "bg-slate-100 text-slate-900 shadow-inner"
            : "text-slate-700 hover:bg-slate-100",
        ].join(" ")
      }
    >
      {label}
    </NavLink>
  );

  return (
    <nav className="sticky top-[57px] z-40 bg-white/90 backdrop-blur border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8">
        <div className="flex items-center gap-2 overflow-x-auto no-scrollbar py-2">
          {item("/", "Home")}
          {item("/employees", "Employees")}
          {item("/projects", "Projects")}
          {item("/hr-allocation", "HR Resource Allocation")}
          {item("/match", "Match")}
        </div>
      </div>
    </nav>
  );
}
