import feedparser
import os
import requests

# === Config ===
feed_url = "https://qlik.dev/rss.xml"
state_file = "last_seen.txt"
chat_webhook = os.environ.get("GOOGLE_CHAT_WEBHOOK")

if not chat_webhook:
    raise ValueError("❌ Google Chat webhook URL not found in environment variables!")

# === Fetch and parse RSS ===
feed = feedparser.parse(feed_url)
entries = feed.entries

if not entries:
    print("❌ No entries found in the RSS feed.")
    exit(1)

# === Load last seen link ===
if os.path.exists(state_file):
    with open(state_file, "r") as f:
        last_seen_link = f.read().strip()
else:
    last_seen_link = None

# === First run: Set last seen and exit ===
if last_seen_link is None:
    print("🛠 First run detected. Setting last seen to latest entry without sending messages.")
    with open(state_file, "w") as f:
        f.write(entries[0].link)
    exit(0)

# === Find new entries ===
new_entries = []
for entry in entries:
    if entry.link == last_seen_link:
        break
    new_entries.append(entry)

# Reverse to send in chronological order
new_entries.reverse()

# === Send messages for new entries ===
for entry in new_entries:
    msg = {
        "text": f"🚀 *New Qlik Changelog Entry!*\n*{entry.title}*\n🔗 {entry.link}"
    }
    res = requests.post(chat_webhook, json=msg)
    if res.status_code == 200:
        print(f"✅ Sent: {entry.title}")
    else:
        print(f"❌ Failed to send: {entry.title} – {res.status_code}, {res.text}")

# === Update last seen if needed ===
if new_entries:
    latest_link = new_entries[-1].link
    with open(state_file, "w") as f:
        f.write(latest_link)
    print(f"📌 Updated last seen to: {latest_link}")
else:
    print("✅ No new updates found.")
