import asyncio
import logging
import socket
from datetime import datetime, timezone
from time import mktime
from typing import Any, Dict, List

import feedparser

from database import FEEDS, get_latest_news_fetch_time, upsert_news_items

logger = logging.getLogger(__name__)

REFRESH_INTERVAL_SECONDS = 30 * 60
FEED_TIMEOUT_SECONDS = 10


def _parse_feed(source: str, url: str) -> List[Dict[str, Any]]:
    previous_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(FEED_TIMEOUT_SECONDS)
    try:
        parsed = feedparser.parse(url)
    finally:
        socket.setdefaulttimeout(previous_timeout)
    items = []
    for entry in parsed.entries[:15]:
        published_at = None
        if getattr(entry, "published_parsed", None):
            published_at = datetime.fromtimestamp(
                mktime(entry.published_parsed), tz=timezone.utc
            ).isoformat()
        else:
            published_at = datetime.now(tz=timezone.utc).isoformat()

        summary = getattr(entry, "summary", "") or ""
        items.append(
            {
                "title": getattr(entry, "title", "Untitled"),
                "link": getattr(entry, "link", ""),
                "source": source,
                "summary": summary[:400],
                "published_at": published_at,
            }
        )
    return items


async def fetch_all_feeds() -> int:
    all_items: List[Dict[str, Any]] = []
    for source, url in FEEDS:
        try:
            items = await asyncio.wait_for(
                asyncio.to_thread(_parse_feed, source, url), timeout=FEED_TIMEOUT_SECONDS + 5
            )
            all_items.extend(items)
        except Exception as e:
            logger.warning(f"Failed to fetch feed {source}: {e}")
    await upsert_news_items(all_items)
    return len(all_items)


async def refresh_if_stale():
    last_fetch = await get_latest_news_fetch_time()
    if last_fetch is None:
        await fetch_all_feeds()
        return

    try:
        last_dt = datetime.fromisoformat(last_fetch)
    except ValueError:
        await fetch_all_feeds()
        return

    age = datetime.utcnow() - last_dt.replace(tzinfo=None)
    if age.total_seconds() > REFRESH_INTERVAL_SECONDS:
        await fetch_all_feeds()
