import Link from "next/link";

export default function Footer() {
  return (
    <footer className="w-full border-t border-slate-200 bg-white/80 backdrop-blur-md relative z-10 pt-16 pb-12 px-4 md:px-8">
      <div className="max-w-7xl mx-auto space-y-12">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-8 pb-12 border-b border-slate-100">
          {/* Brand */}
          <div className="space-y-3 max-w-sm">
            <Link href="/" className="flex items-center gap-2">
              <span className="font-black text-2xl tracking-tighter text-slate-950">
                MANAKSETU
              </span>
              <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                AI PLATFORM
              </span>
            </Link>
            <p className="text-xs text-slate-500 leading-relaxed font-normal">
              AI-powered discovery for Indian Standards. Simplifying regulatory and technical intelligence for civil engineering, construction, and manufacturing.
            </p>
          </div>

          {/* Nav Links */}
          <div className="flex flex-wrap items-center gap-8 text-xs font-semibold text-slate-600">
            <Link href="/" className="hover:text-slate-950 transition-colors">
              Search
            </Link>
            <Link href="/standards" className="hover:text-slate-950 transition-colors">
              Standards Catalog
            </Link>
            <a
              href="https://bis.gov.in"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-slate-950 transition-colors"
            >
              BIS Official Portal ↗
            </a>
          </div>
        </div>

        {/* Bottom Credits */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-slate-400">
          <div>
            © {new Date().getFullYear()} MANAKSETU INTEL • ALL RIGHTS RESERVED
          </div>
          <div className="flex items-center gap-4">
            <span>SYS // BIS.VECTOR.INDEX</span>
            <span>REST API v1.0</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
