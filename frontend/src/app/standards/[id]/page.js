"use client";

import { use, useEffect, useState, useRef } from "react";
import Link from "next/link";
import { 
  ArrowLeft, 
  Download, 
  ShieldCheck, 
  Calendar, 
  FileCheck2, 
  CheckCircle2, 
  XCircle,
  FileQuestion,
  ExternalLink,
  MessageCircle,
  Send,
  Bot,
  User,
  Sparkles
} from "lucide-react";
import gsap from "gsap";
import MetadataItem from "@/components/MetadataItem";
import { chatWithStandard, getStandardById, getStandardSummary } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function StandardDetailPage({ params: paramsPromise }) {
  const params = use(paramsPromise);
  const id = params?.id ? decodeURIComponent(params.id) : null;

  const [standard, setStandard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [summary, setSummary] = useState("");
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [chatOpen, setChatOpen] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState([]);
  const [chatSources, setChatSources] = useState({});
  const [chatLoading, setChatLoading] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    async function loadStandard() {
      if (!id) return;
      setLoading(true);
      setNotFound(false);
      try {
        const data = await getStandardById(id);
        if (!data) {
          setNotFound(true);
        } else {
          setStandard(data);
        }
      } catch (err) {
        console.error("Failed to load standard detail:", err);
        setNotFound(true);
      } finally {
        setLoading(false);
      }
    }
    loadStandard();
  }, [id]);

  useEffect(() => {
    if (!id) return;
    getStandardSummary(id)
      .then((data) => setSummary(data.summary || "No AI summary is available yet."))
      .catch(() => setSummary("AI summary is unavailable for this standard right now."))
      .finally(() => setSummaryLoading(false));
  }, [id]);

  const sendChatMessage = async (event) => {
    event.preventDefault();
    const content = chatInput.trim();
    if (!content || chatLoading) return;
    const nextMessages = [...chatMessages, { role: "user", content }];
    setChatMessages(nextMessages);
    setChatInput("");
    setChatLoading(true);
    try {
      const data = await chatWithStandard(id, { chat_history: nextMessages, new_message: content });
      setChatMessages([...nextMessages, { role: "assistant", content: data.answer }]);
      setChatSources((previous) => ({ ...previous, [nextMessages.length]: data.sources || [] }));
    } catch (error) {
      setChatMessages([...nextMessages, { role: "assistant", content: error.message || "The document assistant is unavailable." }]);
    } finally {
      setChatLoading(false);
    }
  };

  useEffect(() => {
    if (loading || notFound || !standard || !containerRef.current) return;

    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

      tl.fromTo(".detail-anim-1", { y: -10, opacity: 0 }, { y: 0, opacity: 1, duration: 0.4 })
        .fromTo(".detail-anim-2", { y: 25, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5 }, "-=0.2")
        .fromTo(".detail-anim-3", { y: 25, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5 }, "-=0.3")
        .fromTo(".detail-anim-4", { y: 25, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5 }, "-=0.3");
    }, containerRef);

    return () => ctx.revert();
  }, [loading, notFound, standard]);

  // Loading State
  if (loading) {
    return (
      <div className="pt-36 pb-24 px-4 max-w-5xl mx-auto space-y-8 animate-pulse">
        <div className="h-6 w-48 bg-slate-200 rounded-full" />
        <div className="h-16 w-3/4 bg-slate-200 rounded-2xl" />
        <div className="h-32 w-full bg-slate-200 rounded-3xl" />
      </div>
    );
  }

  // 404 Custom State
  if (notFound || !standard) {
    return (
      <div className="pt-36 pb-24 px-4 max-w-3xl mx-auto text-center space-y-6">
        <div className="w-16 h-16 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600 mx-auto">
          <FileQuestion className="w-8 h-8" />
        </div>

        <div className="space-y-2">
          <h1 className="text-3xl font-bold text-slate-950">Standard not found.</h1>
          <p className="text-slate-500 text-sm">
            The standard with ID “{id}” could not be located in the ManakSetu database.
          </p>
        </div>

        <div>
          <Link
            href="/standards"
            className="inline-flex items-center gap-2 font-semibold text-xs px-6 py-3 rounded-full bg-slate-900 text-white hover:bg-blue-600 transition-all shadow-md"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Standards</span>
          </Link>
        </div>
      </div>
    );
  }

  const formattedDate = formatDate(standard.publication_date);

  return (
    <div ref={containerRef} className="pt-32 pb-24 px-4 max-w-6xl mx-auto space-y-10 relative z-10">
      {/* Breadcrumb Navigation */}
      <div className="detail-anim-1 flex items-center gap-2 text-xs font-mono text-slate-500">
        <Link href="/standards" className="hover:text-blue-600 transition-colors flex items-center gap-1">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Standards</span>
        </Link>
        <span>/</span>
        <span className="text-slate-950 font-bold">{standard.standard_number}</span>
      </div>

      {/* Main Editorial Hero */}
      <div className="detail-anim-2 space-y-4 border-b border-slate-200/80 pb-8">
        <div className="flex flex-wrap items-center gap-3">
          <span className="font-mono font-black text-sm px-4 py-1.5 rounded-full bg-slate-950 text-white tracking-wide">
            {standard.standard_number}
          </span>

          {standard.is_active ? (
            <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-full flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              Active Standard
            </span>
          ) : (
            <span className="text-xs font-semibold text-slate-600 bg-slate-100 border border-slate-200 px-3 py-1 rounded-full flex items-center gap-1.5">
              <XCircle className="w-4 h-4 text-slate-400" />
              Inactive Standard
            </span>
          )}
        </div>

        <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-slate-950 tracking-tight leading-tight">
          {standard.title}
        </h1>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Description */}
        <div className="detail-anim-3 lg:col-span-2 space-y-6">
          <div className="bg-white border border-slate-200/80 rounded-3xl p-8 space-y-4 shadow-sm">
            <h2 className="text-sm font-mono font-bold text-slate-400 uppercase tracking-widest">
              SPECIFICATION OVERVIEW
            </h2>

            {standard.description ? (
              <p className="text-base md:text-lg text-slate-700 leading-relaxed font-normal">
                {standard.description}
              </p>
            ) : (
              <p className="text-sm text-slate-400 italic">
                No official description text available for this standard.
              </p>
            )}

            <div className="mt-8 border-t border-slate-100 pt-6">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-4 h-4 text-blue-600" />
                <h2 className="text-sm font-mono font-bold text-blue-700 uppercase tracking-widest">AI SUMMARY</h2>
              </div>
              {summaryLoading ? (
                <div className="space-y-3 animate-pulse"><div className="h-3 bg-slate-200 rounded w-11/12" /><div className="h-3 bg-slate-200 rounded w-4/5" /><div className="h-3 bg-slate-200 rounded w-3/5" /></div>
              ) : <div className="whitespace-pre-line text-sm text-slate-700 leading-relaxed">{summary}</div>}
            </div>
          </div>

          {/* Download CTA if download_link exists */}
          {standard.download_link && (
            <div className="p-8 rounded-3xl bg-blue-50/70 border border-blue-200 flex flex-col sm:flex-row sm:items-center justify-between gap-6">
              <div className="space-y-1">
                <h3 className="font-bold text-slate-900 text-lg">Official Specification File</h3>
                <p className="text-xs text-slate-600">Access full document specifications on official BIS portal.</p>
              </div>

              <a
                href={standard.download_link}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-2 font-bold text-xs px-6 py-3.5 rounded-2xl bg-blue-600 text-white hover:bg-blue-700 transition-all shadow-md shadow-blue-500/20 shrink-0"
              >
                <Download className="w-4 h-4" />
                <span>Download Standard</span>
                <ExternalLink className="w-3.5 h-3.5 opacity-80" />
              </a>
            </div>
          )}
        </div>

        {/* Right Column: Standard Information Grid */}
        <div className="detail-anim-4 space-y-6">
          <div className="bg-white border border-slate-200/80 rounded-3xl p-6 space-y-6 shadow-sm">
            <h2 className="text-xs font-mono font-bold text-slate-400 uppercase tracking-widest pb-3 border-b border-slate-100">
              STANDARD METADATA
            </h2>

            <div className="space-y-3">
              <MetadataItem
                label="Standard Number"
                value={standard.standard_number}
                icon={FileCheck2}
              />

              <MetadataItem
                label="Latest Version"
                value={standard.latest_version}
                icon={FileCheck2}
              />

              <MetadataItem
                label="Publication Date"
                value={formattedDate}
                icon={Calendar}
              />

              <MetadataItem
                label="Mandatory Certification"
                value={standard.mandatory_certification}
                icon={ShieldCheck}
              />

              <MetadataItem
                label="Status"
                value={standard.is_active ? "Active Code of Practice" : "Superseded / Inactive"}
                icon={standard.is_active ? CheckCircle2 : XCircle}
              />
            </div>
          </div>
        </div>
      </div>

      <button type="button" onClick={() => setChatOpen((open) => !open)} className="fixed bottom-6 right-6 z-30 inline-flex items-center gap-2 rounded-full bg-slate-950 px-5 py-3 text-sm font-bold text-white shadow-xl hover:bg-blue-600 transition-colors">
        <MessageCircle className="w-4 h-4" /> Chat with Document
      </button>

      {chatOpen && <section className="fixed bottom-20 right-6 z-30 w-[min(92vw,380px)] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl">
        <header className="flex items-center justify-between bg-slate-950 px-4 py-3 text-white"><span className="flex items-center gap-2 text-sm font-bold"><Bot className="w-4 h-4" /> Standard assistant</span><button type="button" onClick={() => setChatOpen(false)} aria-label="Close chat">×</button></header>
        <div className="max-h-80 space-y-3 overflow-y-auto p-4">
          {chatMessages.length === 0 && <p className="text-xs text-slate-500">Ask a question about this standard.</p>}
          {chatMessages.map((message, index) => <div key={`${message.role}-${index}`} className={`flex gap-2 text-sm ${message.role === "user" ? "justify-end" : "justify-start"}`}><span className={`max-w-[85%] rounded-xl px-3 py-2 ${message.role === "user" ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-700"}`}>{message.role === "user" ? <User className="mr-1 inline h-3 w-3" /> : <Bot className="mr-1 inline h-3 w-3" />}{message.content}{message.role === "assistant" && chatSources[index]?.length > 0 && <span className="mt-2 block border-t border-slate-300 pt-2 text-[10px] text-slate-500">Sources: {chatSources[index].map((source, sourceIndex) => <span key={sourceIndex} className="mr-2">{[source.standard_number || source.standard_id, source.source_document, source.section && `section ${source.section}`, source.clause && `clause ${source.clause}`, source.page && `page ${source.page}`].filter(Boolean).join(" · ")}</span>)}</span>}</span></div>)}
          {chatLoading && <p className="text-xs text-slate-400 animate-pulse">Reading the standard...</p>}
        </div>
        <form onSubmit={sendChatMessage} className="flex gap-2 border-t border-slate-100 p-3"><input value={chatInput} onChange={(event) => setChatInput(event.target.value)} placeholder="Ask about a clause..." className="min-w-0 flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-500" /><button type="submit" aria-label="Send message" className="rounded-lg bg-blue-600 p-2 text-white disabled:opacity-50" disabled={chatLoading || !chatInput.trim()}><Send className="h-4 w-4" /></button></form>
      </section>}
    </div>
  );
}
