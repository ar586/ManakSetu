"use client";

import { useEffect, useRef } from "react";
import gsap from "gsap";

export default function TechnicalBackground() {
  const containerRef = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Subtle ambient movement for technical crosshair elements
      gsap.to(".tech-floating-node", {
        y: "random(-12, 12)",
        x: "random(-8, 8)",
        duration: "random(4, 8)",
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
        stagger: 0.5,
      });
    }, containerRef);

    return () => ctx.revert();
  }, []);

  return (
    <div
      ref={containerRef}
      aria-hidden="true"
      className="fixed inset-0 pointer-events-none z-0 overflow-hidden bg-tech-grid opacity-60"
    >
      {/* Decorative technical line markings */}
      <div className="absolute top-0 left-12 bottom-0 w-[1px] bg-slate-200/60 hidden lg:block" />
      <div className="absolute top-0 right-12 bottom-0 w-[1px] bg-slate-200/60 hidden lg:block" />

      {/* Floating Technical Crosshairs */}
      <div className="tech-floating-node absolute top-[18%] left-[6%] text-[10px] font-mono text-slate-400 select-none hidden md:block">
        + [28.6139° N, 77.2090° E]
      </div>
      <div className="tech-floating-node absolute top-[35%] right-[5%] text-[10px] font-mono text-slate-400 select-none hidden md:block">
        SYS // BIS.INTEL.V1
      </div>
      <div className="tech-floating-node absolute top-[68%] left-[8%] text-[10px] font-mono text-slate-400 select-none hidden md:block">
        VECTOR.INDEX :: SEMANTIC.MATCH
      </div>
      <div className="tech-floating-node absolute top-[82%] right-[7%] text-[10px] font-mono text-slate-400 select-none hidden md:block">
        + STANDARDS.DB.ONLINE
      </div>

      {/* Radial soft gradient overlay */}
      <div className="absolute inset-0 bg-radial from-transparent via-slate-50/50 to-[#faf9f6] opacity-90" />
    </div>
  );
}
