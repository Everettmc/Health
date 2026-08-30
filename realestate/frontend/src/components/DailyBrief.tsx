import { AlertCircle, CalendarClock, ExternalLink, ListChecks, Newspaper } from "lucide-react";
import type { DailyBrief as DailyBriefData } from "../api/client";
import { StatCard } from "./StatCard";

interface Props {
  brief: DailyBriefData;
  onGoToChecklists: () => void;
  onGoToContacts: () => void;
  onGoToNews: () => void;
}

export function DailyBrief({ brief, onGoToChecklists, onGoToContacts, onGoToNews }: Props) {
  const followUpCount = brief.follow_ups_due_today.length + brief.follow_ups_overdue.length;

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <StatCard
          label="Today's checklists"
          value={brief.todays_checklists.length}
          icon={<ListChecks className="w-3 h-3" />}
          highlight
        />
        <StatCard
          label="Active checklists"
          value={brief.active_checklist_count}
          icon={<ListChecks className="w-3 h-3" />}
        />
        <StatCard
          label="Follow-ups due"
          value={followUpCount}
          icon={<CalendarClock className="w-3 h-3" />}
          tone={brief.follow_ups_overdue.length > 0 ? "danger" : followUpCount > 0 ? "warning" : "default"}
        />
      </div>

      {brief.follow_ups_overdue.length + brief.follow_ups_due_today.length > 0 && (
        <section className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-stone-300 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-500" />
              Follow up today
            </h2>
            <button onClick={onGoToContacts} className="text-xs text-brand-500 hover:text-brand-400">
              View all contacts
            </button>
          </div>
          <div className="flex flex-col gap-2">
            {[...brief.follow_ups_overdue, ...brief.follow_ups_due_today].map((c) => {
              const isOverdue = brief.follow_ups_overdue.some((o) => o.id === c.id);
              return (
                <div
                  key={c.id}
                  className="rounded-xl border border-stone-700/40 bg-stone-800/60 px-4 py-3 flex items-center justify-between"
                >
                  <div>
                    <div className="text-sm font-medium">{c.name}</div>
                    <div className="text-xs text-stone-500 capitalize">{c.type.replace("_", " ")} &middot; {c.status.replace("_", " ")}</div>
                  </div>
                  <span className={`text-xs ${isOverdue ? "text-red-400" : "text-amber-400"}`}>
                    {isOverdue ? "Overdue" : "Due today"} &middot; {c.follow_up_date}
                  </span>
                </div>
              );
            })}
          </div>
        </section>
      )}

      <section className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-stone-300 flex items-center gap-2">
            <ListChecks className="w-4 h-4 text-brand-500" />
            Today's checklists
          </h2>
          <button onClick={onGoToChecklists} className="text-xs text-brand-500 hover:text-brand-400">
            View all checklists
          </button>
        </div>
        {brief.todays_checklists.length === 0 ? (
          <div className="rounded-xl border border-stone-700/40 bg-stone-800/60 px-4 py-6 text-center text-sm text-stone-500">
            Nothing scheduled today. Start a checklist for a showing, listing appointment, or open house.
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {brief.todays_checklists.map((c) => {
              const done = c.items.filter((i) => i.done).length;
              return (
                <div
                  key={c.id}
                  className="rounded-xl border border-stone-700/40 bg-stone-800/60 px-4 py-3 flex items-center justify-between"
                >
                  <div>
                    <div className="text-sm font-medium">{c.title}</div>
                    <div className="text-xs text-stone-500">{c.template_name}</div>
                  </div>
                  <span className="text-xs text-stone-400 tabular-nums">
                    {done}/{c.items.length}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </section>

      <section className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-stone-300 flex items-center gap-2">
            <Newspaper className="w-4 h-4 text-brand-500" />
            Industry news
          </h2>
          <button onClick={onGoToNews} className="text-xs text-brand-500 hover:text-brand-400">
            View all news
          </button>
        </div>
        {brief.news.length === 0 ? (
          <div className="rounded-xl border border-stone-700/40 bg-stone-800/60 px-4 py-6 text-center text-sm text-stone-500">
            No headlines yet.
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {brief.news.map((item) => (
              <a
                key={item.id}
                href={item.link}
                target="_blank"
                rel="noreferrer"
                className="rounded-xl border border-stone-700/40 bg-stone-800/60 px-4 py-3 flex items-center justify-between gap-3 hover:border-brand-600/60 transition-colors group"
              >
                <div className="min-w-0">
                  <div className="text-sm font-medium truncate">{item.title}</div>
                  <div className="text-xs text-stone-500">{item.source}</div>
                </div>
                <ExternalLink className="w-3.5 h-3.5 text-stone-600 group-hover:text-stone-400 shrink-0" />
              </a>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
