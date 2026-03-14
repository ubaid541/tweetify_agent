---
description: How to fetch newsletter emails from Gmail using the Gmail API
---

## Objective
Connect to Gmail, retrieve today's Tech Brew and Future Tools newsletters, convert to clean markdown, and save to `.tmp/newsletter_YYYY-MM-DD.json`.

## One-Time Setup (Do This Once)

### 1. Create a Google Cloud Project
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click **"New Project"** → name it `tweetify` → Create
3. In the left sidebar: **APIs & Services** → **Library**
4. Search for **"Gmail API"** → Enable it

### 2. Create OAuth Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **"+ Create Credentials"** → **OAuth client ID**
3. Application type: **Desktop app** → name it `tweetify-agent`
4. Click **Create** → **Download JSON**
5. Rename the downloaded file to `credentials.json`
6. Place it in the root of this project (`g:\my_agents\tweetify\credentials.json`)

### 3. Configure OAuth Consent Screen (if prompted)
1. Go to **APIs & Services** → **OAuth consent screen**
2. User Type: **External** → Click Create
3. Fill in App name: `Tweetify`, your email, and save
4. Add scope: `https://www.googleapis.com/auth/gmail.readonly`
5. Add your Gmail address as a **Test user**

### 4. First Run (Browser Auth)
The first time you run `fetch_newsletter.py`, a browser window will open asking you to log in with `malikunknown633@gmail.com` and grant read-only Gmail access. This creates `token.json` which is reused automatically for all future runs.

> **Note:** `credentials.json` and `token.json` are both gitignored — they will never be committed to version control.

---

## Required Inputs
- `credentials.json` in project root (downloaded from Google Cloud)
- Senders configured in `.env` (`NEWSLETTER_SENDERS`) or defaulted in the script

## Steps

1. Ensure `.env` is configured (copy from `.env.example` if not done):
   ```
   copy .env.example .env
   ```

2. Run the newsletter fetcher:
   ```
   python tools/fetch_newsletter.py
   ```
   For a test without any API calls:
   ```
   python tools/fetch_newsletter.py --dry-run
   ```
   To look back multiple days:
   ```
   python tools/fetch_newsletter.py --days-back 3
   ```

3. Verify the output file exists and contains content:
   - Open `.tmp/newsletter_YYYY-MM-DD.json`
   - Confirm `content` field has readable newsletter text

4. Proceed to: `python tools/extract_ai_content.py`

## Expected Output
- `.tmp/newsletter_YYYY-MM-DD.json` — array of newsletter objects with `source`, `subject`, `date`, `content`
- `.tmp/processed_ids.json` — updated list of processed Gmail message IDs

## Error Handling
| Error | Likely Cause | Fix |
|-------|-------------|-----|
| `credentials.json not found` | File not downloaded/placed | Follow setup steps 1-3 above |
| Browser opens but auth fails | Wrong Google account | Make sure you use `malikunknown633@gmail.com` |
| `No new newsletter emails found` | Newsletters not yet received today | Run with `--days-back 2` or check if newsletters arrived |
| `403 Access Denied` | Gmail API not enabled | Enable Gmail API in Google Cloud Console |
| `token.json` invalid | Token expired | Delete `token.json` and re-run to re-authenticate |

## Notes
- Processed message IDs are tracked in `.tmp/processed_ids.json` — this prevents duplicate processing
- The script only fetches emails in **read-only** mode — it cannot send or delete anything
- To reset and re-fetch already-processed newsletters, delete `.tmp/processed_ids.json`
