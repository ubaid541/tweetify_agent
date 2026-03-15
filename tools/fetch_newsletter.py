"""
fetch_newsletter.py
-------------------
Fetch newsletter emails from Gmail for the configured senders.
Converts HTML body to clean markdown and saves to .tmp/newsletter_YYYY-MM-DD.json.
Tracks processed message IDs to avoid duplicates.

Usage:
    python tools/fetch_newsletter.py
    python tools/fetch_newsletter.py --date 2026-03-10   # fetch for specific date
    python tools/fetch_newsletter.py --dry-run            # use sample data, no API calls
    python tools/fetch_newsletter.py --days-back 3        # look back N days (default 1)
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import argparse
import base64
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

load_dotenv()
console = Console()

# ── Constants ─────────────────────────────────────────────────────────────────
TMP_DIR = Path(".tmp")
PROCESSED_IDS_FILE = TMP_DIR / "processed_ids.json"
CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "token.json")
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

DEFAULT_SENDERS = [
    # "crew@community.morningbrew.com",
    "techbrew@morningbrew.com",
    "futuretools@mail.beehiiv.com",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_processed_ids() -> set:
    if PROCESSED_IDS_FILE.exists():
        with open(PROCESSED_IDS_FILE) as f:
            return set(json.load(f))
    return set()


def save_processed_ids(ids: set):
    TMP_DIR.mkdir(exist_ok=True)
    with open(PROCESSED_IDS_FILE, "w") as f:
        json.dump(list(ids), f, indent=2)


def decode_body(data: str) -> str:
    """Decode base64url-encoded email body."""
    padding = 4 - len(data) % 4
    data += "=" * padding
    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")


def extract_html_or_text(payload: dict) -> tuple[str, str]:
    """Recursively extract best available body from email payload."""
    mime = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data", "")

    if mime == "text/html" and body_data:
        return decode_body(body_data), "html"
    if mime == "text/plain" and body_data:
        return decode_body(body_data), "plain"

    # Multipart: prefer HTML part
    plain_result: tuple[str, str] | None = None
    for part in payload.get("parts", []):
        result = extract_html_or_text(part)
        if result[1] == "html" and result[0]:
            return result
        elif result[1] == "plain" and result[0] and not plain_result:
            plain_result = result
            
    if plain_result is not None:
        return plain_result

    return "", "plain"


def html_to_markdown(html: str) -> str:
    """Convert HTML to clean markdown using html2text."""
    try:
        import html2text
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.ignore_emphasis = False
        h.body_width = 0  # no line wrapping
        return h.handle(html)
    except ImportError:
        console.print("[yellow]html2text not installed, falling back to plain stripping[/yellow]")
        import re
        clean = re.sub(r"<[^>]+>", " ", html)
        return " ".join(clean.split())


def get_gmail_service():
    """Authenticate and return Gmail API service."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if Path(TOKEN_FILE).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(CREDENTIALS_FILE).exists():
                console.print(
                    f"[bold red]Error:[/bold red] {CREDENTIALS_FILE} not found.\n"
                    "Download it from Google Cloud Console → APIs & Services → Credentials.\n"
                    "See workflows/fetch_newsletter.md for setup instructions."
                )
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def fetch_newsletters(senders: list[str], dry_run: bool) -> list[dict]:
    """Fetch newsletter emails from Gmail."""
    if dry_run:
        console.print("[dim]DRY RUN: Using sample newsletter data[/dim]")
        return [
            {
                "id": "dry_run_001",
                "source": "techbrew@morningbrew.com",
                "subject": "[DRY RUN] Tech Brew — March 13, 2026",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "content": (
                    "# Tech Brew — Sample\n\n"
                    "## OpenAI releases GPT-5\n"
                    "OpenAI has released GPT-5 with major improvements in reasoning and multimodal understanding. "
                    "The new model scores 95% on the MMLU benchmark.\n\n"
                    "## Google's AI Overviews expands to 100 countries\n"
                    "Google's AI-powered search summary feature now covers 100+ countries and 40+ languages.\n\n"
                    "## Anthropic raises $2B at $60B valuation\n"
                    "Anthropic closed a new funding round, bringing total raised to $7.6B.\n"
                ),
            },
            {
                "id": "dry_run_002",
                "source": "futuretools@mail.beehiiv.com",
                "subject": "[DRY RUN] Future Tools Weekly — March 13, 2026",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "content": (
                    "# Future Tools — Sample\n\n"
                    "## Tool of the Week: Cursor AI\n"
                    "Cursor AI just added agent mode that writes, runs, and debugs code autonomously.\n\n"
                    "## Sora now available to all ChatGPT Plus users\n"
                    "OpenAI's video generation model Sora is rolling out to all Plus subscribers.\n\n"
                    "## ElevenLabs launches voice cloning API v3\n"
                    "New API allows real-time voice cloning with under 10 seconds of sample audio.\n"
                ),
            },
        ]

    service = get_gmail_service()
    processed_ids = load_processed_ids()

    newsletters = []
    new_ids = set()

    # Build query: emails from ANY sender
    sender_query = " OR ".join(f"from:{s}" for s in senders)
    # Filter for today's emails (since:YYYY/MM/DD)
    today_str = datetime.now().strftime("%Y/%m/%d")
    query = f"({sender_query}) after:{today_str}"

    console.print(f"[dim]Gmail query:[/dim] {query} (fetching latest candidates)")

    # Fetch more results to find the most recent ones for all configured senders
    results = service.users().messages().list(userId="me", q=query, maxResults=15).execute()
    messages = results.get("messages", [])

    if not messages:
        console.print("[yellow]No emails found from any configured senders.[/yellow]")
        return []

    # Strategy: Find ONE latest unseen message FOR EACH sender
    sender_seen = set()

    for msg_meta in messages:
        msg_id = msg_meta["id"]
        
        if msg_id in processed_ids:
            continue

        msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}

        subject = headers.get("Subject", "No Subject")
        source = headers.get("From", "Unknown")
        
        # Match sender case-insensitively
        matched_sender = None
        source_lower = source.lower()
        for s in senders:
            if s.lower() in source_lower:
                matched_sender = s
                break
        
        if not matched_sender:
            continue
            
        # If we already got the latest for this sender in this run, skip
        if matched_sender in sender_seen:
            continue

        raw_content, mime_type = extract_html_or_text(msg["payload"])
        if mime_type == "html":
            content = html_to_markdown(raw_content)
        else:
            content = raw_content

        newsletters.append({
            "id": msg_id,
            "source": matched_sender,
            "subject": subject,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "content": content,
        })
        new_ids.add(msg_id)
        sender_seen.add(matched_sender)
        console.print(f"[green]✓[/green] Fetched: [bold]{subject}[/bold] from {matched_sender}")
        
        # If we've found one for every configured sender, we can stop
        if len(sender_seen) == len(senders):
            break

    if not newsletters:
        console.print("[yellow]All recent emails have already been processed.[/yellow]")

    # Persist processed IDs
    save_processed_ids(processed_ids | new_ids)
    return newsletters


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Fetch newsletter emails from Gmail")
    parser.add_argument("--date", help="Target date YYYY-MM-DD (default: today)")
    parser.add_argument("--days-back", type=int, default=1, help="How many days back to look (default: 1)")
    parser.add_argument("--dry-run", action="store_true", help="Use sample data, no API calls")
    parser.add_argument(
        "--senders",
        default=",".join(DEFAULT_SENDERS),
        help="Comma-separated list of sender emails to fetch from",
    )
    args = parser.parse_args()

    TMP_DIR.mkdir(exist_ok=True)

    target_date = datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.now()
    date_str = target_date.strftime("%Y-%m-%d")

    senders = [s.strip() for s in args.senders.split(",")]

    console.print(Panel(
        f"[bold cyan]Tweetify — Newsletter Fetcher[/bold cyan]\n"
        f"Mode: Fetching single latest unseen email\n"
        f"Senders: {', '.join(senders)}",
        expand=False,
    ))

    newsletters = fetch_newsletters(senders, args.dry_run)

    if not newsletters:
        console.print("[bold yellow]No newsletters fetched. Nothing to save.[/bold yellow]")
        sys.exit(0)

    output_file = TMP_DIR / f"newsletter_{date_str}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(newsletters, f, indent=2, ensure_ascii=False)

    console.print(f"\n[bold green]✓ Saved {len(newsletters)} newsletter(s) → {output_file}[/bold green]")
    console.print("[dim]Next step: python tools/extract_ai_content.py[/dim]")


if __name__ == "__main__":
    main()
