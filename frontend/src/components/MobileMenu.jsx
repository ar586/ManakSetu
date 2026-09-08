"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import { X, ArrowUpRight, Search, BookOpen, Sparkles } from "lucide-react";
import gsap from "gsap";

export default function MobileMenu({ isOpen, onClose }) {
  const overlayRef = useRef(null);
  const menuBoxRef = useRef(null);

  useEffect(() => {
    if (!overlayRef.current || !menuBoxRef.current) return;

    if (isOpen) {
      document.body.style.overflow = "hidden";
      const ctx = gsap.context(() => {
        gsap.to(overlayRef.current, {
          opacity: 1,
          visibility: "visible",
          duration: 0.3,
          ease: "power2.out",
        });

        gsap.fromTo(
          ".mobile-menu-item",
          { y: 30, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            duration: 0.4,
            stagger: 0.08,
            ease: "power3.out",
            delay: 0.1,
          }
        );
      }, overlayRef);

      return () => ctx.revert();
    } else {
      document.body.style.overflow = "";
      gsap.to(overlayRef.current, {
        opacity: 0,
        duration: 0.25,
        ease: "power2.in",
        onComplete: () => {
          if (overlayRef.current) overlayRef.current.style.visibility = "hidden";
        },
      });
    }
  }, [isOpen]);

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-md opacity-0 invisible transition-all duration-300 flex flex-col justify-between p-6 md:hidden"
    >
      <div
        ref={menuBoxRef}
        className="bg-white border border-slate-200 rounded-3xl p-6 shadow-2xl flex flex-col justify-between h-full overflow-y-auto"
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-6 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <span className="font-extrabold tracking-tighter text-xl text-slate-900">
              MANAKSETU
            </span>
            <span className="text-[10px] font-mono font-medium px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
              AI INTEL
            </span>
          </div>

          <button
            onClick={onClose}
            aria-label="Close menu"
            className="p-2 rounded-full text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="py-8 flex flex-col gap-6">
          <Link
            href="/"
            onClick={onClose}
            className="mobile-menu-item flex items-center justify-between text-2xl font-bold text-slate-900 hover:text-blue-600 transition-colors"
          >
            <div className="flex items-center gap-3">
              <Search className="w-6 h-6 text-blue-600" />
              <span>Search</span>
            </div>
            <ArrowUpRight className="w-5 h-5 text-slate-400" />
          </Link>

          <Link
            href="/standards"
            onClick={onClose}
            className="mobile-menu-item flex items-center justify-between text-2xl font-bold text-slate-900 hover:text-blue-600 transition-colors"
          >
            <div className="flex items-center gap-3">
              <BookOpen className="w-6 h-6 text-blue-600" />
              <span>Standards</span>
            </div>
            <ArrowUpRight className="w-5 h-5 text-slate-400" />
          </Link>

          <Link
            href="/standards"
            onClick={onClose}
            className="mobile-menu-item flex items-center justify-between text-2xl font-bold text-slate-900 hover:text-blue-600 transition-colors"
          >
            <div className="flex items-center gap-3">
              <Sparkles className="w-6 h-6 text-blue-600" />
              <span>Explore All</span>
            </div>
            <ArrowUpRight className="w-5 h-5 text-slate-400" />
          </Link>
        </nav>

        {/* Footer info in menu */}
        <div className="pt-6 border-t border-slate-100 flex flex-col gap-4">
          <Link
            href="/standards"
            onClick={onClose}
            className="mobile-menu-item w-full py-4 rounded-2xl bg-blue-600 text-white font-semibold flex items-center justify-center gap-2 hover:bg-blue-700 transition-all shadow-lg shadow-blue-500/20"
          >
            <span>Explore Standards</span>
            <ArrowUpRight className="w-5 h-5" />
          </Link>
          
          <div className="text-xs text-center font-mono text-slate-400">
            MANAKSETU v1.0 • BUREAU OF INDIAN STANDARDS INTEL
          </div>
        </div>
      </div>
    </div>
  );
}
