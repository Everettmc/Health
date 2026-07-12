import { useCallback, useEffect, useState } from "react";
import { ExternalLink, Newspaper, RefreshCw } from "lucide-react";
import { api } from "../api/client";
import type { NewsItem } from "../api/client";

export function NewsTab() {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    const data = await api.getNews(40);
    setNews(data);
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function refresh() {
    setRefreshing(true);
    await api.refreshNews();
    await load();
    setRefreshing(false);
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-stone-300 flex items-center gap-2">
          <Newspaper className="w-4 h-4" />
          Industry news
        </h2>
        <button
          onClick={refresh}
          disabled={refreshing}
          className="flex items-center gap-1.5 text-xs text-stone-400 hover:text-stone-200 transition-colors px-3 py-1.5 rounded-lg hover:bg-stone-800/60 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {loading && <div className="text-center text-stone-500 text-sm py-8">Loading headlines…</div>}

      {!loading && news.length === 0 && (
        <div className="text-center text-stone-500 text-sm py-8">
          No headlines yet — hit refresh, or the feeds may be temporarily unreachable.
        </div>
      )}

      <div className="flex flex-col gap-2">
        {news.map((item) => (
          <a
            key={item.id}
            href={item.link}
            target="_blank"
            rel="noreferrer"
            className="rounded-xl border border-stone-700/40 bg-stone-800/60 p-4 flex flex-col gap-1.5 hover:border-brand-600/60 hover:bg-stone-800 transition-colors group"
          >
            <div className="flex items-start justify-between gap-3">
              <span className="text-sm font-medium leading-snug">{item.title}</span>
              <ExternalLink className="w-3.5 h-3.5 text-stone-600 group-hover:text-stone-400 shrink-0 mt-0.5" />
            </div>
            {item.summary && (
              <p className="text-xs text-stone-500 leading-relaxed line-clamp-2">{stripTags(item.summary)}</p>
            )}
            <div className="flex items-center gap-2 text-[10px] text-stone-600 uppercase tracking-wide mt-1">
              <span className="text-brand-500">{item.source}</span>
              <span>&middot;</span>
              <span>{new Date(item.published_at).toLocaleDateString()}</span>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}

function stripTags(html: string): string {
  return html.replace(/<[^>]*>/g, "");
}
