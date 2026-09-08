import { ChevronLeft, ChevronRight } from "lucide-react";

export default function Pagination({ skip, limit, hasMore, onPrev, onNext }) {
  const currentPage = Math.floor(skip / limit) + 1;

  return (
    <div className="flex items-center justify-between pt-8 border-t border-slate-200">
      <button
        onClick={onPrev}
        disabled={skip === 0}
        className="inline-flex items-center gap-2 font-semibold text-xs px-5 py-2.5 rounded-full border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:hover:bg-white transition-all cursor-pointer shadow-2xs"
      >
        <ChevronLeft className="w-4 h-4" />
        <span>Previous</span>
      </button>

      <div className="font-mono text-xs font-semibold text-slate-500 bg-slate-100 px-4 py-1.5 rounded-full border border-slate-200">
        Page {currentPage}
      </div>

      <button
        onClick={onNext}
        disabled={!hasMore}
        className="inline-flex items-center gap-2 font-semibold text-xs px-5 py-2.5 rounded-full border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:hover:bg-white transition-all cursor-pointer shadow-2xs"
      >
        <span>Next</span>
        <ChevronRight className="w-4 h-4" />
      </button>
    </div>
  );
}
