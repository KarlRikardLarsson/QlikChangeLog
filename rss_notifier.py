"""Shared RSS changelog watcher used by the Qlik Hub and qlik.dev notifiers."""

from __future__ import annotations

import html
import os
import re
from typing import Any

import feedparser
import requests


def entry_id(entry: Any) -> str:
    """Stable identity for an RSS item (prefer guid/id over link)."""
    value = entry.get("id") or entry.get("guid") or entry.get("link")
    if not value:
        raise ValueError(f"RSS entry has no id/guid/link: {entry.get('title')!r}")
    return str(value).strip()


def plain_summary(entry: Any, max_len: int = 280) -> str:
    raw = entry.get("summary") or entry.get("description") or ""
    text = re.sub(r"<[^>]+>", " ", raw)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_len:
        text = text[: max_len - 1].rstrip() + "…"
    return text


def load_last_seen(state_file: str) -> str | None:
    if not os.path.exists(state_file):
        return None
    with open(state_file, "r", encoding="utf-8") as f:
        content = f.read().strip()
    return content or None


def save_last_seen(state_file: str, value: str) -> None:
    with open(state_file, "w", encoding="utf-8") as f:
        f.write(value + "\n")


def collect_new_entries(entries: list[Any], last_seen: str) -> tuple[list[Any], bool]:
    """
    Return (new_entries_oldest_first, found_anchor).

    Walks newest → oldest until the last-seen id is found. If the anchor is
    missing (slug change, feed trim, etc.), returns no new entries so we do
    not flood Chat with the whole feed.
    """
    new_entries: list[Any] = []
    for entry in entries:
        if entry_id(entry) == last_seen:
            new_entries.reverse()
            return new_entries, True
        new_entries.append(entry)

    return [], False


def notify_google_chat(webhook: str, text: str) -> None:
    response = requests.post(webhook, json={"text": text}, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(
            f"Google Chat webhook failed: {response.status_code} – {response.text}"
        )


def run_rss_watcher(
    *,
    feed_url: str,
    state_file: str,
    source_label: str,
    emoji: str,
) -> None:
    chat_webhook = os.environ.get("GOOGLE_CHAT_WEBHOOK")
    if not chat_webhook:
        raise ValueError("GOOGLE_CHAT_WEBHOOK not set!")

    feed = feedparser.parse(feed_url)
    if getattr(feed, "bozo", False) and not feed.entries:
        raise RuntimeError(f"Failed to parse RSS feed {feed_url}: {feed.bozo_exception}")

    entries = feed.entries
    if not entries:
        raise RuntimeError(f"No entries found in RSS feed: {feed_url}")

    latest_id = entry_id(entries[0])
    last_seen = load_last_seen(state_file)

    if last_seen is None:
        save_last_seen(state_file, latest_id)
        print(f"🛠 First run: set last seen for {source_label} to {latest_id}")
        return

    new_entries, found_anchor = collect_new_entries(entries, last_seen)

    if not found_anchor:
        save_last_seen(state_file, latest_id)
        print(
            f"⚠️ Last seen id was not in the {source_label} feed "
            f"({last_seen!r}). Re-anchored to {latest_id} without notifying "
            "to avoid flooding Chat."
        )
        return

    if not new_entries:
        print(f"✅ No new {source_label} updates found.")
        return

    for entry in new_entries:
        title = (entry.get("title") or "(untitled)").strip()
        link = (entry.get("link") or feed_url).strip()
        summary = plain_summary(entry)
        lines = [f"{emoji} *New {source_label} update*", f"*{title}*", f"🔗 {link}"]
        if summary:
            lines.append(summary)
        notify_google_chat(chat_webhook, "\n".join(lines))
        print(f"✅ Sent: {title}")

    save_last_seen(state_file, entry_id(new_entries[-1]))
    print(f"📌 Updated last seen to: {entry_id(new_entries[-1])}")
    print(f"📬 Done — {len(new_entries)} new {source_label} update(s) sent.")
