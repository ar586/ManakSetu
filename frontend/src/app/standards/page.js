"use client";

import { useState, useEffect, useRef } from "react";
import { Search, BookOpen, RotateCcw } from "lucide-react";
import gsap from "gsap";
import StandardRow from "@/components/StandardRow";
import Pagination from "@/components/Pagination";
import { getStandards } from "@/lib/api";

const LIMIT = 10;

export default function StandardsPage() {
  const [standards, setStandards] = useState([]);
  const [skip, setSkip] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [filterQuery, setFilterQuery] = useState("");
  const containerRef = useRef(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(false);
      try {
        const data = await getStandards({ skip, limit: LIMIT });
        setStandards(data);
      } catch (err) {
        console.error("Failed to load standards list:", err);
        setError(true);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [skip]);

  useEffect(() => {
    if (loading || error || standards.length === 0 || !containerRef.current) return;

    const ctx = gsap.context(() => {
      gsap.fromTo(
        ".standard-row",
        { y: 25, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.45,
          stagger: 0.07,
          ease: "power3.out",
        }
      );
    }, containerRef);

    return () => ctx.revert();
  }, [loading, error, standards, filterQuery]);

  // Client-side filtering over currently loaded results
  const filteredStandards = standards.filter((s) => {
    if (!filterQuery.trim()) return true;
    const q = filterQuery.toLowerCase();
    return (
      s.standard_number.toLowerCase().includes(q) ||
      s.title.toLowerCase().includes(q) ||
      (s.description && s.description.toLowerCase().includes(q))
    );
  });

  return (
    <div ref={containerRef} className="pt-32 pb-24 px-4 max-w-6xl mx-auto space-y-10 relative z-10 min-h-screen">
      {/* Page Header */}
      <div className="space-y-4 max-w-3xl">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold">
          <BookOpen className="w-3.5 h-3.5" />
          <span>Catalog Directory</span>
        </div>

        <h1 className="text-4xl md:text-5xl font-black text-slate-950 tracking-tight">
          Indian Standards
        </h1>

        <p className="text-base text-slate-600 font-normal leading-relaxed">
          Browse and discover standards across the ManakSetu knowledge base.
        </p>
      </div>

      {/* Filter / Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-2xl bg-white border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3 w-full sm:w-auto flex-1 px-2">
          <Search className="w-5 h-5 text-slate-400" />
          <input
            type="text"
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            placeholder="Filter loaded results (e.g. IS 456, Concrete, Steel)..."
            className="w-full bg-transparent text-sm font-medium text-slate-900 placeholder:text-slate-400 focus:outline-none"
          />
        </div>
        <div className="text-xs font-mono text-slate-400 shrink-0 px-2">
          showing {filteredStandards.length} items
        </div>
      </div>

      {/* Loading Skeleton */}
      {loading && (
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-28 rounded-2xl bg-white border border-slate-200/80 animate-pulse p-6" />
          ))}
        </div>
      )}

      {/* Error state */}
      {!loading && error && (
        <div className="py-12 px-6 rounded-3xl bg-red-50/50 border border-red-200 text-center space-y-4">
          <p className="text-slate-700 font-medium">Failed to load standards. Please check backend connection.</p>
          <button
            onClick={() => setSkip(skip)}
            className="inline-flex items-center gap-2 font-semibold text-xs px-4 py-2 rounded-full bg-slate-900 text-white"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* List Results */}
      {!loading && !error && (
        <>
          {filteredStandards.length === 0 ? (
            <div className="py-16 text-center text-slate-500 font-medium bg-white rounded-3xl border border-slate-200">
              No matching standards found for filter “{filterQuery}”.
            </div>
          ) : (
            <div className="space-y-4">
              {filteredStandards.map((std, idx) => (
                <StandardRow key={std.id} standard={std} index={idx} />
              ))}
            </div>
          )}

          {/* Pagination Controls */}
          <Pagination
            skip={skip}
            limit={LIMIT}
            hasMore={standards.length >= LIMIT}
            onPrev={() => setSkip(Math.max(0, skip - LIMIT))}
            onNext={() => setSkip(skip + LIMIT)}
          />
        </>
      )}
    </div>
  );
}
