import { Activity } from "lucide-react";

interface Props {
  onSync: () => void;
  syncing: boolean;
}

export function Header({ onSync, syncing }: Props) {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-6 h-6 text-sky-400" />
          <span className="font-semibold text-lg tracking-tight">Health Dashboard</span>
        </div>
        <button
          onClick={onSync}
          disabled={syncing}
          className="px-4 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-sm font-medium transition-colors"
        >
          {syncing ? "Syncing…" : "Sync Eight Sleep"}
        </button>
      </div>
    </header>
  );
}
