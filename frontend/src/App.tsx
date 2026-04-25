import { useCallback, useEffect, useState } from "react";
import { Footprints, Flame, Heart, Timer, AlertTriangle } from "lucide-react";
import { api } from "./api/health";
import type { DashboardData, Suggestions } from "./api/health";
import { Header } from "./components/Header";
import { SleepCard } from "./components/SleepCard";
import { MetricCard } from "./components/MetricCard";
import { TrendChart } from "./components/TrendChart";
import { SuggestionPanel } from "./components/SuggestionPanel";
import { DataImport } from "./components/DataImport";
import { AlertBanner } from "./components/AlertBanner";

type Tab = "dashboard" | "import";

export default function App() {
  const [tab, setTab] = useState<Tab>("dashboard");
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [suggestions, setSuggestions] = useState<Suggestions | null>(null);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const d = await api.getDashboard();
      setData(d);
      setSuggestions(d.latest_suggestion);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  async function handleSyncEightSleep() {
    // Attempt sync using saved credentials; redirect to import tab if none
    setSyncing(true);
    try {
      await api.syncEightSleep("", "");
    } catch {
      setTab("import");
    } finally {
      setSyncing(false);
      loadDashboard();
    }
  }

  const metrics = data?.today.metrics ?? {};
  const trends = data?.trends;

  return (
    <div className="min-h-screen bg-slate-950">
      <Header onSync={handleSyncEightSleep} syncing={syncing} />

      {/* Tab bar */}
      <div className="max-w-7xl mx-auto px-4 pt-4 flex gap-1">
        {(["dashboard", "import"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium capitalize transition-colors ${
              tab === t
                ? "bg-slate-700 text-slate-100"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            {t === "import" ? "Connect Data" : t}
          </button>
        ))}
      </div>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {tab === "import" && (
          <div className="flex flex-col gap-6">
            <h1 className="text-xl font-semibold">Connect Your Data Sources</h1>
            <DataImport onImported={loadDashboard} />
          </div>
        )}

        {tab === "dashboard" && (
          <>
            {loading && (
              <div className="flex items-center justify-center h-64 text-slate-500">
                Loading dashboard…
              </div>
            )}

            {error && (
              <div className="rounded-xl bg-red-900/30 border border-red-700/50 p-4 flex items-center gap-3 text-red-300 text-sm">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                {error}
              </div>
            )}

            {!loading && !error && data && (
              <div className="flex flex-col gap-6">
                {/* Alerts */}
                {trends && trends.alerts.length > 0 && (
                  <AlertBanner alerts={trends.alerts} />
                )}

                {/* Top row: sleep + today's metrics */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                  <div className="lg:col-span-1">
                    <SleepCard session={data.today.sleep} />
                  </div>
                  <div className="lg:col-span-2 grid grid-cols-2 sm:grid-cols-4 gap-3 content-start">
                    <MetricCard
                      label="Steps"
                      value={metrics.steps ? Math.round(metrics.steps).toLocaleString() : null}
                      icon={<Footprints className="w-3 h-3" />}
                    />
                    <MetricCard
                      label="Active Cal"
                      value={metrics.active_calories ? Math.round(metrics.active_calories) : null}
                      unit="kcal"
                      icon={<Flame className="w-3 h-3" />}
                    />
                    <MetricCard
                      label="Resting HR"
                      value={metrics.resting_heart_rate ? Math.round(metrics.resting_heart_rate) : null}
                      unit="bpm"
                      icon={<Heart className="w-3 h-3" />}
                    />
                    <MetricCard
                      label="Workout"
                      value={metrics.workout_minutes ? Math.round(metrics.workout_minutes) : null}
                      unit="min"
                      icon={<Timer className="w-3 h-3" />}
                    />
                  </div>
                </div>

                {/* 7-day vs 30-day summary */}
                {trends && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <MetricCard
                      label="7d Avg Sleep"
                      value={trends["7_day"].avg_sleep_hours}
                      unit="h"
                      highlight
                    />
                    <MetricCard
                      label="7d Avg Score"
                      value={trends["7_day"].avg_sleep_score}
                      highlight
                    />
                    <MetricCard
                      label="7d Avg HRV"
                      value={trends["7_day"].avg_hrv}
                      unit="ms"
                      highlight
                    />
                    <MetricCard
                      label="7d Avg Steps"
                      value={trends["7_day"].avg_steps ? Math.round(trends["7_day"].avg_steps!).toLocaleString() : null}
                      highlight
                    />
                  </div>
                )}

                {/* Trend chart */}
                <TrendChart sessions={data.sleep_history} />

                {/* AI suggestions */}
                <SuggestionPanel
                  initial={suggestions}
                  onUpdate={(s) => setSuggestions(s)}
                />
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
