import feedparser
import os
import requests

feed_url = "https://qlik.dev/rss.xml"
state_file = "last_seen.txt"
chat_webhook = os.environ.get("GOOGLE_CHAT_WEBHOOK")

if not chat_webhook:
    raise ValueError("Google Chat webhook URL not set!")

# Parse the RSS feed
feed = feedparser.parse(feed_url)
entries = feed.entries

# Load last seen GUID or link
if os.path.exists(state_file):
    with open(state_file, "r") as f:
        last_seen_link = f.read().strip()
else:
    last_seen_link = None

# Collect new entries
new_entries = []
for entry in entries:
    if entry.link == last_seen_link:
        break
    new_entries.append(entry)

# Reverse to send in chronological order
new_entries.reverse()

# Send each new entry to Google Chat
for entry in new_entries:
    msg = {
        "text": f"🚀 *New Qlik Changelog Entry!*\n*{entry.title}*\n🔗 {entry.link}"
    }
    res = requests.post(chat_webhook, json=msg)
    if res.status_code == 200:
        print(f"✅ Sent: {entry.title}")
    else:
        print(f"❌ Failed to send: {entry.title} – {res.status_code}, {res.text}")

# Update last seen if there were new entries
if new_entries:
    latest_link = new_entries[-1].link
    with open(state_file, "w") as f:
        f.write(latest_link)
    print(f"📌 Updated last seen to: {latest_link}")
else:
    print("No new updates.")
