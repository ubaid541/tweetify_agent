---
description: Daily pipeline — fetch newsletters, extract AI content, and generate tweet drafts
---

## Objective
Run the full daily pipeline: fetch today's newsletters → extract AI/tech content → generate 4-5 tweet drafts ready for review.

## Prerequisites
- `.env` is configured (Gmail credentials, `OPENAI_API_KEY`)
- `credentials.json` present in project root (one-time Gmail setup — see `workflows/fetch_newsletter.md`)
- Python dependencies installed: `pip install -r requirements.txt`

## Daily Pipeline Steps

### Step 1 — Fetch Newsletters
```
python tools/fetch_newsletter.py
```
- Connects to Gmail, finds unseen newsletters from Tech Brew and Future Tools
- Converts HTML to markdown, saves to `.tmp/newsletter_YYYY-MM-DD.json`
- Expected output: confirmation message and the file created

**If no emails found:** The newsletters may not have arrived yet. Tech Brew typically arrives by 7 AM ET. Future Tools arrives irregularly — run with `--days-back 2` if you missed a day.

---

### Step 2 — Extract AI/Tech Content
```
python tools/extract_ai_content.py
```
- Sends newsletter content to GPT-4o to filter and extract only AI/tech stories
- Outputs structured list of items: title, summary, key insight, significance
- Saves to `.tmp/ai_content_YYYY-MM-DD.json`

**If too few items extracted:** The newsletter may have been light on AI news. You can manually add items to the JSON file before proceeding.

---

### Step 3 — Generate Tweet Drafts
```
python tools/generate_tweets.py
```
- Takes extracted AI items (sorted by significance: high → medium → low)
- Generates 4-5 tweet drafts using GPT-4o with tone guidelines
- Validates all drafts are ≤ 280 characters
- Flags thread candidates with `is_thread: true`
- Saves to `.tmp/drafts_YYYY-MM-DD.json`

To request more tweets:
```
python tools/generate_tweets.py --count 7
```

---

### Step 4 — Review Drafts
```
python tools/approve_tweets.py
```
Follow the [approve_and_post workflow](approve_and_post.md) for review steps.

---

## Full Command Sequence (Quick Reference)
```bash
# Run all steps in order
python tools/fetch_newsletter.py
python tools/extract_ai_content.py
python tools/generate_tweets.py
python tools/approve_tweets.py
```

## Dry-Run Mode (No API Calls)
Test the entire pipeline without using any API credits:
```bash
python tools/fetch_newsletter.py --dry-run
python tools/extract_ai_content.py --dry-run
python tools/generate_tweets.py --dry-run
python tools/approve_tweets.py --dry-run
```

## Intermediate Files (All in `.tmp/`)
| File | Created By | Contents |
|------|-----------|----------|
| `newsletter_YYYY-MM-DD.json` | `fetch_newsletter.py` | Raw newsletter markdown |
| `ai_content_YYYY-MM-DD.json` | `extract_ai_content.py` | Filtered AI/tech items |
| `drafts_YYYY-MM-DD.json` | `generate_tweets.py` | Tweet drafts with statuses |
| `processed_ids.json` | `fetch_newsletter.py` | Deduplification tracker |

> All files in `.tmp/` are disposable and regenerable. They are gitignored.

## Windows Task Scheduler (Optional — Run Automatically)
To run the pipeline automatically every morning:

1. Open **Task Scheduler** (search in Start menu)
2. Click **Create Basic Task**
3. Name: `Tweetify Daily Pipeline`
4. Trigger: **Daily** at your preferred time (e.g. 8:00 AM)
5. Action: **Start a Program**
   - Program: `python`
   - Arguments: `tools/fetch_newsletter.py && python tools/extract_ai_content.py && python tools/generate_tweets.py`
   - Start in: `g:\my_agents\tweetify`
6. Click **Finish**

After the scheduled run, open a terminal and run `python tools/approve_tweets.py` to review drafts.

## Error Handling
| Error | Fix |
|-------|-----|
| `newsletter_YYYY-MM-DD.json not found` | Run Step 1 first |
| `ai_content_YYYY-MM-DD.json not found` | Run Step 2 first |
| `OPENAI_API_KEY not set` | Add to `.env` file |
| GPT returns empty extraction | Newsletter was light on AI news; acceptable |
| Draft exceeds 280 chars | Tool auto-truncates; check approvals carefully |
