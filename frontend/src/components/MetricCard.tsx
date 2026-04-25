interface Props {
  label: string;
  value: string | number | null | undefined;
  unit?: string;
  icon?: React.ReactNode;
  trend?: "up" | "down" | "neutral";
  highlight?: boolean;
}

export function MetricCard({ label, value, unit, icon, highlight }: Props) {
  const isEmpty = value === null || value === undefined;

  return (
    <div
      className={`rounded-xl p-4 flex flex-col gap-1 ${
        highlight
          ? "bg-sky-900/40 border border-sky-700/50"
          : "bg-slate-800/60 border border-slate-700/40"
      }`}
    >
      <div className="flex items-center gap-1.5 text-slate-400 text-xs uppercase tracking-wider">
        {icon}
        {label}
      </div>
      <div className="text-2xl font-bold tabular-nums">
        {isEmpty ? (
          <span className="text-slate-600 text-base">—</span>
        ) : (
          <>
            {value}
            {unit && <span className="text-sm font-normal text-slate-400 ml-1">{unit}</span>}
          </>
        )}
      </div>
    </div>
  );
}
