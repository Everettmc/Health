interface Props {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  highlight?: boolean;
  tone?: "default" | "warning" | "danger";
}

export function StatCard({ label, value, icon, highlight, tone = "default" }: Props) {
  const toneClasses =
    tone === "danger"
      ? "bg-red-900/30 border-red-700/40"
      : tone === "warning"
      ? "bg-amber-900/30 border-amber-700/40"
      : highlight
      ? "bg-brand-900/40 border-brand-700/50"
      : "bg-stone-800/60 border-stone-700/40";

  return (
    <div className={`rounded-xl p-4 flex flex-col gap-1 border ${toneClasses}`}>
      <div className="flex items-center gap-1.5 text-stone-400 text-xs uppercase tracking-wider">
        {icon}
        {label}
      </div>
      <div className="text-2xl font-bold tabular-nums">{value}</div>
    </div>
  );
}
