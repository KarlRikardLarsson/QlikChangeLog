import feedparser
import os
import requests

# RSS feed
feed_url = "https://qlik.dev/rss.xml"
feed = feedparser.parse(feed_url)
latest_entry = feed.entries[0]
latest_title = latest_entry.title
latest_link = latest_entry.link

# State tracking
state_file = "last_seen.txt"

# Webhook from environment variable (GitHub secret)
chat_webhook = os.environ.get("GOOGLE_CHAT_WEBHOOK")

if not chat_webhook:
    raise ValueError("Google Chat webhook URL not found in environment variables!")

# Compare with last seen
if os.path.exists(state_file):
    with open(state_file, "r") as f:
        last_seen = f.read().strip()
else:
    last_seen = ""

# If new entry found
if latest_title != last_seen:
    message = {
        "text": f"🚀 *New Qlik Changelog Entry!*\n*{latest_title}*\n🔗 {latest_link}"
    }

    response = requests.post(chat_webhook, json=message)
    if response.status_code == 200:
        print("✅ Sent to Google Chat.")
    else:
        print(f"❌ Chat message failed: {response.status_code}, {response.text}")

    with open(state_file, "w") as f:
        f.write(latest_title)
else:
    print("No new update.")
