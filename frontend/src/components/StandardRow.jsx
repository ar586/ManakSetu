"use client";

import Link from "next/link";
import { ArrowUpRight, ShieldCheck, Calendar, FileCheck2 } from "lucide-react";
import { formatDate } from "@/lib/utils";

export default function StandardRow({ standard, index }) {
  const formattedDate = formatDate(standard.publication_date);
  const displayNum = String(index + 1).padStart(2, "0");

  return (
    <div className="standard-row group editorial-card rounded-2xl p-6 md:p-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 bg-white hover:-translate-y-0.5">
      <div className="flex items-start gap-6 flex-1">
        {/* Index Number */}
        <span className="font-editorial-num text-2xl md:text-3xl font-black text-slate-300 group-hover:text-blue-600 transition-colors shrink-0">
          {displayNum}
        </span>

        <div className="space-y-2.5 flex-1">
          {/* Top badges */}
          <div className="flex flex-wrap items-center gap-3">
            <span className="font-mono font-bold text-xs px-3 py-1 rounded-full bg-slate-900 text-white">
              {standard.standard_number}
            </span>

            {standard.is_active ? (
              <span className="text-[11px] font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Active
              </span>
            ) : (
              <span className="text-[11px] font-medium text-slate-500 bg-slate-100 border border-slate-200 px-2.5 py-0.5 rounded-full">
                Inactive
              </span>
            )}
          </div>

          {/* Title */}
          <h3 className="text-lg md:text-xl font-bold text-slate-900 group-hover:text-blue-600 transition-colors tracking-tight">
            <Link href={`/standards/${encodeURIComponent(standard.id)}`}>
              {standard.title}
            </Link>
          </h3>

          {/* Description */}
          {standard.description && (
            <p className="text-xs md:text-sm text-slate-600 line-clamp-2 leading-relaxed max-w-3xl">
              {standard.description}
            </p>
          )}

          {/* Metadata */}
          <div className="flex flex-wrap items-center gap-4 pt-2 text-xs text-slate-500">
            {standard.latest_version && (
              <div className="flex items-center gap-1.5">
                <FileCheck2 className="w-3.5 h-3.5 text-slate-400" />
                <span>{standard.latest_version}</span>
              </div>
            )}
            {formattedDate && (
              <div className="flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span>{formattedDate}</span>
              </div>
            )}
            {standard.mandatory_certification && (
              <div className="flex items-center gap-1.5 text-slate-700 font-medium">
                <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                <span className="truncate max-w-[200px]" title={standard.mandatory_certification}>
                  {standard.mandatory_certification}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Right Link CTA */}
      <Link
        href={`/standards/${encodeURIComponent(standard.id)}`}
        className="self-end md:self-center inline-flex items-center gap-2 font-bold text-xs px-4 py-2.5 rounded-full bg-slate-100 text-slate-900 group-hover:bg-blue-600 group-hover:text-white transition-all shrink-0"
      >
        <span>Details</span>
        <ArrowUpRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
      </Link>
    </div>
  );
}
