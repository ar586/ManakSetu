"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export default function CTASection() {
  const containerRef = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo(
        ".cta-title-line",
        { y: 35, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.8,
          stagger: 0.15,
          ease: "power3.out",
          scrollTrigger: {
            trigger: containerRef.current,
            start: "top 80%",
          },
        }
      );
    }, containerRef);

    return () => ctx.revert();
  }, []);

  return (
    <section ref={containerRef} className="py-24 px-4 max-w-6xl mx-auto relative z-10">
      <div className="bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950 rounded-3xl p-10 md:p-16 text-white text-center flex flex-col items-center space-y-8 relative overflow-hidden shadow-2xl border border-slate-800">
        {/* Subtle Background Watermark Text */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 font-black text-8xl md:text-9xl text-white/[0.02] tracking-tighter pointer-events-none select-none uppercase">
          MANAKSETU
        </div>

        {/* Top Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-500/10 border border-blue-400/20 text-blue-300 text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5 text-blue-400 animate-pulse" />
          <span>Bureau of Indian Standards Intelligence</span>
        </div>

        {/* Heading */}
        <div className="space-y-2 max-w-3xl">
          <h2 className="cta-title-line text-4xl sm:text-5xl md:text-6xl font-black tracking-tight leading-tight">
            Stop searching. <br className="hidden sm:inline" />
            <span className="bg-gradient-to-r from-blue-200 via-white to-blue-400 bg-clip-text text-transparent">
              Start finding.
            </span>
          </h2>
          <p className="text-slate-400 text-base md:text-lg max-w-xl mx-auto pt-4 leading-relaxed font-normal">
            Access thousands of Indian Standards in seconds using natural language and semantic AI matching.
          </p>
        </div>

        {/* Button */}
        <div className="pt-4">
          <Link
            href="/standards"
            className="inline-flex items-center gap-3 font-bold text-sm px-8 py-4 rounded-full bg-blue-600 text-white hover:bg-blue-500 transition-all duration-300 shadow-xl shadow-blue-600/30 hover:shadow-blue-500/40 hover:-translate-y-0.5 active:scale-95"
          >
            <span>Explore Standards</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </section>
  );
}
