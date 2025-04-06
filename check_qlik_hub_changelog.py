import requests
from bs4 import BeautifulSoup
import os

# Config
url = "https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Introduction/saas-change-log.htm"
state_file = "last_seen_hub.txt"
chat_webhook = os.environ.get("GOOGLE_CHAT_WEBHOOK")

if not chat_webhook:
    raise ValueError("❌ GOOGLE_CHAT_WEBHOOK is not set!")

# Fetch the page
response = requests.get(url)
if response.status_code != 200:
    raise Exception(f"Failed to load changelog page: {response.status_code}")

soup = BeautifulSoup(response.content, "html.parser")

# Find the first update block
first_block = soup.find("div", class_="cq-text")
if not first_block:
    raise Exception("❌ Could not find changelog entry.")

# Extract title and content
title = first_block.find("h2").get_text(strip=True)
paragraph = first_block.find("p").get_text(separator=" ", strip=True)

# Compose the latest update string
latest_entry = f"{title} - {paragraph}"

# Load last seen
if os.path.exists(state_file):
    with open(state_file, "r") as f:
        last_seen = f.read().strip()
else:
    last_seen = None

# Check and notify if it's new
if latest_entry != last_seen:
    message = {
        "text": f"📢 *New Qlik SaaS Update!*\n\n*{title}*\n🗓️ {paragraph}\n🔗 {url}"
    }

    res = requests.post(chat_webhook, json=message)
    if res.status_code == 200:
        print(f"✅ Update sent to Google Chat: {title}")
    else:
        print(f"❌ Failed to send message: {res.status_code}, {res.text}")

    with open(state_file, "w") as f:
        f.write(latest_entry)
else:
    print("✅ No new update found.")
8
