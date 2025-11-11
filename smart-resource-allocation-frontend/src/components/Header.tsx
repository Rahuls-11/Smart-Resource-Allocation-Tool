// src/components/Header.tsx
import { Link } from "react-router-dom";

export default function Header() {
  return (
    <div className="flex items-center gap-3">
      <Link to="/" className="flex items-center gap-3">
        <img
          src="/euspace-logo.png"
          alt="EUSPACE"
          className="h-7 w-auto select-none"
        />
        <span className="text-[18px] font-semibold tracking-tight text-slate-900">
          EUSPACE Technologies Pvt. Ltd.
        </span>
      </Link>
    </div>
  );
}
