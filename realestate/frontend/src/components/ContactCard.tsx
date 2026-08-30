import { useEffect, useState } from "react";
import { ChevronDown, ChevronUp, Mail, Phone, Pencil, Trash2, Send } from "lucide-react";
import { api } from "../api/client";
import type { Contact, ContactActivity } from "../api/client";

const TYPE_COLORS: Record<string, string> = {
  buyer: "bg-sky-900/50 text-sky-400",
  seller: "bg-purple-900/50 text-purple-400",
  lead: "bg-amber-900/50 text-amber-400",
  past_client: "bg-emerald-900/50 text-emerald-400",
  vendor: "bg-stone-700/50 text-stone-400",
};

const STATUS_COLORS: Record<string, string> = {
  new: "bg-stone-700/50 text-stone-300",
  active: "bg-sky-900/50 text-sky-400",
  nurturing: "bg-amber-900/50 text-amber-400",
  under_contract: "bg-purple-900/50 text-purple-400",
  closed: "bg-emerald-900/50 text-emerald-400",
  lost: "bg-red-900/50 text-red-400",
};

const ACTIVITY_TYPES = ["call", "text", "email", "showing", "meeting", "note"];

interface Props {
  contact: Contact;
  onEdit: (contact: Contact) => void;
  onDelete: (contact: Contact) => void;
  onChanged: () => void;
}

export function ContactCard({ contact, onEdit, onDelete, onChanged }: Props) {
  const [open, setOpen] = useState(false);
  const [activities, setActivities] = useState<ContactActivity[]>([]);
  const [activityType, setActivityType] = useState("call");
  const [note, setNote] = useState("");

  useEffect(() => {
    if (open) {
      api.getActivities(contact.id).then(setActivities);
    }
  }, [open, contact.id]);

  const today = new Date().toISOString().slice(0, 10);
  const isOverdue = !!contact.follow_up_date && contact.follow_up_date < today;
  const isDueToday = contact.follow_up_date === today;

  async function logActivity() {
    if (!note.trim() && activityType === "note") return;
    await api.addActivity(contact.id, { activity_type: activityType, notes: note.trim() || undefined });
    setNote("");
    const updated = await api.getActivities(contact.id);
    setActivities(updated);
    onChanged();
  }

  return (
    <div className="rounded-xl border border-stone-700/40 bg-stone-800/60 overflow-hidden">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center justify-between gap-3 px-4 py-3 text-left">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-sm">{contact.name}</span>
            <span className={`text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded ${TYPE_COLORS[contact.type]}`}>
              {contact.type.replace("_", " ")}
            </span>
            <span className={`text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded ${STATUS_COLORS[contact.status]}`}>
              {contact.status.replace("_", " ")}
            </span>
          </div>
          <div className="text-xs text-stone-500 flex items-center gap-3 mt-1 flex-wrap">
            {contact.phone && (
              <span className="flex items-center gap-1">
                <Phone className="w-3 h-3" /> {contact.phone}
              </span>
            )}
            {contact.email && (
              <span className="flex items-center gap-1">
                <Mail className="w-3 h-3" /> {contact.email}
              </span>
            )}
            {contact.follow_up_date && (
              <span className={isOverdue ? "text-red-400" : isDueToday ? "text-amber-400" : ""}>
                Follow up {contact.follow_up_date}
              </span>
            )}
          </div>
        </div>
        {open ? <ChevronUp className="w-4 h-4 text-stone-500 shrink-0" /> : <ChevronDown className="w-4 h-4 text-stone-500 shrink-0" />}
      </button>

      {open && (
        <div className="px-4 pb-4 flex flex-col gap-3 border-t border-stone-700/40 pt-3">
          {(contact.address || contact.source || contact.notes) && (
            <div className="text-xs text-stone-400 flex flex-col gap-1">
              {contact.address && <div>{contact.address}</div>}
              {contact.source && <div>Source: {contact.source}</div>}
              {contact.notes && <div className="text-stone-300">{contact.notes}</div>}
            </div>
          )}

          <div className="flex items-center gap-2">
            <select
              value={activityType}
              onChange={(e) => setActivityType(e.target.value)}
              className="bg-stone-800 border border-stone-700 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:border-brand-600"
            >
              {ACTIVITY_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
            <input
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Quick note..."
              className="flex-1 bg-stone-800 border border-stone-700 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:border-brand-600"
              onKeyDown={(e) => e.key === "Enter" && logActivity()}
            />
            <button onClick={logActivity} className="p-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 transition-colors">
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>

          {activities.length > 0 && (
            <div className="flex flex-col gap-1.5 max-h-40 overflow-y-auto scrollbar-thin">
              {activities.map((a) => (
                <div key={a.id} className="text-xs flex items-start gap-2">
                  <span className="text-stone-500 shrink-0">{new Date(a.created_at).toLocaleDateString()}</span>
                  <span className="text-stone-400 capitalize shrink-0">{a.activity_type}:</span>
                  <span className="text-stone-300">{a.notes}</span>
                </div>
              ))}
            </div>
          )}

          <div className="flex items-center justify-between pt-2 border-t border-stone-700/40">
            <button
              onClick={() => onDelete(contact)}
              className="flex items-center gap-1 text-xs text-stone-500 hover:text-red-400 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Delete
            </button>
            <button
              onClick={() => onEdit(contact)}
              className="flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-stone-700 hover:bg-stone-600 transition-colors"
            >
              <Pencil className="w-3.5 h-3.5" />
              Edit
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
