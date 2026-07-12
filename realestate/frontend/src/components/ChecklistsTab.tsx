import { useCallback, useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { api } from "../api/client";
import type { Checklist, ChecklistTemplate, Contact } from "../api/client";
import { TemplateIcon } from "./icons";
import { ChecklistCard } from "./ChecklistCard";
import { NewChecklistModal } from "./NewChecklistModal";

export function ChecklistsTab() {
  const [templates, setTemplates] = useState<ChecklistTemplate[]>([]);
  const [checklists, setChecklists] = useState<Checklist[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [pickedTemplate, setPickedTemplate] = useState<ChecklistTemplate | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const [t, c, ct] = await Promise.all([api.getTemplates(), api.getChecklists(), api.getContacts()]);
    setTemplates(t);
    setChecklists(c);
    setContacts(ct);
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCreate(data: { title: string; event_date: string; contact_id?: number }) {
    if (!pickedTemplate) return;
    await api.startChecklist({ template_id: pickedTemplate.id, ...data });
    setPickedTemplate(null);
    load();
  }

  async function toggleItem(checklist: Checklist, index: number) {
    const items = checklist.items.map((item, i) => (i === index ? { ...item, done: !item.done } : item));
    setChecklists((prev) => prev.map((c) => (c.id === checklist.id ? { ...c, items } : c)));
    await api.updateChecklist(checklist.id, { items });
  }

  async function complete(checklist: Checklist) {
    await api.updateChecklist(checklist.id, { status: "completed" });
    load();
  }

  async function reopen(checklist: Checklist) {
    await api.updateChecklist(checklist.id, { status: "active" });
    load();
  }

  async function remove(checklist: Checklist) {
    await api.deleteChecklist(checklist.id);
    load();
  }

  const active = checklists.filter((c) => c.status === "active");
  const completed = checklists.filter((c) => c.status === "completed");

  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-3">
        <h2 className="text-sm font-semibold text-stone-300">Start a checklist</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {templates.map((tpl) => (
            <button
              key={tpl.id}
              onClick={() => setPickedTemplate(tpl)}
              className="rounded-xl border border-stone-700/40 bg-stone-800/60 p-4 flex flex-col gap-2 items-start text-left hover:border-brand-600/60 hover:bg-stone-800 transition-colors"
            >
              <div className="w-8 h-8 rounded-lg bg-brand-900/50 flex items-center justify-center">
                <TemplateIcon name={tpl.icon} className="w-4 h-4 text-brand-500" />
              </div>
              <div className="text-sm font-medium">{tpl.name}</div>
              <div className="text-xs text-stone-500">{tpl.items.length} items</div>
            </button>
          ))}
        </div>
      </section>

      {!loading && active.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold text-stone-300">Active ({active.length})</h2>
          <div className="flex flex-col gap-2">
            {active.map((c) => (
              <ChecklistCard
                key={c.id}
                checklist={c}
                onToggleItem={toggleItem}
                onComplete={complete}
                onReopen={reopen}
                onDelete={remove}
                defaultOpen
              />
            ))}
          </div>
        </section>
      )}

      {!loading && completed.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold text-stone-300">Completed ({completed.length})</h2>
          <div className="flex flex-col gap-2">
            {completed.map((c) => (
              <ChecklistCard
                key={c.id}
                checklist={c}
                onToggleItem={toggleItem}
                onComplete={complete}
                onReopen={reopen}
                onDelete={remove}
              />
            ))}
          </div>
        </section>
      )}

      {!loading && checklists.length === 0 && (
        <div className="text-center text-stone-500 text-sm py-8 flex flex-col items-center gap-2">
          <Plus className="w-5 h-5" />
          Pick a template above to start your first checklist.
        </div>
      )}

      {pickedTemplate && (
        <NewChecklistModal
          template={pickedTemplate}
          contacts={contacts}
          onClose={() => setPickedTemplate(null)}
          onCreate={handleCreate}
        />
      )}
    </div>
  );
}
