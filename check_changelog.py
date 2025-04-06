import feedparser
import os

feed_url = "https://qlik.dev/rss.xml"
feed = feedparser.parse(feed_url)
latest_title = feed.entries[0].title
latest_link = feed.entries[0].link

# Local file to track last seen title
state_file = "last_seen.txt"

# Load previous
if os.path.exists(state_file):
    with open(state_file, "r") as f:
        last_seen = f.read().strip()
else:
    last_seen = ""

# Compare and update
if latest_title != last_seen:
    print(f"🔔 New Qlik Changelog item found: {latest_title} ({latest_link})")
    # Optional: Send webhook, post to Slack, etc.
    with open(state_file, "w") as f:
        f.write(latest_title)
else:
    print("✅ No new changelog entries.")
