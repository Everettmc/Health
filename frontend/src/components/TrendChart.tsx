import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { SleepSession } from "../api/health";

interface Props {
  sessions: SleepSession[];
}

export function TrendChart({ sessions }: Props) {
  const data = [...sessions]
    .reverse()
    .slice(-21)
    .map((s) => ({
      date: s.date.slice(5), // MM-DD
      score: s.sleep_score,
      hrv: s.hrv_avg,
      deepMin: s.deep_sleep_minutes,
      remMin: s.rem_sleep_minutes,
    }));

  if (data.length === 0) {
    return (
      <div className="rounded-xl bg-slate-800/60 border border-slate-700/40 p-5 flex items-center justify-center h-52">
        <p className="text-slate-500 text-sm">No trend data yet</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-slate-800/60 border border-slate-700/40 p-5">
      <p className="text-sm font-medium text-slate-300 mb-4">Sleep Trends — Last 21 Days</p>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="date" tick={{ fill: "#94a3b8", fontSize: 11 }} />
          <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
          <Tooltip
            contentStyle={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 8 }}
            labelStyle={{ color: "#e2e8f0" }}
          />
          <Legend wrapperStyle={{ fontSize: 12, color: "#94a3b8" }} />
          <Line
            type="monotone"
            dataKey="score"
            name="Sleep Score"
            stroke="#38bdf8"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="hrv"
            name="HRV (ms)"
            stroke="#a78bfa"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
