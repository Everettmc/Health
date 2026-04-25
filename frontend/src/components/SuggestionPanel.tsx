import { useState } from "react";
import { Salad, Dumbbell, Moon, Brain, Zap, RefreshCw, ChevronDown, ChevronUp } from "lucide-react";
import type { Suggestions } from "../api/health";
import { api } from "../api/health";

interface Props {
  initial: Suggestions | null;
  onUpdate: (s: Suggestions) => void;
}

interface Card {
  key: keyof Suggestions;
  label: string;
  icon: React.ReactNode;
  color: string;
}

const CARDS: Card[] = [
  { key: "priority_focus", label: "Priority Focus", icon: <Zap className="w-4 h-4" />, color: "text-amber-400" },
  { key: "diet", label: "Nutrition", icon: <Salad className="w-4 h-4" />, color: "text-emerald-400" },
  { key: "workout", label: "Workout", icon: <Dumbbell className="w-4 h-4" />, color: "text-sky-400" },
  { key: "sleep", label: "Sleep", icon: <Moon className="w-4 h-4" />, color: "text-indigo-400" },
  { key: "insights", label: "Insights", icon: <Brain className="w-4 h-4" />, color: "text-purple-400" },
];

function SuggestionCard({ card, text }: { card: Card; text: string }) {
  const [expanded, setExpanded] = useState(true);
  return (
    <div className="rounded-xl bg-slate-800/60 border border-slate-700/40 overflow-hidden">
      <button
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-700/30 transition-colors"
        onClick={() => setExpanded((e) => !e)}
      >
        <span className={`flex items-center gap-2 font-medium text-sm ${card.color}`}>
          {card.icon}
          {card.label}
        </span>
        {expanded ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
      </button>
      {expanded && (
        <div className="px-4 pb-4 text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">{text}</div>
      )}
    </div>
  );
}

export function SuggestionPanel({ initial, onUpdate }: Props) {
  const [suggestions, setSuggestions] = useState<Suggestions | null>(initial);
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [streamText, setStreamText] = useState("");
  const [userContext, setUserContext] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setError(null);
    setStreamText("");
    setStreaming(true);
    setLoading(true);

    const cancel = api.streamSuggestions(
      userContext || undefined,
      (chunk) => setStreamText((t) => t + chunk),
      (s) => {
        setSuggestions(s);
        onUpdate(s);
        setStreaming(false);
        setLoading(false);
        setStreamText("");
      },
      (msg) => {
        setError(msg);
        setStreaming(false);
        setLoading(false);
      }
    );

    // Cancel not needed since component stays mounted, but keep reference
    return cancel;
  }

  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-base font-semibold text-slate-200">AI Health Coach</h2>
        <span className="text-xs text-slate-500">
          {suggestions?.date ? `Generated ${suggestions.date}` : "No suggestions yet"}
        </span>
      </div>

      <div className="mb-3 flex gap-2">
        <input
          type="text"
          placeholder="Optional context (e.g. 'ran a 10K yesterday')"
          value={userContext}
          onChange={(e) => setUserContext(e.target.value)}
          className="flex-1 rounded-lg bg-slate-800 border border-slate-700 px-3 py-2 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-sky-500"
        />
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-sm font-medium transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          {loading ? "Generating…" : "Generate"}
        </button>
      </div>

      {error && (
        <div className="mb-3 rounded-lg bg-red-900/30 border border-red-700/50 px-4 py-2 text-sm text-red-300">
          {error}
        </div>
      )}

      {streaming && streamText && (
        <div className="mb-3 rounded-xl bg-slate-800/60 border border-slate-700/40 p-4">
          <p className="text-xs text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse inline-block" />
            Claude is thinking…
          </p>
          <pre className="text-sm text-slate-300 whitespace-pre-wrap font-mono max-h-48 overflow-y-auto scrollbar-thin">
            {streamText}
          </pre>
        </div>
      )}

      {suggestions && !streaming && (
        <div className="flex flex-col gap-3">
          {CARDS.map((card) => (
            <SuggestionCard key={card.key} card={card} text={String(suggestions[card.key] ?? "")} />
          ))}
        </div>
      )}

      {!suggestions && !loading && (
        <div className="rounded-xl bg-slate-800/60 border border-slate-700/40 p-8 flex flex-col items-center gap-3 text-center">
          <Brain className="w-8 h-8 text-slate-600" />
          <p className="text-slate-500 text-sm">
            Click Generate to get personalized AI recommendations based on your health trends.
          </p>
        </div>
      )}
    </section>
  );
}
