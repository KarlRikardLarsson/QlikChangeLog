import asyncio
from playwright.async_api import async_playwright
import os

url = "https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Introduction/saas-change-log.htm"
state_file = "last_seen_hub.txt"
chat_webhook = os.environ.get("GOOGLE_CHAT_WEBHOOK")

if not chat_webhook:
    raise ValueError("GOOGLE_CHAT_WEBHOOK is not set")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)

        # Wait for any visible H2s to load
        await page.wait_for_selector("h2")

        # Get first H2 and its following paragraph
        title = await page.locator("h2").first.text_content()
        description = await page.locator("h2 + p").first.text_content()

        latest_entry = f"{title.strip()} - {description.strip()}"

        # Load last seen
        if os.path.exists(state_file):
            with open(state_file, "r") as f:
                last_seen = f.read().strip()
        else:
            last_seen = None

        if latest_entry != last_seen:
            # Send message
            import requests
            message = {
                "text": f"📢 *New Qlik Hub Update!*\n\n*{title.strip()}*\n🗓️ {description.strip()}\n🔗 {url}"
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
