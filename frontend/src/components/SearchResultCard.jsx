"use client";

import Link from "next/link";
import { ArrowUpRight, Calendar, ShieldCheck, FileCheck2, Tag } from "lucide-react";
import { formatSimilarityScore, formatDate } from "@/lib/utils";

export default function SearchResultCard({ result, index }) {
  const { standard, similarity_score } = result;
  const matchPercent = formatSimilarityScore(similarity_score);
  const formattedDate = formatDate(standard.publication_date);

  return (
    <div className="search-result-card group editorial-card rounded-2xl p-6 md:p-8 flex flex-col justify-between gap-6 relative overflow-hidden bg-white hover:-translate-y-1">
      {/* Top Header Row */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="font-mono font-bold text-xs px-3 py-1 rounded-full bg-slate-900 text-white tracking-wider">
            {standard.standard_number}
          </span>

          {standard.is_active ? (
            <span className="text-[11px] font-medium text-emerald-700 bg-emerald-50 border border-emerald-200/60 px-2.5 py-0.5 rounded-full flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Active
            </span>
          ) : (
            <span className="text-[11px] font-medium text-slate-500 bg-slate-100 border border-slate-200 px-2.5 py-0.5 rounded-full">
              Inactive
            </span>
          )}
        </div>

        {/* Similarity Score Percentage Pill */}
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 font-mono text-xs font-bold shadow-xs">
          <Tag className="w-3.5 h-3.5 text-blue-600" />
          <span>{matchPercent}</span>
        </div>
      </div>

      {/* Main Content */}
      <div className="space-y-3">
        <h3 className="text-xl md:text-2xl font-bold text-slate-900 tracking-tight leading-snug group-hover:text-blue-600 transition-colors">
          <Link href={`/standards/${encodeURIComponent(standard.id)}`} className="focus:outline-none">
            {standard.title}
          </Link>
        </h3>

        {standard.description && (
          <p className="text-sm md:text-base text-slate-600 line-clamp-3 leading-relaxed">
            {standard.description}
          </p>
        )}
      </div>

      {/* Metadata Badges Footer */}
      <div className="pt-4 border-t border-slate-100 flex flex-wrap items-center justify-between gap-4 text-xs text-slate-500">
        <div className="flex flex-wrap items-center gap-4">
          {standard.latest_version && (
            <div className="flex items-center gap-1.5">
              <FileCheck2 className="w-4 h-4 text-slate-400" />
              <span>{standard.latest_version}</span>
            </div>
          )}

          {formattedDate && (
            <div className="flex items-center gap-1.5">
              <Calendar className="w-4 h-4 text-slate-400" />
              <span>{formattedDate}</span>
            </div>
          )}

          {standard.mandatory_certification && (
            <div className="flex items-center gap-1.5 text-slate-700 font-medium">
              <ShieldCheck className="w-4 h-4 text-blue-600" />
              <span className="truncate max-w-[220px]" title={standard.mandatory_certification}>
                {standard.mandatory_certification}
              </span>
            </div>
          )}
        </div>

        {/* Action Link */}
        <Link
          href={`/standards/${encodeURIComponent(standard.id)}`}
          className="inline-flex items-center gap-1.5 font-semibold text-slate-900 group-hover:text-blue-600 transition-all text-xs"
        >
          <span>View Specification</span>
          <ArrowUpRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
        </Link>
      </div>
    </div>
  );
}
