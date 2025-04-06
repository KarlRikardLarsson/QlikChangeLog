import requests
from bs4 import BeautifulSoup
import os

# Config
url = "https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Introduction/saas-change-log.htm"
state_file = "last_seen_hub.txt"
chat_webhook = os.environ.get("GOOGLE_CHAT_WEBHOOK")

if not chat_webhook:
    raise ValueError("❌ GOOGLE_CHAT_WEBHOOK not set!")

# Load page
response = requests.get(url)
if response.status_code != 200:
    raise Exception(f"Failed to fetch page: {response.status_code}")

soup = BeautifulSoup(response.text, "html.parser")

# Find the first h2 and the following paragraph
latest_title = soup.find("h2")
latest_paragraph = latest_title.find_next_sibling("p") if latest_title else None

if not latest_title or not latest_paragraph:
    raise Exception("❌ Couldn't find latest changelog content.")

# Compose entry string
latest_entry = f"{latest_title.get_text(strip=True)} - {latest_paragraph.get_text(strip=True)}"

# Load last seen
if os.path.exists(state_file):
    with open(state_file, "r") as f:
        last_seen = f.read().strip()
else:
    last_seen = None

# Compare and notify
if latest_entry != last_seen:
    message = {
        "text": f"📢 *New Qlik Hub Update!*\n\n*{latest_title.get_text(strip=True)}*\n🗓️ {latest_paragraph.get_text(strip=True)}\n🔗 {url}"
    }

    res = requests.post(chat_webhook, json=message)
    if res.status_code == 200:
        print(f"✅ Message sent: {latest_entry}")
    else:
        print(f"❌ Failed to send: {res.status_code}, {res.text}")

    # Save state
    with open(state_file, "w") as f:
        f.write(latest_entry)
else:
    print("✅ No new updates.")
