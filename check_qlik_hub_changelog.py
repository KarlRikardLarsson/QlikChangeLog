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

        await page.wait_for_timeout(3000)
        await page.wait_for_selector("h2", timeout=15000, state="attached")

        now = datetime.now(timezone.utc)
        seen_entries = set()

        if os.path.exists(state_file):
            with open(state_file, "r") as f:
                seen_entries = set(line.strip() for line in f if line.strip())

        print(f"🧠 Loaded {len(seen_entries)} previously seen entries.")

        headings = await page.locator("h2").all()
        print(f"🔍 Found {len(headings)} changelog blocks.")

        date_pattern = r"\d{1,2}/\d{1,2}/\d{4}"
        updates = []

        for h2 in headings:
            title = (await h2.text_content()).strip()
            print(f"🧩 Heading: {title[:60]}")

            # Get the first following <p> (date line)
            date_p = h2.locator("xpath=following-sibling::p[1]")
            if await date_p.count() == 0:
                continue

            date_text = re.sub(r"\s+", " ", (await date_p.text_content()).strip())
            print(f"🕵️ Date candidate: {date_text[:60]}")

            date_match = re.search(date_pattern, date_text)
            if not date_match:
                print("🚫 Skipped — no valid date line found")
                continue

            found_date = date_match.group()
            post_date = parse_date(found_date)
            if not post_date:
                continue

            if post_date < now - timedelta(days=days_to_look_back):
                print(f"📭 Skipping old post: {found_date}")
                continue

            # Get next 1-2 paragraphs for summary
            summary_parts = []
            for i in range(2, 4):
                sibling = h2.locator(f"xpath=following-sibling::p[{i}]")
                if await sibling.count() > 0:
                    summary_parts.append((await sibling.text_content()).strip())

            summary = "\n".join(summary_parts)
            unique_id = f"{title} - {found_date}"

            if unique_id in seen_entries:
                print(f"↪️ Already seen: {unique_id}")
                continue

            updates.append({
                "title": title,
                "date": found_date,
                "summary": summary,
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
