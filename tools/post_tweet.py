"""
tools/post_tweet.py
-------------------
Posts a tweet (or thread) via the Twitter / X API v2.

Usage:
    python tools/post_tweet.py --text "Your tweet text here"
    python tools/post_tweet.py --file tweet.txt         # reads text from file
    python tools/post_tweet.py --reply-to <tweet_id>    # reply to existing tweet

Requires in .env:
    TWITTER_API_KEY
    TWITTER_API_SECRET
    TWITTER_ACCESS_TOKEN
    TWITTER_ACCESS_TOKEN_SECRET
"""

import argparse
import os
import sys
from pathlib import Path

import tweepy
from dotenv import load_dotenv

# ── Load environment ───────────────────────────────────────────────────────────
load_dotenv()

REQUIRED_VARS = [
    "TWITTER_API_KEY",
    "TWITTER_API_SECRET",
    "TWITTER_ACCESS_TOKEN",
    "TWITTER_ACCESS_TOKEN_SECRET",
]


def get_client() -> tweepy.Client:
    """Authenticate with Twitter API v2 and return a Client."""
    missing = [v for v in REQUIRED_VARS if not os.getenv(v)]
    if missing:
        print(f"[ERROR] Missing environment variables: {', '.join(missing)}")
        print("        Copy .env.example → .env and fill in your credentials.")
        sys.exit(1)

    return tweepy.Client(
        consumer_key=os.getenv("TWITTER_API_KEY"),
        consumer_secret=os.getenv("TWITTER_API_SECRET"),
        access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
        access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
    )


def post_tweet(text: str, reply_to: str | None = None) -> dict:
    """
    Post a single tweet.

    Args:
        text: Tweet text (max 280 chars).
        reply_to: Optional tweet ID to reply to.

    Returns:
        dict with 'id' and 'text' of the created tweet.
    """
    client = get_client()

    if len(text) > 280:
        print(f"[WARN] Tweet text is {len(text)} chars — Twitter will truncate at 280.")

    kwargs: dict = {"text": text}
    if reply_to:
        kwargs["in_reply_to_tweet_id"] = reply_to

    response = client.create_tweet(**kwargs)
    tweet = response.data

    print(f"[OK] Tweet posted → https://x.com/i/web/status/{tweet['id']}")
    return {"id": tweet["id"], "text": tweet["text"]}


# ── CLI ────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Post a tweet via Twitter API v2")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", type=str, help="Tweet text (max 280 chars)")
    group.add_argument("--file", type=Path, help="Path to a .txt file containing the tweet text")
    parser.add_argument("--reply-to", type=str, default=None, help="Tweet ID to reply to")
    args = parser.parse_args()

    if args.file:
        text = args.file.read_text(encoding="utf-8").strip()
    else:
        text = args.text

    post_tweet(text, reply_to=args.reply_to)


if __name__ == "__main__":
    main()
