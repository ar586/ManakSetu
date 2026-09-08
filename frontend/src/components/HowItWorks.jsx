"use client";

import { useEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { MessageSquareText, Cpu, CheckCircle2 } from "lucide-react";

gsap.registerPlugin(ScrollTrigger);

const STEPS = [
  {
    num: "01",
    title: "Describe",
    description: "Tell ManakSetu what you need using plain English, technical specs, or tender clauses.",
    icon: MessageSquareText,
  },
  {
    num: "02",
    title: "Discover",
    description: "AI vector embeddings scan and rank semantically relevant Indian Standards instantly.",
    icon: Cpu,
  },
  {
    num: "03",
    title: "Verify",
    description: "Explore version history, mandatory certification rules, and official download specifications.",
    icon: CheckCircle2,
  },
];

export default function HowItWorks() {
  const sectionRef = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.fromTo(
        ".how-step-card",
        { y: 45, opacity: 0 },
        {
          y: 0,
          opacity: 1,
          duration: 0.7,
          stagger: 0.2,
          ease: "power3.out",
          scrollTrigger: {
            trigger: sectionRef.current,
            start: "top 80%",
          },
        }
      );
    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section ref={sectionRef} className="py-24 px-4 max-w-6xl mx-auto space-y-14 relative z-10">
      {/* Section Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between border-b border-slate-200/80 pb-6 gap-4">
        <div className="space-y-2">
          <div className="text-xs font-mono font-bold text-blue-600 tracking-widest uppercase">
            HOW MANAKSETU WORKS
          </div>
          <h2 className="text-3xl md:text-5xl font-black text-slate-950 tracking-tight">
            From requirement <br className="hidden sm:inline" />
            <span className="text-slate-400">to standard.</span>
          </h2>
        </div>
        <p className="text-sm text-slate-500 max-w-md font-normal leading-relaxed">
          Replacing complex regulatory searches with conversational intelligence for engineering and architecture.
        </p>
      </div>

      {/* 3 Editorial Horizontal Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
        {STEPS.map((step, idx) => {
          const Icon = step.icon;
          return (
            <div
              key={idx}
              className="how-step-card bg-white border border-slate-200/80 rounded-3xl p-8 flex flex-col justify-between space-y-8 relative overflow-hidden group hover:border-blue-300 transition-all duration-300 hover:shadow-xl hover:shadow-blue-500/5"
            >
              {/* Top Row: Oversized Step Number */}
              <div className="flex items-start justify-between">
                <span className="font-editorial-num text-5xl md:text-6xl font-black text-slate-200 group-hover:text-blue-600 transition-colors duration-300">
                  {step.num}
                </span>
                <div className="p-3 rounded-2xl bg-slate-50 border border-slate-100 text-slate-700 group-hover:bg-blue-50 group-hover:text-blue-600 transition-colors">
                  <Icon className="w-6 h-6" />
                </div>
              </div>

              {/* Bottom Row: Content */}
              <div className="space-y-3 pt-4 border-t border-slate-100">
                <h3 className="text-2xl font-bold text-slate-900 tracking-tight">
                  {step.title}
                </h3>
                <p className="text-sm text-slate-600 leading-relaxed font-normal">
                  {step.description}
                </p>
              </div>

              {/* Bottom Accent Line */}
              <div className="absolute bottom-0 left-0 right-0 h-1 bg-blue-600 scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left" />
            </div>
          );
        })}
      </div>
    </section>
  );
}
