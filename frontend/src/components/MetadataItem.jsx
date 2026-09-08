export default function MetadataItem({ label, value, icon: Icon }) {
  if (!value) return null;

  return (
    <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100 flex items-start gap-3">
      {Icon && (
        <div className="p-2 rounded-xl bg-white text-blue-600 border border-slate-200/60 shrink-0">
          <Icon className="w-4 h-4" />
        </div>
      )}
      <div className="space-y-0.5 min-w-0">
        <div className="text-[11px] font-mono font-medium text-slate-400 uppercase tracking-wider">
          {label}
        </div>
        <div className="text-sm font-bold text-slate-900 truncate">
          {value}
        </div>
      </div>
    </div>
  );
}
