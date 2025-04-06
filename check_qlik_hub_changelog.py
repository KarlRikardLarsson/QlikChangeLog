import asyncio
from playwright.async_api import async_playwright
import os
import requests
import re
from datetime import datetime, timedelta, timezone

# === Config ===
url = "https://help.qlik.com/en-US/cloud-services/Subsystems/Hub/Content/Sense_Hub/Introduction/saas-change-log.htm"
state_file = "last_seen_hub.txt"
chat_webhook = os.environ.get("GOOGLE_CHAT_WEBHOOK")
days_to_look_back = 7

if not chat_webhook:
    raise ValueError("❌ GOOGLE_CHAT_WEBHOOK not set!")

# === Parse US-style dates like 4/3/2025 or 12/25/2025
def parse_date(text):
    match = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if match:
        month, day, year = map(int, match.groups())
        return datetime(year, month, day, tzinfo=timezone.utc)
    return None

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url, timeout=60000)
        await page.wait_for_selector("p", state="attached")

        now = datetime.now(timezone.utc)
        seen_entries = set()

        if os.path.exists(state_file):
            with open(state_file, "r") as f:
                seen_entries = set(line.strip() for line in f if line.strip())

        print(f"🧠 Loaded {len(seen_entries)} previously seen entries.")

        paragraphs = await page.locator("p").all()
        date_pattern = r"^\d{1,2}/\d{1,2}/\d{4}"
        updates = []

        for p in paragraphs:
            p_text = (await p.text_content()).strip()
           if re.match(date_pattern, p_text):
    print(f"📅 Found dated paragraph: {p_text[:30]}")
else:
    print(f"🚫 Skipped (no match): {p_text[:30]}")


            post_date = parse_date(p_text)
            if not post_date:
                continue

            print(f"📅 Found dated paragraph: {p_text[:10]} → {post_date.date()}")

            # Filter by date
            if post_date < now - timedelta(days=days_to_look_back):
                print(f"📭 Skipping old post: {p_text[:10]}")
                continue

            # Get the heading above it
            h2 = p.locator("xpath=preceding-sibling::h2[1]")
            if await h2.count() == 0:
                continue

            title = (await h2.text_content()).strip()
            unique_id = f"{title} - {p_text[:10]}"

            if unique_id in seen_entries:
                print(f"↪️ Already seen: {unique_id}")
                continue

            updates.append({
                "title": title,
                "date": p_text[:10],
                "summary": p_text,
                "id": unique_id
            })

        if not updates:
            print("✅ No new updates found.")
        else:
            print(f"📦 Sending {len(updates)} new update(s)...")

        for update in updates:
            message = {
                "text": f"📢 *New Qlik Hub Update!*\n\n*{update['title']}*\n🗓️ {update['date']}\n{update['summary']}\n🔗 {url}"
            }

            res = requests.post(chat_webhook, json=message)
            if res.status_code == 200:
                print(f"✅ Sent: {update['id']}")
                seen_entries.add(update['id'])
            else:
                print(f"❌ Failed to send: {res.status_code} - {res.text}")

        # Save updated seen entries
        with open(state_file, "w") as f:
            for entry in seen_entries:
                f.write(entry + "\n")

        await browser.close()

asyncio.run(main())
