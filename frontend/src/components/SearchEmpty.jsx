"use client";

import Link from "next/link";
import { SearchX, ArrowRight } from "lucide-react";

export default function SearchEmpty({ onBrowseAll }) {
  return (
    <div className="w-full py-16 px-6 rounded-3xl bg-white border border-slate-200/80 shadow-sm flex flex-col items-center justify-center text-center space-y-6">
      <div className="w-14 h-14 rounded-2xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600">
        <SearchX className="w-7 h-7" />
      </div>

      <div className="space-y-2 max-w-sm">
        <h3 className="text-2xl font-bold text-slate-900 tracking-tight">
          No standards found.
        </h3>
        <p className="text-sm text-slate-500 leading-relaxed">
          Try describing your requirement differently or use a broader technical description.
        </p>
      </div>

      <Link
        href="/standards"
        onClick={onBrowseAll}
        className="inline-flex items-center gap-2 font-semibold text-xs px-5 py-3 rounded-full bg-slate-900 text-white hover:bg-blue-600 transition-all shadow-sm"
      >
        <span>Browse all standards</span>
        <ArrowRight className="w-4 h-4" />
      </Link>
    </div>
  );
}
