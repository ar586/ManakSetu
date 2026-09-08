"use client";

import { useEffect, useRef } from "react";
import gsap from "gsap";
import { Cpu } from "lucide-react";

export default function SearchLoading() {
  const containerRef = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.to(".loading-bar-inner", {
        x: "100%",
        duration: 1.4,
        repeat: -1,
        ease: "power2.inOut",
      });

      gsap.to(".loading-dot", {
        opacity: 0.2,
        duration: 0.5,
        stagger: 0.15,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
      });
    }, containerRef);

    return () => ctx.revert();
  }, []);

  return (
    <div
      ref={containerRef}
      className="w-full py-16 px-6 rounded-3xl bg-white border border-slate-200/80 shadow-sm flex flex-col items-center justify-center text-center space-y-6"
    >
      <div className="w-12 h-12 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 shadow-xs">
        <Cpu className="w-6 h-6 animate-pulse" />
      </div>

      <div className="space-y-2 max-w-md">
        <h3 className="text-xl font-bold text-slate-900 tracking-tight flex items-center justify-center gap-1.5">
          <span>Finding relevant standards</span>
          <span className="flex gap-0.5">
            <span className="loading-dot">.</span>
            <span className="loading-dot">.</span>
            <span className="loading-dot">.</span>
          </span>
        </h3>
        <p className="text-xs font-mono text-slate-400">
          RUNNING VECTOR SIMILARITY SCAN AGAINST INDIAN STANDARDS DATABASE
        </p>
      </div>

      {/* Progress Line */}
      <div className="w-64 h-1.5 rounded-full bg-slate-100 overflow-hidden relative border border-slate-200/60">
        <div className="loading-bar-inner absolute top-0 bottom-0 -left-full w-full bg-gradient-to-r from-blue-500 via-indigo-600 to-blue-500 rounded-full" />
      </div>
    </div>
  );
}
