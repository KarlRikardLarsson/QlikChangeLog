import asyncio
from playwright.async_api import async_playwright
import os
import requests

url = "https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Introduction/saas-change-log.htm"
state_file = "last_seen_hub.txt"
chat_webhook = os.environ.get("GOOGLE_CHAT_WEBHOOK")

if not chat_webhook:
    raise ValueError("GOOGLE_CHAT_WEBHOOK not set")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_selector("h2", state="attached")

        # Get all h2s and look for the first one with a real <p> update after it
        headings = await page.locator("h2").all()
        title, description = None, None

        for h2 in headings:
            text = (await h2.text_content()).strip()
            sibling = h2.locator("xpath=following-sibling::p[1]")
            if await sibling.count() > 0:
                desc = (await sibling.text_content()).strip()
                if any(char.isdigit() for char in desc[:10]):  # crude date check
                    title = text
                    description = desc
                    break

        if not title or not description:
            raise Exception("❌ Could not locate valid changelog entry.")

        latest_entry = f"{title} - {description}"

        # Load previous state
        if os.path.exists(state_file):
            with open(state_file, "r") as f:
                last_seen = f.read().strip()
        else:
            last_seen = None

        if latest_entry != last_seen:
            # Send Google Chat message
            msg = {
                "text": f"📢 *New Qlik Hub Update!*\n\n*{title}*\n🗓️ {description}\n🔗 {url}"
            }
            res = requests.post(chat_webhook, json=msg)
            if res.status_code == 200:
                print("✅ Message sent.")
            else:
                print(f"❌ Failed to send: {res.status_code} - {res.text}")

            with open(state_file, "w") as f:
                f.write(latest_entry)
        else:
            print("✅ No new update found.")

        await browser.close()

asyncio.run(main())
