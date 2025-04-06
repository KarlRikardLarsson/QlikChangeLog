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

# === Date parser: supports 4/3/2025 etc.
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
        date_pattern = r"\d{1,2}/\d{1,2}/\d{4}"
        updates = []

        for p in paragraphs:
            p_text = re.sub(r"\s+", " ", (await p.text_content()).strip())

            date_match = re.search(date_pattern, p_text)
            if date_match:
                found_date = date_match.group()
                print(f"📅 Found date: {found_date} in → {p_text[:60]}")
            else:
                print(f"🚫 Skipped (no date): {p_text[:60]}")
                continue

            post_date = parse_date(found_date)
            if not post_date:
                continue

            if post_date < now - timedelta(days=days_to_look_back):
                print(f"📭 Skipping old post: {found_date}")
                continue

            h2 = p.locator("xpath=preceding-sibling::h2[1]")
            if await h2.count() == 0:
                continue

            title = (await h2.text_content()).strip()
            unique_id = f"{title} - {found_date}"

            if unique_id in seen_entries:
                print(f"↪️ Already seen: {unique_id}")
                continue

            updates.append({
                "title": title,
                "date": found_date,
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

        with open(state_file, "w") as f:
            for entry in seen_entries:
                f.write(entry + "\n")

        await browser.close()

asyncio.run(main())
