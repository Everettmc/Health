import type { SleepSession } from "../api/health";

interface Props {
  session: SleepSession | null;
}

function fmt(minutes: number | null): string {
  if (!minutes) return "—";
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${h}h ${m.toString().padStart(2, "0")}m`;
}

function scoreColor(score: number | null) {
  if (!score) return "text-slate-400";
  if (score >= 80) return "text-emerald-400";
  if (score >= 60) return "text-yellow-400";
  return "text-red-400";
}

export function SleepCard({ session }: Props) {
  if (!session) {
    return (
      <div className="rounded-xl bg-slate-800/60 border border-slate-700/40 p-5 flex items-center justify-center h-40">
        <p className="text-slate-500 text-sm">No sleep data for today</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-slate-800/60 border border-slate-700/40 p-5">
      <div className="flex items-start justify-between mb-4">
        <div>
          <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">Last Night</p>
          <p className="text-slate-300 text-sm">{session.date}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">Sleep Score</p>
          <p className={`text-4xl font-bold tabular-nums ${scoreColor(session.sleep_score)}`}>
            {session.sleep_score ?? "—"}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm">
        <div className="flex flex-col">
          <span className="text-slate-500 text-xs">Total Sleep</span>
          <span className="font-medium">{fmt(session.total_sleep_minutes)}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-slate-500 text-xs">Deep Sleep</span>
          <span className="font-medium text-indigo-400">{fmt(session.deep_sleep_minutes)}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-slate-500 text-xs">REM Sleep</span>
          <span className="font-medium text-purple-400">{fmt(session.rem_sleep_minutes)}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-slate-500 text-xs">HRV</span>
          <span className="font-medium">{session.hrv_avg != null ? `${session.hrv_avg} ms` : "—"}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-slate-500 text-xs">Resp. Rate</span>
          <span className="font-medium">
            {session.respiratory_rate != null ? `${session.respiratory_rate} brpm` : "—"}
          </span>
        </div>
        <div className="flex flex-col">
          <span className="text-slate-500 text-xs">Toss & Turns</span>
          <span className="font-medium">{session.toss_turns ?? "—"}</span>
        </div>
      </div>
    </div>
  );
}
