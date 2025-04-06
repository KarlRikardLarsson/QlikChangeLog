# 🔔 Qlik Changelog Notifier

This GitHub Action monitors the [Qlik Developer Changelog](https://qlik.dev/changelog/) every morning at **08:00 UTC** and sends a message to a Google Chat space if there's a new entry.

---

## 📦 How It Works

- Checks the [Qlik Changelog RSS feed](https://qlik.dev/rss.xml).
- Compares the latest entry to the previously seen one.
- If there’s a new update, sends a notification to Google Chat.
- Stores the last seen title in `last_seen.txt`.

---

## 🛠 Setup

1. **Add a GitHub Secret**
   - Go to your repository → Settings → Secrets → Actions.
   - Add a new secret:
     - **Name:** `GOOGLE_CHAT_WEBHOOK`
     - **Value:** your Google Chat webhook URL.

2. **Customize (Optional)**
   - You can change the check time in `.github/workflows/qlik-changelog-check.yml` by editing the `cron` expression.

---

## 🧪 Run a Manual Test

To run the workflow now and verify everything works:

- Go to **Actions** in your repo.
- Select **Qlik Changelog Watcher** workflow.
- Click **"Run workflow"** → Run on `main`.

> It will print a success message in the logs and send a test message to your Chat space if a new changelog entry is found.

---

## ✅ Requirements

- Python 3.x (auto-installed via GitHub Actions)
- GitHub Actions enabled
- Google Chat webhook set as a secret

---

## 💬 Output Example in Google Chat

