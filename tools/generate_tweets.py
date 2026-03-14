"""
generate_tweets.py
──────────────────
Read AI/tech content from .tmp/ai_content_YYYY-MM-DD.json,
generate exactly 3 tweet drafts using Gemini 2.5 Flash,
and save to .tmp/drafts_YYYY-MM-DD.json.

Usage:
    python tools/generate_tweets.py
    python tools/generate_tweets.py --date 2026-03-10
    python tools/generate_tweets.py --input .tmp/ai_content_2026-03-11.json
    python tools/generate_tweets.py --count 5
    python tools/generate_tweets.py --dry-run
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import argparse
import json
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

load_dotenv()
console = Console()

TMP_DIR = Path(".tmp")
MAX_TWEET_LENGTH = 260

TWEET_SYSTEM_PROMPT = """You are a sharp, insightful, and curious human tech voice on Twitter. 
You write tweets that are:
- Punchy and direct — no corporate speak, no filler words
- Human, curious, and slightly opinionated — NOT generic or robotic
- No cringe AI hype language ("game-changing", "revolutionary", "this changes everything")

CRITICAL RULES for every tweet draft:
1. START with a strong hook: a bold claim, a sharp question, or a surprising stat.
2. END with 1-2 relevant hashtags.
3. CREDIT the source exactly at the end: "(via @TechBrew)" or "(via @FutureTools)" depending on the source.
4. The ENTIRE text length must be strictly UNDER 260 characters to leave room for a URL link.

For a single tweet, return an object with:
{
  "text": "the full tweet text here (via @TechBrew) #AI #Tech",
  "char_count": 142,
  "is_thread": false,
  "thread_tweets": null
}

If the story is big enough for a thread (2-3 tweets), set is_thread to true and provide thread_tweets as an array of strings (each strictly under 260 chars).

