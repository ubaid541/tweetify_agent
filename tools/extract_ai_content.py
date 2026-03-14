"""
extract_ai_content.py
─────────────────────
Read newsletter markdown from .tmp/newsletter_YYYY-MM-DD.json,
extract only AI and emerging-tech relevant items using GPT-4o,
and save structured results to .tmp/ai_content_YYYY-MM-DD.json.

Usage:
    python tools/extract_ai_content.py
    python tools/extract_ai_content.py --date 2026-03-10
    python tools/extract_ai_content.py --input .tmp/newsletter_2026-03-11.json
    python tools/extract_ai_content.py --dry-run
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
from rich.table import Table

load_dotenv()
console = Console()

TMP_DIR = Path(".tmp")

EXTRACTION_SYSTEM_PROMPT = """You are an expert AI/tech journalist and newsletter analyst.

Your job is to read newsletter content and extract ONLY the stories, tools, research, or announcements that are specifically about:
- Artificial Intelligence (AI models, LLMs, agents, multimodal AI, etc.)
- Machine Learning / Deep Learning
- AI-powered products and tools
- AI companies, funding, and industry news
- Emerging technology closely tied to AI (robotics with AI, AI chips, etc.)

Do NOT include:
- General business/finance news unrelated to AI/tech
- Lifestyle, food, sports, or entertainment
- Marketing or politics content
- Generic tech not related to AI

Return a JSON array of objects. Each object must have exactly these fields:
{
  "title": "Short clear title for the story (max 10 words)",
  "summary": "2-3 sentence factual summary of the story",
  "key_insight": "The most tweet-worthy angle or takeaway (1 sentence)",
  "source_newsletter": "Name of the newsletter this came from",
  "url": "URL if mentioned in the content, else null",
  "significance": "high | medium | low"
}

Return ONLY the raw JSON array. No markdown, no explanation."""


def extract_with_llm(newsletter_content: str, source: str, dry_run: bool) -> list[dict]:
    """Call GPT-4o to extract AI/tech content items from newsletter text."""
    if dry_run:
        return [
            {
                "title": "OpenAI releases GPT-5",
                "summary": "OpenAI has released GPT-5 with major improvements in reasoning and multimodal understanding. The model scores 95% on MMLU benchmark.",
                "key_insight": "GPT-5 could make GPT-4o obsolete almost overnight for most real-world tasks.",
                "source_newsletter": source,
                "url": None,
                "significance": "high",
            },
            {
                "title": "Google AI Overviews hits 100 countries",
                "summary": "Google's AI-powered search summaries now available in 100+ countries and 40+ languages, reshaping how billions search.",
                "key_insight": "AI is now the default search experience for most of the world's internet users.",
                "source_newsletter": source,
                "url": None,
                "significance": "high",
            },
        ]

    import os
    from google import genai
    from google.genai import types

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        console.print("[bold red]Error:[/bold red] GEMINI_API_KEY not set in .env")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    truncated = newsletter_content[:15000]  # Reduced to 15k to guarantee fast generation and avoid silent timeouts
    
    console.print(f"  [dim]↳ Sending {len(truncated)} chars to Gemini API...[/dim]")

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{EXTRACTION_SYSTEM_PROMPT}\n\nNewsletter source: {source}\n\n---\n\n{truncated}",
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        raw = response.text.strip()
        console.print("  [dim]↳ Response received from Gemini[/dim]")
    except Exception as e:
        console.print(f"  [bold red]Error from Gemini API:[/bold red]\n{str(e)}")
        return []

    # GPT returns {"items": [...]} or just [...] — handle both
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        console.print(f"[red]JSON parse error:[/red] {e}\nRaw response:\n{raw[:500]}")
        return []

    if isinstance(parsed, list):
        return parsed
    # Try to find the array in a wrapper object
    for v in parsed.values():
        if isinstance(v, list):
            return v
    return []


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Extract AI/tech content from newsletters via LLM")
    parser.add_argument("--date", help="Target date YYYY-MM-DD (default: today)")
    parser.add_argument("--input", help="Path to newsletter JSON file (overrides --date)")
    parser.add_argument("--dry-run", action="store_true", help="Use sample data, no API calls")
    args = parser.parse_args()

    TMP_DIR.mkdir(exist_ok=True)

    if args.input:
        input_file = Path(args.input)
        date_str = datetime.now().strftime("%Y-%m-%d")
    else:
        date_str = args.date or datetime.now().strftime("%Y-%m-%d")
        input_file = TMP_DIR / f"newsletter_{date_str}.json"

    console.print(Panel(
        f"[bold cyan]Tweetify — AI Content Extractor[/bold cyan]\n"
        f"Input: {input_file}",
        expand=False,
    ))

    if not input_file.exists():
        if args.dry_run:
            # Create a minimal placeholder for dry-run
            newsletters = [{"id": "dr1", "source": "crew@community.morningbrew.com", "content": "sample"}]
        else:
            console.print(f"[bold red]Error:[/bold red] {input_file} not found.\nRun: python tools/fetch_newsletter.py")
            sys.exit(1)
    else:
        with open(input_file, encoding="utf-8") as f:
            newsletters = json.load(f)

    all_items = []
    for newsletter in newsletters:
        source = newsletter.get("source", "Unknown")
        content = newsletter.get("content", "")
        subject = newsletter.get("subject", "")

        console.print(f"\n[bold]Processing:[/bold] {subject or source}")

        items = extract_with_llm(content, source, args.dry_run)
        if items:
            # Add source and date to each item before extending
            for item in items:
                item["source_newsletter"] = source
                item["date"] = newsletter.get("date")
            all_items.extend(items)
        else:
            console.print("  [yellow]No AI/tech items found in this newsletter.[/yellow]")

    # Sort globally by significance to get the absolute best stories
    all_items = sorted(
        all_items,
        key=lambda x: {"high": 3, "medium": 2, "low": 1}.get(str(x.get("significance")).lower(), 0),
        reverse=True
    )[:3]  # Global cap at exactly 3 items

    if not all_items:
        console.print("\n[bold yellow]No AI content extracted. Nothing to save.[/bold yellow]")
        sys.exit(0)

    # Assign IDs globally
    for idx, item in enumerate(all_items):
        item["id"] = f"{date_str}_{idx+1:03d}"

    # Display summary table
    table = Table(title=f"Extracted AI/Tech Items — {date_str}", show_lines=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Title", style="bold")
    table.add_column("Significance", style="cyan", width=10)
    table.add_column("Newsletter", style="dim", width=15)

    for i, item in enumerate(all_items, 1):
        sig = item.get("significance", "medium")
        sig_display = {"high": "[red]HIGH[/red]", "medium": "[yellow]MED[/yellow]", "low": "[dim]LOW[/dim]"}.get(sig, sig)
        table.add_row(str(i), item.get("title", ""), sig_display, item.get("source_newsletter", ""))

    console.print(table)

    output_file = TMP_DIR / f"ai_content_{date_str}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_items, f, indent=2, ensure_ascii=False)

    console.print(f"\n[bold green]✓ Saved {len(all_items)} item(s) → {output_file}[/bold green]")
    console.print("[dim]Next step: python tools/generate_tweets.py[/dim]")


if __name__ == "__main__":
    main()
