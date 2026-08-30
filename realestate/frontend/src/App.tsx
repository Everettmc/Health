import { useCallback, useEffect, useState } from "react";
import { api } from "./api/client";
import type { DailyBrief as DailyBriefData } from "./api/client";
import { Header } from "./components/Header";
import { DailyBrief } from "./components/DailyBrief";
import { ChecklistsTab } from "./components/ChecklistsTab";
import { ContactsTab } from "./components/ContactsTab";
import { NewsTab } from "./components/NewsTab";

type Tab = "brief" | "checklists" | "contacts" | "news";

const TABS: { id: Tab; label: string }[] = [
  { id: "brief", label: "Daily Brief" },
  { id: "checklists", label: "Checklists" },
  { id: "contacts", label: "Contacts" },
  { id: "news", label: "News" },
];

export default function App() {
  const [tab, setTab] = useState<Tab>("brief");
  const [brief, setBrief] = useState<DailyBriefData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadBrief = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getBrief();
      setBrief(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (tab === "brief") {
      loadBrief();
    }
  }, [tab, loadBrief]);

  async function handleRefresh() {
    setRefreshing(true);
    await loadBrief();
    setRefreshing(false);
  }

  return (
    <div className="min-h-screen bg-stone-950">
      <Header onRefresh={handleRefresh} refreshing={refreshing} />

      <div className="max-w-7xl mx-auto px-4 pt-4 flex gap-1">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              tab === t.id ? "bg-stone-700 text-stone-100" : "text-stone-500 hover:text-stone-300"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {tab === "brief" && (
          <>
            {loading && <div className="flex items-center justify-center h-64 text-stone-500">Loading your brief…</div>}
            {error && (
              <div className="rounded-xl bg-red-900/30 border border-red-700/50 p-4 text-red-300 text-sm">{error}</div>
            )}
            {!loading && !error && brief && (
              <DailyBrief
                brief={brief}
                onGoToChecklists={() => setTab("checklists")}
                onGoToContacts={() => setTab("contacts")}
                onGoToNews={() => setTab("news")}
              />
            )}
          </>
        )}

        {tab === "checklists" && <ChecklistsTab />}
        {tab === "contacts" && <ContactsTab />}
        {tab === "news" && <NewsTab />}
      </main>
    </div>
  );
}
