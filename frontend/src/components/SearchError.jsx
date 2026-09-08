"use client";

import { AlertCircle, RotateCcw } from "lucide-react";

export default function SearchError({ onRetry }) {
  return (
    <div className="w-full py-14 px-6 rounded-3xl bg-red-50/50 border border-red-200 flex flex-col items-center justify-center text-center space-y-6">
      <div className="w-14 h-14 rounded-2xl bg-red-100 border border-red-200 flex items-center justify-center text-red-600">
        <AlertCircle className="w-7 h-7" />
      </div>

      <div className="space-y-2 max-w-sm">
        <h3 className="text-2xl font-bold text-slate-900 tracking-tight">
          Something went wrong.
        </h3>
        <p className="text-sm text-slate-600 leading-relaxed">
          We couldn't complete the search. Please check your connection and try again.
        </p>
      </div>

      <button
        onClick={onRetry}
        className="inline-flex items-center gap-2 font-semibold text-xs px-5 py-3 rounded-full bg-slate-900 text-white hover:bg-blue-600 transition-all cursor-pointer"
      >
        <RotateCcw className="w-4 h-4" />
        <span>Retry</span>
      </button>
    </div>
  );
}
