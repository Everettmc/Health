const BASE = "/api";

export interface SleepSession {
  id: string;
  date: string;
  sleep_score: number | null;
  total_sleep_minutes: number | null;
  deep_sleep_minutes: number | null;
  rem_sleep_minutes: number | null;
  light_sleep_minutes: number | null;
  awake_minutes: number | null;
  hrv_avg: number | null;
  respiratory_rate: number | null;
  bed_temp_delta: number | null;
  toss_turns: number | null;
}

export interface HealthMetric {
  id: number;
  date: string;
  metric_type: string;
  value: number;
  unit: string;
  source: string;
}

export interface Suggestions {
  id?: number;
  date?: string;
  diet: string;
  workout: string;
  sleep: string;
  insights: string;
  priority_focus: string;
}

export interface Trends {
  "7_day": Record<string, number | null>;
  "30_day": Record<string, number | null>;
  alerts: string[];
}

export interface DashboardData {
  today: {
    date: string;
    sleep: SleepSession | null;
    metrics: Record<string, number>;
  };
  trends: Trends;
  latest_suggestion: Suggestions | null;
  sleep_history: SleepSession[];
  metrics_history: HealthMetric[];
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? res.statusText);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getDashboard: () => request<DashboardData>("/dashboard"),

  getSleep: (days = 30) => request<SleepSession[]>(`/sleep?days=${days}`),

  getMetrics: (days = 30, types?: string[]) => {
    const q = types ? `&types=${types.join(",")}` : "";
    return request<HealthMetric[]>(`/metrics?days=${days}${q}`);
  },

  getLatestSuggestion: () => request<Suggestions>("/suggestions/latest"),

  generateSuggestions: (userContext?: string) =>
    request<Suggestions>("/suggestions/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_context: userContext ?? null }),
    }),

  syncEightSleep: (email: string, password: string) =>
    request<{ status: string; message: string }>("/sync/eight-sleep", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    }),

  importAppleHealth: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ status: string; imported: number; message: string }>(
      "/sync/apple-health",
      { method: "POST", body: form }
    );
  },

  streamSuggestions(
    userContext: string | undefined,
    onChunk: (text: string) => void,
    onDone: (suggestions: Suggestions) => void,
    onError: (msg: string) => void
  ): () => void {
    const ctrl = new AbortController();

    (async () => {
      try {
        const res = await fetch(`${BASE}/suggestions/stream`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_context: userContext ?? null }),
          signal: ctrl.signal,
        });

        if (!res.ok || !res.body) {
          onError("Stream request failed");
          return;
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buf = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });

          const lines = buf.split("\n");
          buf = lines.pop() ?? "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const payload = JSON.parse(line.slice(6));
            if (payload.chunk) onChunk(payload.chunk);
            if (payload.done && payload.suggestions) onDone(payload.suggestions);
            if (payload.error) onError(payload.error);
          }
        }
      } catch (e) {
        if ((e as Error).name !== "AbortError") onError(String(e));
      }
    })();

    return () => ctrl.abort();
  },
};