Return ONLY the raw JSON object."""


def generate_tweet(item: dict, dry_run: bool) -> dict | None:
    """Generate a tweet draft for one content item."""
    if dry_run:
        sample_texts = [
            "GPT-5 just dropped and it's scoring 95% on MMLU. GPT-4o went from frontier to commodity in one announcement. The pace is getting hard to track. #OpenAI #AI",
            "Google's AI Overviews is now live in 100+ countries. Most of the world's searches are now AI-mediated. We skipped the opt-in phase entirely.",
            "Anthropic raised another $2B at a $60B valuation. Investors are betting a lot on \"safe AI\" being a real differentiator. We'll see.",
            "Cursor AI's agent mode can now write, run, and debug code on its own. The IDE is becoming an autonomous dev. Junior devs should pay attention. #AI",
            "OpenAI's Sora rolling out to all ChatGPT Plus users. AI video gen just became a commodity feature, not a lab experiment.",
        ]
        idx = hash(item.get("title", "")) % len(sample_texts)
        text = sample_texts[idx]
        return {
            "title": item.get("title", ""),
            "source_newsletter": item.get("source_newsletter", ""),
            "url": item.get("url"),
            "text": text,
            "char_count": len(text),
            "is_thread": False,
            "thread_tweets": None,
            "status": "pending",
            "generated_at": datetime.now().isoformat(),
        }

    import os
    from google import genai
    from google.genai import types

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        console.print("[bold red]Error:[/bold red] GEMINI_API_KEY not set in .env")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    source_handle = "@TechBrew" if "brew" in item.get('source_newsletter', '').lower() else "@FutureTools"

    prompt = (
        f"Write a tweet about this AI/tech story:\n\n"
        f"Title: {item.get('title')}\n"
        f"Summary: {item.get('summary')}\n"
        f"Key insight: {item.get('key_insight')}\n"
        f"Significance: {item.get('significance', 'medium')}\n"
        f"MANDATORY SOURCE CREDIT: Must end with (via {source_handle})\n"
    )
    if item.get("url"):
        prompt += f"Source URL: {item['url']}\n"

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{TWEET_SYSTEM_PROMPT}\n\n---\n\n{prompt}",
            config=types.GenerateContentConfig(
                temperature=0.75,
                response_mime_type="application/json"
            )
        )

        raw = response.text.strip()
        parsed = json.loads(raw)

        # Enforce char count correctness
        text = parsed.get("text", "")
        if len(text) > MAX_TWEET_LENGTH:
            console.print(f"  [yellow]⚠ Tweet too long ({len(text)} chars), truncating...[/yellow]")
            text = text[:MAX_TWEET_LENGTH - 3] + "..."
            parsed["text"] = text

        return {
            "title": item.get("title", ""),
            "source_newsletter": item.get("source_newsletter", ""),
            "url": item.get("url"),
            "text": text,
            "char_count": len(text),
            "has_hashtags": parsed.get("has_hashtags", "#" in text),
            "is_thread": parsed.get("is_thread", False),
            "thread_tweets": parsed.get("thread_tweets"),
            "status": "pending",
            "generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        console.print(f"  [red]Error generating tweet:[/red] {e}")
        return None


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate tweet drafts from AI content using GPT-4o")
    parser.add_argument("--date", help="Target date YYYY-MM-DD (default: today)")
    parser.add_argument("--input", help="Path to ai_content JSON file (overrides --date)")
    parser.add_argument("--count", type=int, default=5, help="Target number of tweets to generate (default: 5)")
    parser.add_argument("--dry-run", action="store_true", help="Use sample data, no API calls")
    args = parser.parse_args()

    TMP_DIR.mkdir(exist_ok=True)

    if args.input:
        input_file = Path(args.input)
        date_str = datetime.now().strftime("%Y-%m-%d")
    else:
        date_str = args.date or datetime.now().strftime("%Y-%m-%d")
        input_file = TMP_DIR / f"ai_content_{date_str}.json"

    console.print(Panel(
        f"[bold cyan]Tweetify — Tweet Generator[/bold cyan]\n"
        f"Input: {input_file} | Target: 3 tweets",
        expand=False,
    ))

    if not input_file.exists():
        if args.dry_run:
            items = [
                {"title": f"Sample AI Story {i}", "summary": "Summary.", "key_insight": "Insight.", "source_newsletter": "Tech Brew", "significance": "high"}
                for i in range(1, args.count + 1)
            ]
        else:
            console.print(f"[bold red]Error:[/bold red] {input_file} not found.\nRun: python tools/extract_ai_content.py")
            sys.exit(1)
    else:
        with open(input_file, encoding="utf-8") as f:
            items = json.load(f)

    if not items:
        console.print("[bold yellow]No content items found. Exiting.[/bold yellow]")
        sys.exit(0)

    # Sort by significance: high > medium > low
    significance_order = {"high": 0, "medium": 1, "low": 2}
    items.sort(key=lambda x: significance_order.get(x.get("significance", "medium"), 1))

    # Generate tweets up to count limit
    drafts = []
    for item in items[:args.count]:
        console.print(f"[dim]Generating tweet for:[/dim] {item.get('title', 'Unknown')}")
        draft = generate_tweet(item, args.dry_run)
        if draft:
            drafts.append(draft)
            char_count = draft.get("char_count", 0)
            thread_note = " [THREAD]" if draft.get("is_thread") else ""
            console.print(f"  [green]✓[/green] {char_count} chars{thread_note}")

    if not drafts:
        console.print("[bold red]No tweet drafts were generated.[/bold red]")
        sys.exit(1)

    # Check if output file already exists for today and merge
    output_file = TMP_DIR / f"drafts_{date_str}.json"
    existing_drafts = []
    if output_file.exists():
        with open(output_file, encoding="utf-8") as f:
            existing_drafts = json.load(f)
        console.print(f"[dim]Merging with {len(existing_drafts)} existing draft(s)[/dim]")

    all_drafts = existing_drafts + drafts

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_drafts, f, indent=2, ensure_ascii=False)

    console.print(f"\n[bold green]✓ {len(drafts)} new draft(s) saved → {output_file}[/bold green]")
    console.print(f"[dim]Total drafts for {date_str}: {len(all_drafts)}[/dim]")
    console.print("[dim]Next step: python tools/approve_tweets.py[/dim]")


if __name__ == "__main__":
    main()
