import requests
from bs4 import BeautifulSoup
import os

# Configuration
url = "https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Introduction/saas-change-log.htm"
state_file = "last_seen_hub.txt"
chat_webhook = os.environ.get("GOOGLE_CHAT_WEBHOOK")

if not chat_webhook:
    raise ValueError("❌ GOOGLE_CHAT_WEBHOOK not set!")

# Fetch the HTML page
response = requests.get(url)
if response.status_code != 200:
    raise Exception(f"❌ Failed to fetch changelog page: {response.status_code}")

soup = BeautifulSoup(response.text, "html.parser")

# Look for the first changelog block using class="content-paragraph"
first_entry = soup.find("div", class_="content-paragraph")
if not first_entry:
    raise Exception("❌ Could not find changelog content block.")

# Extract the title and text
title = first_entry.find("h2")
description = first_entry.find("p")

if not title or not description:
    raise Exception("❌ Missing <h2> or <p> in the changelog block.")

latest_entry = f"{title.get_text(strip=True)} - {description.get_text(strip=True)}"

# Load previous value
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
        print("✅ Notification sent to Google Chat.")
    else:
        print(f"❌ Failed to send: {res.status_code}, {res.text}")

    # Save the latest entry
    with open(state_file, "w") as f:
        f.write(latest_entry)
else:
    print("✅ No new updates found.")
