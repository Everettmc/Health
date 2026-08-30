import { useState } from "react";
import { X } from "lucide-react";
import type { ChecklistTemplate, Contact } from "../api/client";

interface Props {
  template: ChecklistTemplate;
  contacts: Contact[];
  onClose: () => void;
  onCreate: (data: { title: string; event_date: string; contact_id?: number }) => void;
}

export function NewChecklistModal({ template, contacts, onClose, onCreate }: Props) {
  const [title, setTitle] = useState(template.name);
  const [eventDate, setEventDate] = useState(new Date().toISOString().slice(0, 10));
  const [contactId, setContactId] = useState<string>("");

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-stone-900 border border-stone-700 rounded-xl w-full max-w-md p-5 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold">Start "{template.name}"</h2>
          <button onClick={onClose} className="text-stone-500 hover:text-stone-200">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs text-stone-400">Title</label>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="bg-stone-800 border border-stone-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-600"
            placeholder="e.g. 123 Main St showing"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs text-stone-400">Date</label>
          <input
            type="date"
            value={eventDate}
            onChange={(e) => setEventDate(e.target.value)}
            className="bg-stone-800 border border-stone-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-600"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs text-stone-400">Link to contact (optional)</label>
          <select
            value={contactId}
            onChange={(e) => setContactId(e.target.value)}
            className="bg-stone-800 border border-stone-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-600"
          >
            <option value="">None</option>
            {contacts.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex justify-end gap-2 pt-1">
          <button
            onClick={onClose}
            className="text-xs px-3 py-2 rounded-lg text-stone-400 hover:text-stone-200 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={() =>
              onCreate({
                title: title.trim() || template.name,
                event_date: eventDate,
                contact_id: contactId ? Number(contactId) : undefined,
              })
            }
            className="text-xs px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 transition-colors font-medium"
          >
            Start checklist
          </button>
        </div>
      </div>
    </div>
  );
}
