import { useState } from "react";
import { Check, ChevronDown, ChevronUp, Trash2 } from "lucide-react";
import type { Checklist } from "../api/client";

interface Props {
  checklist: Checklist;
  onToggleItem: (checklist: Checklist, index: number) => void;
  onComplete: (checklist: Checklist) => void;
  onReopen: (checklist: Checklist) => void;
  onDelete: (checklist: Checklist) => void;
  defaultOpen?: boolean;
}

export function ChecklistCard({ checklist, onToggleItem, onComplete, onReopen, onDelete, defaultOpen }: Props) {
  const [open, setOpen] = useState(!!defaultOpen);
  const done = checklist.items.filter((i) => i.done).length;
  const total = checklist.items.length;
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;
  const isCompleted = checklist.status === "completed";

  return (
    <div className="rounded-xl border border-stone-700/40 bg-stone-800/60 overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between gap-3 px-4 py-3 text-left"
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-sm truncate">{checklist.title}</span>
            {isCompleted && (
              <span className="text-[10px] uppercase tracking-wide bg-emerald-900/50 text-emerald-400 px-1.5 py-0.5 rounded">
                Done
              </span>
            )}
          </div>
          <div className="text-xs text-stone-500 flex items-center gap-2 mt-0.5">
            <span>{checklist.template_name}</span>
            <span>&middot;</span>
            <span>{checklist.event_date}</span>
          </div>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <div className="w-20 h-1.5 rounded-full bg-stone-700 overflow-hidden hidden sm:block">
            <div
              className={`h-full rounded-full ${isCompleted ? "bg-emerald-500" : "bg-brand-500"}`}
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="text-xs text-stone-400 tabular-nums w-10 text-right">
            {done}/{total}
          </span>
          {open ? <ChevronUp className="w-4 h-4 text-stone-500" /> : <ChevronDown className="w-4 h-4 text-stone-500" />}
        </div>
      </button>

      {open && (
        <div className="px-4 pb-4 flex flex-col gap-2 border-t border-stone-700/40 pt-3">
          {checklist.items.map((item, idx) => (
            <label
              key={idx}
              className="flex items-start gap-2.5 text-sm cursor-pointer group"
            >
              <span
                onClick={(e) => {
                  e.preventDefault();
                  onToggleItem(checklist, idx);
                }}
                className={`mt-0.5 shrink-0 w-4 h-4 rounded border flex items-center justify-center transition-colors ${
                  item.done
                    ? "bg-brand-600 border-brand-600"
                    : "border-stone-600 group-hover:border-stone-400"
                }`}
              >
                {item.done && <Check className="w-3 h-3 text-stone-50" />}
              </span>
              <span className={item.done ? "text-stone-500 line-through" : "text-stone-200"}>{item.text}</span>
            </label>
          ))}

          <div className="flex items-center justify-between pt-2 mt-1 border-t border-stone-700/40">
            <button
              onClick={() => onDelete(checklist)}
              className="flex items-center gap-1 text-xs text-stone-500 hover:text-red-400 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              Delete
            </button>
            {isCompleted ? (
              <button
                onClick={() => onReopen(checklist)}
                className="text-xs px-3 py-1.5 rounded-lg bg-stone-700 hover:bg-stone-600 transition-colors"
              >
                Reopen
              </button>
            ) : (
              <button
                onClick={() => onComplete(checklist)}
                className="text-xs px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 transition-colors"
              >
                Mark complete
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
