---
description: How to post a tweet or thread using the Twitter / X API
---

## Objective
Post one or more tweets to the authenticated Twitter account.

## Required Inputs
- Tweet text (max 280 chars per tweet)
- Optional: tweet ID to reply to (for threads)
- Optional: media attachments (future)

## Credentials Needed (in `.env`)
- `TWITTER_API_KEY`
- `TWITTER_API_SECRET`
- `TWITTER_ACCESS_TOKEN`
- `TWITTER_ACCESS_TOKEN_SECRET`

## Steps

1. Verify credentials are set in `.env`
   - If missing, prompt user to run: `copy .env.example .env` and fill in keys

2. Prepare tweet text
   - If generating from content: run the content → tweet generation step first
   - If user-provided: use as-is
   - Validate: length ≤ 280 chars, no prohibited content

3. Post the tweet
   ```
   python tools/post_tweet.py --text "Your tweet text here"
   ```
   - For reply: `python tools/post_tweet.py --text "Reply text" --reply-to <tweet_id>`
   - For text from file: `python tools/post_tweet.py --file .tmp/tweet.txt`

4. Capture the output
   - Tool prints the tweet URL on success
   - Record the tweet ID if building a thread

5. For threads (multiple connected tweets)
   - Post tweet 1, capture its ID
   - Post tweet 2 with `--reply-to <tweet_1_id>`
   - Repeat for each subsequent tweet

## Expected Output
- Console: `[OK] Tweet posted → https://x.com/i/web/status/<id>`
- Tweet ID returned for use in threads

## Error Handling
| Error | Likely Cause | Fix |
|-------|-------------|-----|
| `Missing environment variables` | `.env` not set up | Copy `.env.example` → `.env`, fill in keys |
| `401 Unauthorized` | Wrong credentials | Regenerate tokens on developer.twitter.com |
| `403 Forbidden` | App lacks write permission | Upgrade app to "Read and Write" in Twitter Dev Portal |
| `429 Too Many Requests` | Rate limited | Wait 15 min, then retry |
| Tweet text too long | >280 chars | Split into thread or shorten content |

## Notes
- Twitter API v2 Free tier: 1,500 tweets/month write limit
- Do NOT post duplicate content — Twitter may suspend the account
- Rate limit: 300 tweets per 3-hour window per account
