import asyncio
from playwright.async_api import async_playwright
import os
import requests

# === Config ===
url = "https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Introduction/saas-change-log.htm"
state_file = "last_seen_titles.txt"
chat_webhook = os.environ.get("GOOGLE_CHAT_WEBHOOK")

if not chat_webhook:
    raise ValueError("❌ GOOGLE_CHAT_WEBHOOK not set!")

# Optional: exclude generic headings
ignore_keywords = [
    "help", "resources", "company", "legal", "cookie", "did this page", "filters", "qlik cloud"
]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url, timeout=60000)

        await page.wait_for_timeout(60000)
        await page.wait_for_selector("h2", timeout=60000, state="attached")

        seen_titles = set()
        if os.path.exists(state_file):
            with open(state_file, "r") as f:
                seen_titles = set(line.strip() for line in f if line.strip())

        print(f"🧠 Loaded {len(seen_titles)} previously seen titles.")

        headings = await page.locator("h2").all()
        print(f"🔍 Found {len(headings)} <h2> elements.")

        new_titles = []

        for h2 in headings:
            title = (await h2.text_content()).strip()
            if not title:
                continue

            # Ignore generic headings
            if any(word in title.lower() for word in ignore_keywords):
                continue

            if title in seen_titles:
                continue

            print(f"🆕 New heading: {title}")
            new_titles.append(title)

            # Send message to Google Chat
            message = {
                "text": f"🆕 *New Qlik Hub Update:*\n{title}\n🔗 {url}"
            }

            res = requests.post(chat_webhook, json=message)
            if res.status_code == 200:
                print(f"✅ Sent: {title}")
                seen_titles.add(title)
            else:
                print(f"❌ Failed to send: {res.status_code} - {res.text}")

        # Save updated seen titles
        with open(state_file, "w") as f:
            for title in sorted(seen_titles):
                f.write(title + "\n")

        if not new_titles:
            print("✅ No new updates found.")
        else:
            print(f"📬 Done — {len(new_titles)} new title(s) sent.")

        await browser.close()

asyncio.run(main())
