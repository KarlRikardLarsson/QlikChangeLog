import requests
from bs4 import BeautifulSoup
import os

# Config
url = "https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Introduction/saas-change-log.htm"
state_file = "last_seen_hub.txt"
chat_webhook = os.environ.get("GOOGLE_CHAT_WEBHOOK")

if not chat_webhook:
    raise ValueError("❌ Google Chat webhook URL not set!")

# Load page
response = requests.get(url)
if response.status_code != 200:
    raise Exception(f"Failed to fetch page: {response.status_code}")

soup = BeautifulSoup(response.text, "html.parser")

# Extract latest update - targeting first changelog section
latest_section = soup.select_one("div.topic")
if not latest_section:
    raise Exception("❌ Couldn't find changelog content.")

# Extract heading and date text
heading = latest_section.find("h2")
content = latest_section.find("p")
latest_entry = f"{heading.get_text(strip=True)} - {content.get_text(strip=True)}"

# Load last seen
if os.path.exists(state_file):
    with open(state_file, "r") as f:
        last_seen = f.read().strip()
else:
    last_seen = None

# Compare and notify
if latest_entry != last_seen:
    message = {
        "text": f"📢 *New Qlik SaaS Hub Update!*\n\n*{heading.get_text(strip=True)}*\n📅 {content.get_text(strip=True)}\n🔗 {url}"
    }

    post = requests.post(chat_webhook, json=message)
    if post.status_code == 200:
        print(f"✅ Update sent: {latest_entry}")
    else:
        print(f"❌ Failed to send message: {post.status_code}, {post.text}")

    # Save the new entry
    with open(state_file, "w") as f:
        f.write(latest_entry)
else:
    print("✅ No new updates.")
