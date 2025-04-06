import feedparser
import os
import requests

# === Configuration ===
feed_url = "https://qlik.dev/rss.xml"
state_file = "last_seen.txt"
chat_webhook = os.environ.get("GOOGLE_CHAT_WEBHOOK")

if not chat_webhook:
    raise ValueError("❌ Google Chat webhook URL not set in environment variables!")

# === Load the feed ===
feed = feedparser.parse(feed_url)
entries = feed.entries

if not entries:
    print("❌ No entries found in the RSS feed. Exiting.")
    exit(1)

# === Load the last seen link (if it exists and is not empty) ===
last_seen_link = None
if os.path.exists(state_file):
    with open(state_file, "r") as f:
        content = f.read().strip()
        if content:
            last_seen_link = content
        else:
            print("⚠️ last_seen.txt exists but is empty. Treating as first run.")

# === First run logic: just set the latest and exit ===
if last_seen_link is None:
    latest_link = entries[0].link
    with open(state_file, "w") as f:
        f.write(latest_link)
    print(f"🛠 First run: Set last seen to latest entry: {latest_link}")
    exit(0)

# === Find new entries since last seen ===
new_entries = []
for entry in entries:
    if entry.link == last_seen_link:
        break
    new_entries.append(entry)

# Reverse to send in chronological order
new_entries.reverse()

# === Send messages to Google Chat ===
if not new_entries:
    print("✅ No new updates found.")
else:
    for entry in new_entries:
        msg = {
            "text": f"🚀 *New Qlik Changelog Entry!*\n*{entry.title}*\n🔗 {entry.link}"
        }
        response = requests.post(chat_webhook, json=msg)
        if response.status_code == 200:
            print(f"✅ Sent: {entry.title}")
        else:
            print(f"❌ Failed to send: {entry.title} – {response.status_code}, {response.text}")

    # Update last_seen.txt with the most recent entry
    latest_link = new_entries[-1].link
    with open(state_file, "w") as f:
        f.write(latest_link)
    print(f"📌 Updated last seen to: {latest_link}")
