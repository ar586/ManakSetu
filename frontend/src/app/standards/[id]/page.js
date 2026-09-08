"use client";

import { use, useEffect, useState, useRef } from "react";
import Link from "next/link";
import { 
  ArrowLeft, 
  Download, 
  ShieldCheck, 
  Calendar, 
  FileCheck2, 
  CheckCircle2, 
  XCircle,
  FileQuestion,
  ExternalLink
} from "lucide-react";
import gsap from "gsap";
import MetadataItem from "@/components/MetadataItem";
import { getStandardById } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function StandardDetailPage({ params: paramsPromise }) {
  const params = use(paramsPromise);
  const id = params?.id;

  const [standard, setStandard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    async function loadStandard() {
      if (!id) return;
      setLoading(true);
      setNotFound(false);
      try {
        const data = await getStandardById(id);
        if (!data) {
          setNotFound(true);
        } else {
          setStandard(data);
        }
      } catch (err) {
        console.error("Failed to load standard detail:", err);
        setNotFound(true);
      } finally {
        setLoading(false);
      }
    }
    loadStandard();
  }, [id]);

  useEffect(() => {
    if (loading || notFound || !standard || !containerRef.current) return;

    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

      tl.fromTo(".detail-anim-1", { y: -10, opacity: 0 }, { y: 0, opacity: 1, duration: 0.4 })
        .fromTo(".detail-anim-2", { y: 25, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5 }, "-=0.2")
        .fromTo(".detail-anim-3", { y: 25, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5 }, "-=0.3")
        .fromTo(".detail-anim-4", { y: 25, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5 }, "-=0.3");
    }, containerRef);

    return () => ctx.revert();
  }, [loading, notFound, standard]);

  // Loading State
  if (loading) {
    return (
      <div className="pt-36 pb-24 px-4 max-w-5xl mx-auto space-y-8 animate-pulse">
        <div className="h-6 w-48 bg-slate-200 rounded-full" />
        <div className="h-16 w-3/4 bg-slate-200 rounded-2xl" />
        <div className="h-32 w-full bg-slate-200 rounded-3xl" />
      </div>
    );
  }

  // 404 Custom State
  if (notFound || !standard) {
    return (
      <div className="pt-36 pb-24 px-4 max-w-3xl mx-auto text-center space-y-6">
        <div className="w-16 h-16 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600 mx-auto">
          <FileQuestion className="w-8 h-8" />
        </div>

        <div className="space-y-2">
          <h1 className="text-3xl font-bold text-slate-950">Standard not found.</h1>
          <p className="text-slate-500 text-sm">
            The standard with ID “{id}” could not be located in the ManakSetu database.
          </p>
        </div>

        <div>
          <Link
            href="/standards"
            className="inline-flex items-center gap-2 font-semibold text-xs px-6 py-3 rounded-full bg-slate-900 text-white hover:bg-blue-600 transition-all shadow-md"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Standards</span>
          </Link>
        </div>
      </div>
    );
  }

  const formattedDate = formatDate(standard.publication_date);

  return (
    <div ref={containerRef} className="pt-32 pb-24 px-4 max-w-6xl mx-auto space-y-10 relative z-10">
      {/* Breadcrumb Navigation */}
      <div className="detail-anim-1 flex items-center gap-2 text-xs font-mono text-slate-500">
        <Link href="/standards" className="hover:text-blue-600 transition-colors flex items-center gap-1">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Standards</span>
        </Link>
        <span>/</span>
        <span className="text-slate-950 font-bold">{standard.standard_number}</span>
      </div>

      {/* Main Editorial Hero */}
      <div className="detail-anim-2 space-y-4 border-b border-slate-200/80 pb-8">
        <div className="flex flex-wrap items-center gap-3">
          <span className="font-mono font-black text-sm px-4 py-1.5 rounded-full bg-slate-950 text-white tracking-wide">
            {standard.standard_number}
          </span>

          {standard.is_active ? (
            <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-full flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              Active Standard
            </span>
          ) : (
            <span className="text-xs font-semibold text-slate-600 bg-slate-100 border border-slate-200 px-3 py-1 rounded-full flex items-center gap-1.5">
              <XCircle className="w-4 h-4 text-slate-400" />
              Inactive Standard
            </span>
          )}
        </div>

        <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-slate-950 tracking-tight leading-tight">
          {standard.title}
        </h1>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Description */}
        <div className="detail-anim-3 lg:col-span-2 space-y-6">
          <div className="bg-white border border-slate-200/80 rounded-3xl p-8 space-y-4 shadow-sm">
            <h2 className="text-sm font-mono font-bold text-slate-400 uppercase tracking-widest">
              SPECIFICATION OVERVIEW
            </h2>

            {standard.description ? (
              <p className="text-base md:text-lg text-slate-700 leading-relaxed font-normal">
                {standard.description}
              </p>
            ) : (
              <p className="text-sm text-slate-400 italic">
                No official description text available for this standard.
              </p>
            )}
          </div>

          {/* Download CTA if download_link exists */}
          {standard.download_link && (
            <div className="p-8 rounded-3xl bg-blue-50/70 border border-blue-200 flex flex-col sm:flex-row sm:items-center justify-between gap-6">
              <div className="space-y-1">
                <h3 className="font-bold text-slate-900 text-lg">Official Specification File</h3>
                <p className="text-xs text-slate-600">Access full document specifications on official BIS portal.</p>
              </div>

              <a
                href={standard.download_link}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-2 font-bold text-xs px-6 py-3.5 rounded-2xl bg-blue-600 text-white hover:bg-blue-700 transition-all shadow-md shadow-blue-500/20 shrink-0"
              >
                <Download className="w-4 h-4" />
                <span>Download Standard</span>
                <ExternalLink className="w-3.5 h-3.5 opacity-80" />
              </a>
            </div>
          )}
        </div>

        {/* Right Column: Standard Information Grid */}
        <div className="detail-anim-4 space-y-6">
          <div className="bg-white border border-slate-200/80 rounded-3xl p-6 space-y-6 shadow-sm">
            <h2 className="text-xs font-mono font-bold text-slate-400 uppercase tracking-widest pb-3 border-b border-slate-100">
              STANDARD METADATA
            </h2>

            <div className="space-y-3">
              <MetadataItem
                label="Standard Number"
                value={standard.standard_number}
                icon={FileCheck2}
              />

              <MetadataItem
                label="Latest Version"
                value={standard.latest_version}
                icon={FileCheck2}
              />

              <MetadataItem
                label="Publication Date"
                value={formattedDate}
                icon={Calendar}
              />

              <MetadataItem
                label="Mandatory Certification"
                value={standard.mandatory_certification}
                icon={ShieldCheck}
              />

              <MetadataItem
                label="Status"
                value={standard.is_active ? "Active Code of Practice" : "Superseded / Inactive"}
                icon={standard.is_active ? CheckCircle2 : XCircle}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
