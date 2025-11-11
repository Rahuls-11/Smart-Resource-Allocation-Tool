export default function Header() {
  return (
    <header className="sticky top-0 z-50 bg-white">
      {/* thin purple bar across the very top */}
      <div className="h-1 w-full bg-violet-500" />

      {/* logo + company name */}
      <div className="max-w-7xl mx-auto px-4 md:px-6 lg:px-8 py-3 flex items-center gap-3">
        {/* Use public folder image via absolute path */}
        <img
          src="/euspace-logo.png"
          alt="EUSPACE"
          className="h-8 w-auto select-none"
          draggable={false}
        />
        <div className="text-xl md:text-2xl font-semibold text-slate-900">
          EUSPACE Technologies Pvt. Ltd.
        </div>
      </div>
    </header>
  );
}
