"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowLeft, AlertTriangle, CheckCircle2, FileText } from "lucide-react";

export default function AnalyzePage() {
  const [analysis] = useState(() => {
    if (typeof window === "undefined") return null;
    const saved = sessionStorage.getItem("manaksetu-analysis");
    return saved ? JSON.parse(saved) : null;
  });

  if (!analysis) return <main className="mx-auto max-w-3xl px-4 pb-24 pt-36 text-center"><h1 className="text-2xl font-black text-slate-950">No analysis found</h1><p className="mt-2 text-sm text-slate-500">Upload a tender document from the home page to begin.</p><Link href="/" className="mt-6 inline-flex items-center gap-2 rounded-full bg-slate-950 px-5 py-3 text-sm font-bold text-white"><ArrowLeft className="h-4 w-4" /> Back home</Link></main>;

  const compliance = analysis.compliance_analysis || {};
  return <main className="mx-auto max-w-7xl px-4 pb-24 pt-32">
    <Link href="/" className="inline-flex items-center gap-2 text-xs font-bold text-slate-500 hover:text-blue-600"><ArrowLeft className="h-4 w-4" /> New analysis</Link>
    <div className="mt-8 flex flex-wrap items-end justify-between gap-4 border-b border-slate-200 pb-8"><div><p className="flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-widest text-blue-600"><FileText className="h-4 w-4" /> Tender analysis</p><h1 className="mt-2 text-3xl font-black text-slate-950">{analysis.filename}</h1></div><span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700">Analysis complete</span></div>
    <div className="mt-8 grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
      <section><h2 className="text-xs font-mono font-bold uppercase tracking-widest text-slate-400">Applicable standards</h2><div className="mt-4 space-y-3">{analysis.matched_standards?.length ? analysis.matched_standards.map((item) => <article key={item.standard.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-start justify-between gap-4"><div><p className="font-mono text-xs font-bold text-blue-600">{item.standard.standard_number}</p><h3 className="mt-1 font-bold text-slate-950">{item.standard.title}</h3></div><span className="shrink-0 rounded-full bg-blue-50 px-2 py-1 text-xs font-bold text-blue-700">{Math.round(item.similarity_score * 100)}% match</span></div><p className="mt-3 text-sm leading-relaxed text-slate-600">{item.standard.description}</p></article>) : <p className="rounded-2xl border border-dashed border-slate-300 p-6 text-sm text-slate-500">No matching standards were found.</p>}</div></section>
      <section className="space-y-5"><h2 className="text-xs font-mono font-bold uppercase tracking-widest text-slate-400">AI compliance analysis</h2><article className="rounded-2xl border border-slate-200 bg-slate-950 p-6 text-white"><p className="text-sm leading-relaxed text-slate-200">{compliance.summary}</p></article>{analysis.findings?.length > 0 && <article className="rounded-2xl border border-slate-200 bg-white p-5"><h3 className="font-bold text-slate-900">Structured findings</h3><div className="mt-3 space-y-3">{analysis.findings.map((finding, index) => <div key={index} className="border-l-2 border-blue-500 pl-3 text-sm"><p className="font-bold text-slate-900">{finding.compliance_status.replaceAll("_", " ")}</p><p className="mt-1 text-slate-600">{finding.explanation}</p>{(finding.clause || finding.section || finding.page) && <p className="mt-1 text-xs text-slate-400">Source: {[finding.clause && `clause ${finding.clause}`, finding.section && `section ${finding.section}`, finding.page && `page ${finding.page}`].filter(Boolean).join(", ")}</p>}</div>)}</div></article>}{[["Conflicts", compliance.conflicts, AlertTriangle, "text-rose-600"], ["Gaps", compliance.gaps || compliance.compliance_gaps, AlertTriangle, "text-amber-600"], ["Recommendations", compliance.recommendations || compliance.clauses_to_watch, CheckCircle2, "text-emerald-600"]].map(([title, items, Icon, color]) => <article key={title} className="rounded-2xl border border-slate-200 bg-white p-5"><h3 className="flex items-center gap-2 font-bold text-slate-900"><Icon className={`h-4 w-4 ${color}`} />{title}</h3><ul className="mt-3 space-y-2 text-sm leading-relaxed text-slate-600">{(items?.length ? items : ["No specific items were flagged."]).map((item, index) => <li key={index} className="border-l-2 border-slate-200 pl-3">{item}</li>)}</ul></article>)}</section>
    </div>
  </main>;
}