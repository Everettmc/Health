import { useState, useRef } from "react";
import { Upload, Wifi } from "lucide-react";
import { api } from "../api/health";

interface Props {
  onImported: () => void;
}

export function DataImport({ onImported }: Props) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [syncMsg, setSyncMsg] = useState<string | null>(null);
  const [importMsg, setImportMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function handleEightSleep() {
    if (!email || !password) return;
    setBusy(true);
    setSyncMsg(null);
    try {
      const res = await api.syncEightSleep(email, password);
      setSyncMsg(res.message);
      onImported();
    } catch (e) {
      setSyncMsg(`Error: ${(e as Error).message}`);
    } finally {
      setBusy(false);
    }
  }

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setImportMsg(null);
    try {
      const res = await api.importAppleHealth(file);
      setImportMsg(res.message);
      onImported();
    } catch (e) {
      setImportMsg(`Error: ${(e as Error).message}`);
    } finally {
      setBusy(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Eight Sleep */}
      <div className="rounded-xl bg-slate-800/60 border border-slate-700/40 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Wifi className="w-4 h-4 text-sky-400" />
          <span className="text-sm font-medium">Eight Sleep Sync</span>
        </div>
        <div className="flex flex-col gap-2 mb-3">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-sm placeholder-slate-600 focus:outline-none focus:border-sky-500"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-sm placeholder-slate-600 focus:outline-none focus:border-sky-500"
          />
        </div>
        <button
          onClick={handleEightSleep}
          disabled={busy || !email || !password}
          className="w-full py-2 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-sm font-medium transition-colors"
        >
          {busy ? "Connecting…" : "Connect & Sync"}
        </button>
        {syncMsg && (
          <p className="mt-2 text-xs text-slate-400">{syncMsg}</p>
        )}
      </div>

      {/* Apple Health */}
      <div className="rounded-xl bg-slate-800/60 border border-slate-700/40 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Upload className="w-4 h-4 text-emerald-400" />
          <span className="text-sm font-medium">Apple Health Import</span>
        </div>
        <p className="text-xs text-slate-500 mb-3">
          Export from Health app → Profile → Export All Health Data. Upload the .zip or export.xml.
        </p>
        <label className="block">
          <input
            ref={fileRef}
            type="file"
            accept=".xml,.zip"
            className="hidden"
            onChange={handleFileChange}
            disabled={busy}
          />
          <span className="flex items-center justify-center gap-2 w-full py-2 rounded-lg bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 text-sm font-medium transition-colors cursor-pointer">
            <Upload className="w-4 h-4" />
            {busy ? "Importing…" : "Choose File"}
          </span>
        </label>
        {importMsg && (
          <p className="mt-2 text-xs text-slate-400">{importMsg}</p>
        )}
      </div>
    </div>
  );
}
