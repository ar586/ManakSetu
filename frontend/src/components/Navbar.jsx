"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { Menu, ArrowRight } from "lucide-react";
import gsap from "gsap";
import MobileMenu from "@/components/MobileMenu";

export default function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navRef = useRef(null);

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 20) {
        setIsScrolled(true);
      } else {
        setIsScrolled(false);
      }
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    if (!navRef.current) return;
    if (isScrolled) {
      gsap.to(navRef.current, {
        backgroundColor: "rgba(255, 255, 255, 0.85)",
        borderColor: "rgba(226, 232, 240, 0.8)",
        backdropFilter: "blur(12px)",
        boxShadow: "0 4px 20px -2px rgba(15, 23, 42, 0.03)",
        paddingTop: "0.75rem",
        paddingBottom: "0.75rem",
        duration: 0.3,
        ease: "power2.out",
      });
    } else {
      gsap.to(navRef.current, {
        backgroundColor: "rgba(250, 249, 246, 0)",
        borderColor: "rgba(226, 232, 240, 0)",
        backdropFilter: "blur(0px)",
        boxShadow: "0 0 0 0 rgba(0, 0, 0, 0)",
        paddingTop: "1.25rem",
        paddingBottom: "1.25rem",
        duration: 0.3,
        ease: "power2.out",
      });
    }
  }, [isScrolled]);

  return (
    <>
      <header
        ref={navRef}
        className="fixed top-0 left-0 right-0 z-40 px-4 md:px-8 border-b border-transparent transition-all duration-300"
      >
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Left Wordmark */}
          <Link href="/" className="group flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-slate-900 text-white flex items-center justify-center font-extrabold text-sm tracking-tighter group-hover:bg-blue-600 transition-colors">
              M
            </div>
            <div className="flex flex-col">
              <span className="font-black text-lg tracking-tighter text-slate-950 group-hover:text-blue-600 transition-colors">
                MANAKSETU
              </span>
              <span className="text-[9px] font-mono text-slate-400 tracking-wider -mt-1 hidden sm:inline">
                INDIAN STANDARDS AI
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
            <Link
              href="/"
              className="hover:text-slate-950 transition-colors relative py-1 after:content-[''] after:absolute after:bottom-0 after:left-0 after:right-0 after:h-[2px] after:bg-blue-600 after:scale-x-0 hover:after:scale-x-100 after:transition-transform"
            >
              Search
            </Link>
            <Link
              href="/standards"
              className="hover:text-slate-950 transition-colors relative py-1 after:content-[''] after:absolute after:bottom-0 after:left-0 after:right-0 after:h-[2px] after:bg-blue-600 after:scale-x-0 hover:after:scale-x-100 after:transition-transform"
            >
              Standards
            </Link>
          </nav>

          {/* Primary CTA */}
          <div className="hidden md:flex items-center gap-4">
            <Link
              href="/standards"
              className="inline-flex items-center gap-2 text-xs font-semibold px-4 py-2.5 rounded-full bg-slate-900 text-white hover:bg-blue-600 transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/20 active:scale-95"
            >
              <span>Explore Standards</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Mobile Hamburger Menu Toggle */}
          <button
            onClick={() => setMobileMenuOpen(true)}
            aria-label="Open navigation menu"
            className="md:hidden p-2.5 rounded-xl border border-slate-200 bg-white/80 text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Mobile Animated Overlay */}
      <MobileMenu
        isOpen={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
      />
    </>
  );
}
