import { Link } from "react-router-dom";

function Card({
  title,
  color,
  to,
}: {
  title: string;
  color: "navy" | "purple";
  to: string;
}) {
  const header =
    color === "navy" ? "bg-[#17386A]" : "bg-[#7C64E8]"; // deep navy / purple
  const bar = color === "navy" ? "bg-[#2B4E86]" : "bg-[#7C64E8]";

  return (
    <Link
      to={to}
      className="block rounded-2xl bg-white shadow-[0_10px_30px_rgba(2,8,20,0.06)] border border-slate-200 overflow-hidden hover:shadow-[0_14px_40px_rgba(2,8,20,0.08)] transition-shadow"
    >
      <div className={`${header} px-6 py-4`}>
        <h3 className="text-white text-lg font-semibold">{title}</h3>
      </div>
      <div className="px-6 py-6">
        <div className="h-3 w-56 rounded-full bg-slate-200 mb-3" />
        <div className="h-3 w-64 rounded-full bg-slate-200 mb-3" />
        <div className="h-3 w-full rounded-full bg-slate-200 mb-3" />
        <div className={`h-3 w-2/3 rounded-full ${bar} mb-3`} />
        <div className="h-3 w-full rounded-full bg-slate-200 mb-3" />
        <div className={`h-3 w-1/2 rounded-full ${bar}`} />
      </div>
    </Link>
  );
}

export default function Home() {
  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title="Employees" color="navy" to="/employees" />
        <Card title="HR Resource Allocation" color="purple" to="/match" />
      </div>
    </>
  );
}
