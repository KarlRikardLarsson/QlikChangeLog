import asyncio
from playwright.async_api import async_playwright
import os
import requests
import re

# === Config ===
url = "https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Introduction/saas-change-log.htm"
state_file = "last_seen_hub.txt"
chat_webhook = os.environ.get("GOOGLE_CHAT_WEBHOOK")

if not chat_webhook:
    raise ValueError("❌ GOOGLE_CHAT_WEBHOOK not set")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url, timeout=60000)
        await page.wait_for_selector("p", state="attached")

        # === Find the first paragraph starting with a date (e.g. 4/3/2025)
        date_pattern = r"^\d{1,2}/\d{1,2}/\d{4}"
        paragraphs = await page.locator("p").all()
        title, description = None, None

        for para in paragraphs:
            text = (await para.text_content()).strip()
            if re.match(date_pattern, text):
                # Go up and find the most recent <h2> above this <p>
                h2 = para.locator("xpath=preceding-sibling::h2[1]")
                if await h2.count() > 0:
                    title = (await h2.text_content()).strip()
                    description = text
                    break

        if not title or not description:
            raise Exception("❌ Could not locate valid changelog entry.")

        latest_entry = f"{title} - {description}"

        # === Load previous
        if os.path.exists(state_file):
            with open(state_file, "r") as f:
                last_seen = f.read().strip()
        else:
            last_seen = None

        # === Send if new
        if latest_entry != last_seen:
            message = {
                "text": f"📢 *New Qlik Hub Update!*\n\n*{title}*\n🗓️ {description}\n🔗 {url}"
            }
            res = requests.post(chat_webhook, json=message)

            if res.status_code == 200:
                print("✅ Message sent.")
            else:
                print(f"❌ Failed to send: {res.status_code}, {res.text}")

            with open(state_file, "w") as f:
                f.write(latest_entry)
        else:
            print("✅ No new update found.")

        await browser.close()

asyncio.run(main())
