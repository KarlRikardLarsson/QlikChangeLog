import requests
from bs4 import BeautifulSoup
import os

# Configuration
url = "https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Introduction/saas-change-log.htm"
state_file = "last_seen_hub.txt"
chat_webhook = os.environ.get("GOOGLE_CHAT_WEBHOOK")

if not chat_webhook:
    raise ValueError("❌ GOOGLE_CHAT_WEBHOOK is not set!")

# Fetch the page
response = requests.get(url)
if response.status_code != 200:
    raise Exception(f"❌ Failed to fetch changelog page: {response.status_code}")

soup = BeautifulSoup(response.content, "html.parser")

# Find the first h2 and the next <p>
title = soup.find("h2")
description = title.find_next_sibling("p") if title else None

if not title or not description:
    raise Exception("❌ Could not extract title and description.")

# Clean and combine
latest_entry = f"{title.get_text(strip=True)} - {description.get_text(strip=True)}"

# Load last seen
if os.path.exists(state_file):
    with open(state_file, "r") as f:
        last_seen = f.read().strip()
else:
    last_seen = None

# Compare and notify
if latest_entry != last_seen:
    message = {
        "text": f"📢 *New Qlik Hub Update!*\n\n*{title.get_text(strip=True)}*\n🗓️ {description.get_text(strip=True)}\n🔗 {url}"
    }

    res = requests.post(chat_webhook, json=message)
    if res.status_code == 200:
        print("✅ Message sent to Google Chat.")
    else:
        print(f"❌ Failed to send: {res.status_code}, {res.text}")

    with open(state_file, "w") as f:
        f.write(latest_entry)
else:
    print("✅ No new update found.")
