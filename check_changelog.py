import feedparser
import os
import requests

# RSS feed
feed_url = "https://qlik.dev/rss.xml"
feed = feedparser.parse(feed_url)
latest_entry = feed.entries[0]
latest_title = latest_entry.title
latest_link = latest_entry.link

# Track last seen
state_file = "last_seen.txt"

# Google Chat webhook URL
chat_webhook = "https://chat.googleapis.com/v1/spaces/AAQAAIRi4fg/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=4wcZG-oNtawH9bjgpMlRHN9my7NjRB1dFNKdmnn7Nvc"

# Check if already seen
if os.path.exists(state_file):
    with open(state_file, "r") as f:
        last_seen = f.read().strip()
else:
    last_seen = ""

# If new changelog entry found
if latest_title != last_seen:
    message = {
        "text": f"🚀 *New Qlik Changelog Entry!*\n*{latest_title}*\n🔗 {latest_link}"
    }

    response = requests.post(chat_webhook, json=message)
    if response.status_code == 200:
        print("✅ Message sent to Google Chat.")
    else:
        print(f"❌ Failed to send message. Status: {response.status_code}, Response: {response.text}")

    with open(state_file, "w") as f:
        f.write(latest_title)
else:
    print("No new updates.")
