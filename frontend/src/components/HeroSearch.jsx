"use client";

import { useState, useRef, useEffect } from "react";
import { Search, Sparkles, ArrowRight, CornerDownLeft, Upload, FileText, LoaderCircle } from "lucide-react";
import gsap from "gsap";
import { useRouter } from "next/navigation";
import { analyzeDocument } from "@/lib/api";

const EXAMPLE_QUERIES = [
  "Steel reinforcement requirements for residential construction",
  "Drinking water safety specifications IS 10500",
  "Earthquake resistant building design criteria",
  "Measurement of earthwork civil works",
];

export default function HeroSearch({ onSearch, isSearching }) {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState("text");
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadStep, setUploadStep] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const router = useRouter();
  const heroRef = useRef(null);
  const searchContainerRef = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

      tl.fromTo(
        ".hero-badge",
        { y: -15, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.5 }
      )
        .fromTo(
          ".hero-title-line",
          { y: 35, opacity: 0 },
          { y: 0, opacity: 1, duration: 0.7, stagger: 0.12 },
          "-=0.3"
        )
        .fromTo(
          ".hero-desc",
          { y: 20, opacity: 0 },
          { y: 0, opacity: 1, duration: 0.5 },
          "-=0.4"
        )
        .fromTo(
          searchContainerRef.current,
          { scale: 0.96, y: 25, opacity: 0 },
          { scale: 1, y: 0, opacity: 1, duration: 0.6 },
          "-=0.3"
        )
        .fromTo(
          ".hero-chip",
          { y: 15, opacity: 0 },
          { y: 0, opacity: 1, duration: 0.4, stagger: 0.06 },
          "-=0.3"
        );
    }, heroRef);

    return () => ctx.revert();
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim() || isSearching) return;
    onSearch(query.trim());
  };

  const handleChipClick = (example) => {
    setQuery(example);
    onSearch(example);
  };

  const handleDocumentSubmit = async (event) => {
    event.preventDefault();
    if (!file || uploading) return;
    setUploading(true);
    setUploadStep("Extracting text...");
    try {
      const result = await analyzeDocument(file);
      setUploadStep("Finding standards...");
      await new Promise((resolve) => setTimeout(resolve, 250));
      setUploadStep("Analyzing compliance...");
      sessionStorage.setItem("manaksetu-analysis", JSON.stringify(result));
      await new Promise((resolve) => setTimeout(resolve, 250));
      router.push("/analyze");
    } catch (error) {
      setUploadStep(error.message || "Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  const acceptFile = (candidate) => {
    if (!candidate) return;
    const allowed = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"];
    const validExtension = /\.(pdf|docx)$/i.test(candidate.name);
    if (!validExtension || (candidate.type && !allowed.includes(candidate.type))) {
      setFile(null);
      setUploadStep("Only valid PDF or DOCX files are supported.");
      return;
    }
    if (candidate.size > 15 * 1024 * 1024) {
      setFile(null);
      setUploadStep("The document must be smaller than 15 MB.");
      return;
    }
    setUploadStep("");
    setFile(candidate);
  };

  return (
    <section ref={heroRef} className="pt-32 pb-16 md:pt-40 md:pb-20 px-4 max-w-5xl mx-auto flex flex-col items-center text-center space-y-8 relative z-10">
      {/* Supporting Badge */}
      <div className="hero-badge inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-blue-50/80 border border-blue-200/80 text-blue-700 text-xs font-semibold shadow-xs">
        <Sparkles className="w-3.5 h-3.5 text-blue-600 animate-pulse" />
        <span>Powered by AI</span>
        <span className="w-1 h-1 rounded-full bg-blue-400" />
        <span className="text-[10px] font-mono opacity-80">SEMANTIC v1.0</span>
      </div>

      {/* Main Cinematic Heading */}
      <div className="space-y-2 max-w-4xl">
        <h1 className="hero-title-line font-hero text-slate-950 tracking-tight leading-[0.98]">
          Find the right <br className="hidden sm:inline" />
          <span className="bg-gradient-to-r from-slate-950 via-blue-950 to-blue-700 bg-clip-text text-transparent">
            Indian Standard.
          </span>
        </h1>
        
        <p className="hero-desc text-base sm:text-lg md:text-xl text-slate-600 font-normal max-w-2xl mx-auto pt-4 leading-relaxed">
          Search Indian Standards using natural language, tender descriptions, or technical requirements.
        </p>
      </div>

      {/* Primary Search Container (Visual Centerpiece) */}
      <div className="flex rounded-full border border-slate-200 bg-white/80 p-1 text-xs font-bold shadow-sm">
        <button type="button" onClick={() => setMode("text")} className={`rounded-full px-4 py-2 transition-colors ${mode === "text" ? "bg-slate-950 text-white" : "text-slate-500"}`}>Text Search</button>
        <button type="button" onClick={() => setMode("document")} className={`rounded-full px-4 py-2 transition-colors ${mode === "document" ? "bg-blue-600 text-white" : "text-slate-500"}`}>Document Upload</button>
      </div>

      {mode === "text" ? <form
        ref={searchContainerRef}
        onSubmit={handleSubmit}
        className="w-full max-w-3xl group bg-white border-2 border-slate-200 focus-within:border-blue-600 rounded-3xl p-3 md:p-4 shadow-xl shadow-slate-950/5 focus-within:shadow-2xl focus-within:shadow-blue-500/10 transition-all duration-300 relative overflow-hidden"
      >
        <div className="flex flex-col sm:flex-row items-center gap-3">
          {/* Input & Search Icon */}
          <div className="flex items-center gap-3 flex-1 w-full px-3 py-1">
            <Search className="w-6 h-6 text-slate-400 group-focus-within:text-blue-600 transition-colors shrink-0" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Describe what you're looking for..."
              className="w-full bg-transparent text-slate-900 placeholder:text-slate-400 font-medium text-base md:text-lg focus:outline-none py-2"
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={!query.trim() || isSearching}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 font-bold text-sm px-6 py-3.5 rounded-2xl bg-slate-900 text-white hover:bg-blue-600 disabled:opacity-50 disabled:hover:bg-slate-900 transition-all duration-200 cursor-pointer shadow-md hover:shadow-lg hover:shadow-blue-500/25 active:scale-95 shrink-0"
          >
            <span>Search</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {/* Bottom hint bar */}
        <div className="hidden sm:flex items-center justify-between px-3 pt-3 mt-2 border-t border-slate-100 text-[11px] text-slate-400 font-mono">
          <div className="flex items-center gap-1.5">
            <CornerDownLeft className="w-3 h-3 text-slate-400" />
            <span>Press Enter to search</span>
          </div>
          <span>AI Vector Index • 10,000+ BIS Specs</span>
        </div>
      </form> : <form onSubmit={handleDocumentSubmit} onDragOver={(event) => { event.preventDefault(); setIsDragging(true); }} onDragLeave={() => setIsDragging(false)} onDrop={(event) => { event.preventDefault(); setIsDragging(false); acceptFile(event.dataTransfer.files?.[0]); }} className={`w-full max-w-3xl rounded-3xl border-2 border-dashed p-8 shadow-xl shadow-blue-950/5 transition-colors ${isDragging ? "border-blue-600 bg-blue-100" : "border-blue-200 bg-blue-50/50"}`}>
        <label htmlFor="tender-file" className="flex cursor-pointer flex-col items-center gap-3 text-center">
          <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-blue-600 shadow-sm"><Upload className="h-5 w-5" /></span>
          <span className="text-sm font-bold text-slate-900">Drop a tender or project specification here</span>
          <span className="text-xs text-slate-500">Drop here or browse. PDF or DOCX, up to 15 MB</span>
          <input id="tender-file" type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" className="sr-only" onChange={(event) => acceptFile(event.target.files?.[0])} />
          {file && <span className="flex items-center gap-2 text-xs font-semibold text-blue-700"><FileText className="h-4 w-4" />{file.name}</span>}
        </label>
        <button type="submit" disabled={!file || uploading} className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-blue-600 px-5 py-3 text-sm font-bold text-white transition-colors hover:bg-blue-700 disabled:opacity-50">
          {uploading && <LoaderCircle className="h-4 w-4 animate-spin" />}{uploading ? uploadStep : "Analyze Tender"}
        </button>
        {uploadStep && !uploading && <p className="mt-3 text-xs text-rose-600">{uploadStep}</p>}
      </form>}

      {/* Suggested Prompt Chips */}
      <div className="w-full max-w-3xl flex flex-wrap items-center justify-center gap-2 pt-2">
        <span className="text-xs font-mono text-slate-400 mr-1 hidden sm:inline">Try asking:</span>
        {EXAMPLE_QUERIES.map((example, i) => (
          <button
            key={i}
            onClick={() => handleChipClick(example)}
            className="hero-chip text-xs font-medium text-slate-600 bg-white/80 hover:bg-blue-50 hover:text-blue-700 border border-slate-200/80 hover:border-blue-200 rounded-full px-3.5 py-1.5 transition-all shadow-2xs hover:shadow-xs cursor-pointer text-left truncate max-w-[280px] sm:max-w-none"
          >
            “{example}”
          </button>
        ))}
      </div>
    </section>
  );
}
