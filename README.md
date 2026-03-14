# Tweetify 🐦

> An AI-powered tweet scheduling and content repurposing agent built on the **WAT framework** (Workflows · Agents · Tools).

---

## What It Does

Tweetify turns long-form content (articles, videos, newsletters) into polished, on-brand tweets — and posts them via the Twitter / X API.

---

## Architecture

```
Workflows (what to do)  →  Agent (decides how)  →  Tools (does the work)
```

| Layer | Location | Role |
|-------|----------|------|
| **Workflows** | `workflows/` | Markdown SOPs — objectives, inputs, steps, edge cases |
| **Agent** | You (AI) | Reads workflows, sequences tools, handles errors |
| **Tools** | `tools/` | Python scripts — deterministic execution |

---

## Directory Layout

```
tweetify/
├── .env.example      # Copy → .env, fill in your keys
├── .gitignore
├── requirements.txt
├── CLAUDE.md         # Agent operating instructions
├── README.md         # This file
│
├── tools/            # Python execution scripts
│   ├── post_tweet.py
│   └── fetch_twitter_data.py
│
├── workflows/        # Markdown SOPs
│   ├── post_tweet.md
│   └── scrape_content.md
│
└── .tmp/             # Disposable intermediate files (gitignored)
```

---

## Quick Start

```bash
# 1. Clone / navigate to the project
cd tweetify

# 2. Create a virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up credentials
copy .env.example .env
# Edit .env with your actual API keys

# 5. Run a tool directly (example)
python tools/post_tweet.py --text "Hello from Tweetify! 🐦"
```

---

## Credentials

| Secret | Where to get it |
|--------|----------------|
| `TWITTER_API_KEY` / `SECRET` | [developer.twitter.com](https://developer.twitter.com) → Project → App → Keys |
| `TWITTER_ACCESS_TOKEN` / `SECRET` | Same page → "Access Token and Secret" |
| `TWITTER_BEARER_TOKEN` | Same page → "Bearer Token" |
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |

---

## Rules (from CLAUDE.md)

1. **Check `tools/` before building anything new**
2. **Update workflows when you discover better methods or constraints**
3. **All secrets live in `.env` only — never hardcoded**
4. **`.tmp/` is disposable — deliverables go to cloud services**
