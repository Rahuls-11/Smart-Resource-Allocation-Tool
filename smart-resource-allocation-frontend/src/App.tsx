import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Header from "./components/Header";
import Nav from "./components/Nav";
import Home from "./pages/Home";
import Employees from "./pages/Employees";
import Projects from "./pages/Projects";
import Match from "./pages/Match";
import HrResourceAllocation from "./pages/HrResourceAllocation"; // <-- NEW

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col">
      {/* --- Top Header --- */}
      <Header />

      {/* --- Top Navigation Bar --- */}
      <Nav />

      {/* --- Main Content Area --- */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-4 md:px-6 lg:px-8 py-6">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/employees" element={<Employees />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/hr-allocation" element={<HrResourceAllocation />} />
          <Route path="/match" element={<Match />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}