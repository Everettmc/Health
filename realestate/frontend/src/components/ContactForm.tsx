import { useState } from "react";
import { X } from "lucide-react";
import type { Contact, ContactStatus, ContactType } from "../api/client";

interface Props {
  contact?: Contact;
  onClose: () => void;
  onSave: (data: Partial<Contact>) => void;
}

const TYPES: ContactType[] = ["buyer", "seller", "lead", "past_client", "vendor"];
const STATUSES: ContactStatus[] = ["new", "active", "nurturing", "under_contract", "closed", "lost"];

export function ContactForm({ contact, onClose, onSave }: Props) {
  const [form, setForm] = useState<Partial<Contact>>(
    contact ?? { name: "", type: "lead", status: "new" }
  );

  function set<K extends keyof Contact>(key: K, value: Contact[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-stone-900 border border-stone-700 rounded-xl w-full max-w-lg p-5 flex flex-col gap-4 max-h-[90vh] overflow-y-auto scrollbar-thin">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold">{contact ? "Edit contact" : "New contact"}</h2>
          <button onClick={onClose} className="text-stone-500 hover:text-stone-200">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <Field label="Name" full>
            <input
              value={form.name || ""}
              onChange={(e) => set("name", e.target.value)}
              className="input"
              placeholder="Jane Smith"
            />
          </Field>
          <Field label="Phone">
            <input
              value={form.phone || ""}
              onChange={(e) => set("phone", e.target.value)}
              className="input"
              placeholder="(555) 555-1234"
            />
          </Field>
          <Field label="Email">
            <input
              value={form.email || ""}
              onChange={(e) => set("email", e.target.value)}
              className="input"
              placeholder="jane@email.com"
            />
          </Field>
          <Field label="Type">
            <select value={form.type || "lead"} onChange={(e) => set("type", e.target.value as ContactType)} className="input">
              {TYPES.map((t) => (
                <option key={t} value={t}>
                  {t.replace("_", " ")}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Status">
            <select value={form.status || "new"} onChange={(e) => set("status", e.target.value as ContactStatus)} className="input">
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s.replace("_", " ")}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Address" full>
            <input
              value={form.address || ""}
              onChange={(e) => set("address", e.target.value)}
              className="input"
              placeholder="123 Main St"
            />
          </Field>
          <Field label="Source">
            <input
              value={form.source || ""}
              onChange={(e) => set("source", e.target.value)}
              className="input"
              placeholder="Referral, Zillow, Open House..."
            />
          </Field>
          <Field label="Follow-up date">
            <input
              type="date"
              value={form.follow_up_date || ""}
              onChange={(e) => set("follow_up_date", e.target.value)}
              className="input"
            />
          </Field>
          <Field label="Notes" full>
            <textarea
              value={form.notes || ""}
              onChange={(e) => set("notes", e.target.value)}
              className="input min-h-[70px] resize-none"
              placeholder="Wants a 3bd/2ba under $450k in the school district..."
            />
          </Field>
        </div>

        <div className="flex justify-end gap-2 pt-1">
          <button onClick={onClose} className="text-xs px-3 py-2 rounded-lg text-stone-400 hover:text-stone-200 transition-colors">
            Cancel
          </button>
          <button
            onClick={() => onSave(form)}
            disabled={!form.name?.trim()}
            className="text-xs px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 transition-colors font-medium disabled:opacity-40"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children, full }: { label: string; children: React.ReactNode; full?: boolean }) {
  return (
    <div className={`flex flex-col gap-1.5 ${full ? "col-span-2" : ""}`}>
      <label className="text-xs text-stone-400">{label}</label>
      {children}
    </div>
  );
}
