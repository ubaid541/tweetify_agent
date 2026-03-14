# Tools Directory

This folder contains Python scripts that handle all deterministic execution in Tweetify.

## How Tools Work

- Each tool is a **standalone Python script** — no shared state between runs
- Tools read from `.env` for credentials and write results to `.tmp/` or stdout
- Tools are called by the agent *after* reading the relevant workflow
- All tools use `argparse` for CLI and `python-dotenv` for credentials

## Available Tools

| Tool | Purpose | Credentials Needed |
|------|---------|-------------------|
| `post_tweet.py` | Post a tweet or thread | `TWITTER_API_KEY/SECRET`, `TWITTER_ACCESS_TOKEN/SECRET` |
| `fetch_twitter_data.py` | Fetch tweets, user timelines, search | `TWITTER_BEARER_TOKEN` |
| `fetch_newsletter.py` | Fetch newsletters from Gmail (Tech Brew + Future Tools) | `credentials.json`, `token.json` |
| `extract_ai_content.py` | Extract AI/tech items from newsletter via GPT-4o | `OPENAI_API_KEY` |
| `generate_tweets.py` | Generate 4-5 tweet drafts from AI content via GPT-4o | `OPENAI_API_KEY` |
| `approve_tweets.py` | Interactive Rich UI to review, edit, and approve drafts | — |

## Tools To Build Next

| Tool | Purpose |
|------|---------|
| `schedule_tweet.py` | Queue an approved tweet for posting at a specific time |
| `analyze_engagement.py` | Pull engagement metrics on past tweets |

## Adding a New Tool

1. Create `tools/<tool_name>.py`
2. Use `argparse` for CLI arguments
3. Use `python-dotenv` to load credentials from `.env`
4. Print results to stdout (JSON preferred for structured data)
5. Save intermediate files to `.tmp/`
6. Update this README with the new tool entry
7. Create or update the relevant workflow in `workflows/`
