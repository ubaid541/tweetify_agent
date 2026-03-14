"""
tools/fetch_twitter_data.py
---------------------------
Fetches data from the Twitter / X API v2.

Supported operations:
    - Get recent tweets by a user
    - Get tweet details by ID
    - Search recent tweets by keyword

Usage:
    python tools/fetch_twitter_data.py --user elonmusk --count 10
    python tools/fetch_twitter_data.py --tweet-id 1234567890
    python tools/fetch_twitter_data.py --search "AI agents" --count 20

Requires in .env:
    TWITTER_BEARER_TOKEN
"""

import argparse
import json
import os
import sys

import tweepy
from dotenv import load_dotenv

# ── Load environment ───────────────────────────────────────────────────────────
load_dotenv()


def get_client() -> tweepy.Client:
    """Authenticate with Twitter API v2 using Bearer Token (read-only)."""
    bearer = os.getenv("TWITTER_BEARER_TOKEN")
    if not bearer:
        print("[ERROR] TWITTER_BEARER_TOKEN not set in .env")
        sys.exit(1)
    return tweepy.Client(bearer_token=bearer, wait_on_rate_limit=True)


def get_user_tweets(username: str, count: int = 10) -> list[dict]:
    """Fetch the most recent tweets from a user's timeline."""
    client = get_client()

    # Resolve username → user ID
    user = client.get_user(username=username)
    if not user.data:
        print(f"[ERROR] User @{username} not found.")
        sys.exit(1)

    user_id = user.data.id
    response = client.get_users_tweets(
        id=user_id,
        max_results=min(count, 100),
        tweet_fields=["created_at", "public_metrics", "text"],
    )

    tweets = []
    if response.data:
        for tweet in response.data:
            tweets.append({
                "id": tweet.id,
                "text": tweet.text,
                "created_at": str(tweet.created_at),
                "metrics": tweet.public_metrics,
            })

    print(json.dumps(tweets, indent=2))
    return tweets


def get_tweet_by_id(tweet_id: str) -> dict:
    """Fetch details for a specific tweet."""
    client = get_client()
    response = client.get_tweet(
        id=tweet_id,
        tweet_fields=["created_at", "public_metrics", "author_id", "text"],
    )

    if not response.data:
        print(f"[ERROR] Tweet {tweet_id} not found.")
        sys.exit(1)

    tweet = {
        "id": response.data.id,
        "text": response.data.text,
        "created_at": str(response.data.created_at),
        "author_id": response.data.author_id,
        "metrics": response.data.public_metrics,
    }

    print(json.dumps(tweet, indent=2))
    return tweet


def search_tweets(query: str, count: int = 10) -> list[dict]:
    """Search recent tweets matching a query."""
    client = get_client()
    response = client.search_recent_tweets(
        query=query,
        max_results=min(count, 100),
        tweet_fields=["created_at", "public_metrics", "author_id", "text"],
    )

    tweets = []
    if response.data:
        for tweet in response.data:
            tweets.append({
                "id": tweet.id,
                "text": tweet.text,
                "created_at": str(tweet.created_at),
                "author_id": tweet.author_id,
                "metrics": tweet.public_metrics,
            })

    print(json.dumps(tweets, indent=2))
    return tweets


# ── CLI ────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Fetch data from Twitter API v2")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--user", type=str, help="Twitter username (without @)")
    group.add_argument("--tweet-id", type=str, help="Specific tweet ID to fetch")
    group.add_argument("--search", type=str, help="Search query for recent tweets")
    parser.add_argument("--count", type=int, default=10, help="Number of results (default: 10)")
    args = parser.parse_args()

    if args.user:
        get_user_tweets(args.user, args.count)
    elif args.tweet_id:
        get_tweet_by_id(args.tweet_id)
    elif args.search:
        search_tweets(args.search, args.count)


if __name__ == "__main__":
    main()
