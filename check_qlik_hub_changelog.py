import asyncio
from playwright.async_api import async_playwright
import os
import requests
import re
from datetime import datetime, timedelta

# === Config ===
url = "https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Introduction/saas-change-log.htm"
state_file = "last_seen_hub.txt"
chat_webhook = os.environ.get("GOOGLE_CHAT_WEBHOOK")
days_to_look_back = 7

if not chat_webhook:
    raise ValueError("❌ GOOGLE_CHAT_WEBHOOK not set!")

# === Helper: Parse US-style date strings like 4/3/2025
def parse_date(text):
    match = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if match:
        month, day, year = map(int, match.groups())
        return datetime(year, month, day)
    return None

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url, timeout=60000)
        await page.wait_for_selector("p", state="attached")

        # Load state
        seen_entries = set()
        if os.path.exists(state_file):
            with open(state_file, "r") as f:
                seen_entries = set(line.strip() for line in f if line.strip())

        # Go through all paragraphs
        paragraphs = await page.locator("p").all()
        date_pattern = r"^\d{1,2}/\d{1,2}/\d{4}"
        now = datetime.utcnow()
        updates = []

        for p in paragraphs:
            p_text = (await p.text_content()).strip()

            # Check if it starts with a date
            if re.match(date_pattern, p_text):
                post_date = parse_date(p_text)
                if not post_date:
                    continue

                # Skip if older than N days
                if post_date < now - timedelta(days=days_to_look_back):
                    continue

                # Get update title
                h2 = p.locator("xpath=preceding-sibling::h2[1]")
                if await h2.count() == 0:
                    continue
                title = (await h2.text_content()).strip()

                unique_id = f"{title} - {p_text[:10]}"
                if unique_id in seen_entries:
                    continue  # already sent

                updates.append({
                    "title": title,
                    "date": p_text[:10],
                    "summary": p_text,
                    "id": unique_id
                })

        if not updates:
            print("✅ No new updates found.")
        else:
            print(f"📦 Found {len(updates)} new updates... sending to Chat")

        # Send each message
        for update in updates:
            message = {
                "text": f"📢 *New Qlik Hub Update!*\n\n*{update['title']}*\n🗓️ {update['date']}\n{update['summary']}\n🔗 {url}"
            }
            res = requests.post(chat_webhook, json=message)
            if res.status_code == 200:
                print(f"✅ Sent: {update['title']}")
                seen_entries.add(update['id'])
            else:
                print(f"❌ Failed to send: {res.status_code} - {res.text}")

        # Save updated seen list
        with open(state_file, "w") as f:
            for entry in seen_entries:
                f.write(entry + "\n")

        await browser.close()

asyncio.run(main())
