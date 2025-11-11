import { Outlet } from "react-router-dom";
import Header from "./components/Header";
import Nav from "./components/Nav";

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Top bar */}
      <header className="sticky top-0 z-50 bg-white/90 backdrop-blur border-b border-slate-200">
        <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
          <Header />
          <Nav />
        </div>
      </header>

      {/* Page content */}
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
