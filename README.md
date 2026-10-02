# 🔔 Qlik Changelog Notifier

GitHub Actions that watch Qlik's official RSS feeds and post new entries to a Google Chat space.

| Watcher | Feed | Schedule | State file |
| --- | --- | --- | --- |
| Qlik.dev Changelog | [qlik.dev/rss.xml](https://qlik.dev/rss.xml) | 08:00 UTC | `last_seen.txt` |
| Qlik Hub What's New | [saas-change-log.htm.rss](https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Introduction/saas-change-log.htm.rss) | 09:00 UTC | `last_seen_hub.txt` |

---

## How it works

- Parses each RSS feed with `feedparser`.
- Compares entries to the stored last-seen item id (guid/link).
- Sends new items to Google Chat (oldest → newest), including a short summary when available.
- If the stored id disappeared from the feed (slug change / trim), re-anchors to the latest item **without** notifying, so Chat is not flooded.

Shared logic lives in `rss_notifier.py`. The two `check_*.py` scripts are thin wrappers.

---

## Setup

1. **Add a GitHub Secret**
   - Repository → Settings → Secrets → Actions
   - Name: `GOOGLE_CHAT_WEBHOOK`
   - Value: your Google Chat webhook URL

2. **Optional**
   - Change schedules in `.github/workflows/qlik-changelog-check.yml` and `.github/workflows/qlik-hub-changelog.yml`

---

## Manual test

1. Actions → pick **Qlik Changelog Watcher** or **Qlik Hub Changelog Watcher**
2. Run workflow → Run on `main`

First run with an empty state file only seeds the latest entry and does not notify.

---

## Requirements

- Python 3.x (via GitHub Actions)
- `feedparser` + `requests`
- Google Chat webhook secret
