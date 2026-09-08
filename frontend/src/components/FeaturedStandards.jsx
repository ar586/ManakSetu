"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { ArrowRight, ArrowUpRight, ShieldCheck } from "lucide-react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { getStandards } from "@/lib/api";

gsap.registerPlugin(ScrollTrigger);

export default function FeaturedStandards() {
  const [standards, setStandards] = useState([]);
  const [loading, setLoading] = useState(true);
  const sectionRef = useRef(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await getStandards({ skip: 0, limit: 4 });
        setStandards(data);
      } catch (err) {
        console.error("Failed to load featured standards:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  useEffect(() => {
    if (loading || standards.length === 0 || !sectionRef.current) return;

    const ctx = gsap.context(() => {
      gsap.fromTo(
        ".featured-card",
        { y: 35, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.6,
          stagger: 0.12,
          ease: "power3.out",
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top 75%",
          },
        }
      );
    }, sectionRef);

    return () => ctx.revert();
  }, [loading, standards]);

  return (
    <section ref={sectionRef} className="py-20 px-4 max-w-6xl mx-auto space-y-12 relative z-10">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between border-b border-slate-200 pb-6 gap-4">
        <div>
          <div className="text-xs font-mono font-bold text-blue-600 tracking-widest uppercase mb-1">
            EXPLORE CATALOG
          </div>
          <h2 className="text-3xl md:text-4xl font-extrabold text-slate-950 tracking-tight">
            Featured Indian Standards
          </h2>
        </div>

        <Link
          href="/standards"
          className="inline-flex items-center gap-2 font-semibold text-xs text-blue-600 hover:text-blue-800 transition-colors"
        >
          <span>View all standards</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* Grid of Cards */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-48 rounded-3xl bg-white border border-slate-200/80 animate-pulse p-6" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {standards.map((std) => (
            <div
              key={std.id}
              className="featured-card group bg-white border border-slate-200/80 rounded-3xl p-6 md:p-8 flex flex-col justify-between space-y-6 hover:border-blue-400 transition-all duration-300 hover:shadow-xl hover:shadow-blue-500/5 relative overflow-hidden"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-bold text-xs px-3 py-1 rounded-full bg-slate-900 text-white">
                    {std.standard_number}
                  </span>
                  {std.mandatory_certification && (
                    <span className="text-[10px] font-medium text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded-full flex items-center gap-1">
                      <ShieldCheck className="w-3 h-3 text-blue-600" />
                      BIS Certified
                    </span>
                  )}
                </div>

                <h3 className="text-xl font-bold text-slate-900 group-hover:text-blue-600 transition-colors line-clamp-2">
                  <Link href={`/standards/${encodeURIComponent(std.id)}`}>
                    {std.title}
                  </Link>
                </h3>

                {std.description && (
                  <p className="text-xs md:text-sm text-slate-600 line-clamp-2 leading-relaxed">
                    {std.description}
                  </p>
                )}
              </div>

              <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 font-medium">
                <span>{std.latest_version || "Latest Version"}</span>
                <Link
                  href={`/standards/${encodeURIComponent(std.id)}`}
                  className="inline-flex items-center gap-1 text-slate-900 group-hover:text-blue-600 transition-colors font-bold"
                >
                  <span>Explore</span>
                  <ArrowUpRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
