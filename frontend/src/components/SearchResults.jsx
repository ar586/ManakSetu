"use client";

import { useEffect, useRef } from "react";
import gsap from "gsap";
import SearchResultCard from "@/components/SearchResultCard";
import SearchLoading from "@/components/SearchLoading";
import SearchEmpty from "@/components/SearchEmpty";
import SearchError from "@/components/SearchError";

export default function SearchResults({
  query,
  loading,
  error,
  data,
  onRetry,
}) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || loading || error || !data || data.results.length === 0) return;

    const ctx = gsap.context(() => {
      gsap.fromTo(
        ".search-result-card",
        { y: 30, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.5,
          stagger: 0.08,
          ease: "power3.out",
        }
      );
    }, containerRef);

    return () => ctx.revert();
  }, [data, loading, error]);

  if (!query && !loading && !error && !data) {
    return null;
  }

  return (
    <section ref={containerRef} className="w-full max-w-5xl mx-auto py-8 space-y-8 scroll-mt-24" id="results">
      {loading && <SearchLoading />}

      {error && <SearchError onRetry={onRetry} />}

      {!loading && !error && data && data.results.length === 0 && (
        <SearchEmpty />
      )}

      {!loading && !error && data && data.results.length > 0 && (
        <div className="space-y-8">
          {/* Header info */}
          <div className="flex flex-col sm:flex-row sm:items-end justify-between border-b border-slate-200 pb-4 gap-2">
            <div>
              <div className="text-xs font-mono text-slate-400 uppercase tracking-widest mb-1">
                SEMANTIC MATCH RESULTS
              </div>
              <h2 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
                Search results for <span className="text-blue-600">“{data.query}”</span>
              </h2>
            </div>
            <div className="text-xs font-mono font-semibold text-slate-500 bg-slate-100 px-3 py-1.5 rounded-full self-start sm:self-auto border border-slate-200">
              {data.results.length} {data.results.length === 1 ? "relevant standard" : "relevant standards"}
            </div>
          </div>

          {/* Result Cards Grid */}
          <div className="grid grid-cols-1 gap-6">
            {data.results.map((result, idx) => (
              <SearchResultCard key={result.standard.id || idx} result={result} index={idx} />
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
