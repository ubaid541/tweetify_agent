"""
approve_tweets.py
─────────────────
Interactive Rich terminal UI for reviewing tweet drafts.
Lets you approve, edit, or skip each draft.
Approved tweets are saved with status "approved" — you post them manually.

Usage:
    python tools/approve_tweets.py
    python tools/approve_tweets.py --date 2026-03-10
    python tools/approve_tweets.py --input .tmp/drafts_2026-03-11.json
    python tools/approve_tweets.py --dry-run     # loads today's drafts read-only
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import argparse
import json
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from rich.columns import Columns
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

load_dotenv()
console = Console()

TMP_DIR = Path(".tmp")


def display_draft(draft: dict, index: int, total: int):
    """Display a single tweet draft in a formatted panel."""
    text = draft.get("text", "")
    char_count = draft.get("char_count", len(text))
    is_thread = draft.get("is_thread", False)
    thread_tweets = draft.get("thread_tweets")
    source = draft.get("source_newsletter", "")
    title = draft.get("title", "")
    url = draft.get("url")
    status = draft.get("status", "pending")

    char_color = "green" if char_count <= 240 else "yellow" if char_count <= 270 else "red"
    type_label = "🧵 THREAD" if is_thread else "TWEET"

    # Header info
    header = f"[bold]Draft {index}/{total}[/bold]  |  {type_label}  |  [{char_color}]{char_count}/280 chars[/{char_color}]"
    if source:
        header += f"  |  [dim]{source}[/dim]"

    # Build content
    content_lines = []
    if title:
        content_lines.append(f"[dim italic]Story: {title}[/dim italic]")
    if url:
        content_lines.append(f"[dim]Source: {url}[/dim]")
    content_lines.append("")

    if is_thread and thread_tweets:
        for i, t in enumerate(thread_tweets, 1):
            content_lines.append(f"[bold]Tweet {i}/{len(thread_tweets)}:[/bold]")
            content_lines.append(f"[white]{t}[/white]")
            content_lines.append(f"[dim]{len(t)}/280 chars[/dim]")
            content_lines.append("")
    else:
        content_lines.append(f"[white bold]{text}[/white bold]")

    console.print(Panel(
        "\n".join(content_lines),
        title=header,
        border_style="cyan" if status == "pending" else "yellow",
        padding=(1, 2),
    ))


def prompt_action(dry_run: bool) -> str:
    """Display action menu and get user choice."""
    options = [
        ("[A] Approve", "green"),
        ("[E] Edit", "yellow"),
        ("[S] Skip", "dim"),
        ("[Q] Quit", "red"),
    ]
    parts = [Text(label, style=color) for label, color in options]
    console.print("  ", end="")
    for i, part in enumerate(parts):
        console.print(part, end="")
        if i < len(parts) - 1:
            console.print("  ", end="")
    console.print()

    choice = Prompt.ask("  Action", choices=["a", "e", "s", "q", "A", "E", "S", "Q"], default="s").lower()
    return choice


def inline_edit(draft: dict) -> dict:
    """Allow user to edit tweet text inline."""
    current = draft.get("text", "")
    console.print(f"\n[dim]Current text ({len(current)} chars):[/dim]")
    console.print(f"[yellow]{current}[/yellow]\n")
    console.print("[dim]Type new tweet text below (press Enter twice to confirm, or just Enter to keep current):[/dim]")

    try:
        new_lines = []
        while True:
            line = input()
            if not line and not new_lines:
                # Just Enter with no content — keep original
                console.print("[dim]Keeping original text.[/dim]")
                return draft
            if not line and new_lines:
                break
            new_lines.append(line)

        new_text = " ".join(new_lines).strip()

        if not new_text:
            console.print("[dim]No change made.[/dim]")
            return draft

        if len(new_text) > 280:
            console.print(f"[red]⚠ Text is {len(new_text)} chars — exceeds 280! Trimming to 280.[/red]")
            new_text = new_text[:277] + "..."

        draft["text"] = new_text
        draft["char_count"] = len(new_text)
        draft["edited"] = True
        console.print(f"[green]✓ Updated ({len(new_text)} chars)[/green]")
        return draft

    except (EOFError, KeyboardInterrupt):
        console.print("\n[dim]Edit cancelled.[/dim]")
        return draft


def show_summary(drafts: list[dict], date_str: str):
    """Show a summary table of all drafts and their statuses."""
    table = Table(title=f"Draft Summary — {date_str}", show_lines=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Status", width=10)
    table.add_column("Tweet", style="white")
    table.add_column("Chars", width=6)

    for i, draft in enumerate(drafts, 1):
        status = draft.get("status", "pending")
        status_styles = {
            "approved": "[bold green]✓ Approved[/bold green]",
            "skipped": "[dim]⊘ Skipped[/dim]",
            "pending": "[yellow]◌ Pending[/yellow]",
        }
        status_display = status_styles.get(status, status)
        text = draft.get("text", "")
        preview = (text[:60] + "...") if len(text) > 60 else text
        table.add_row(str(i), status_display, preview, str(draft.get("char_count", len(text))))

    console.print(table)

    approved = [d for d in drafts if d.get("status") == "approved"]
    if approved:
        console.print(f"\n[bold green]✓ {len(approved)} tweet(s) approved and ready to post![/bold green]")
        console.print("\n[bold]─── Your Approved Tweets ───[/bold]\n")
        for i, d in enumerate(approved, 1):
            console.print(Panel(
                d.get("text", ""),
                title=f"[green]Tweet {i}[/green]  |  {d.get('char_count', 0)}/280 chars",
                border_style="green",
                padding=(1, 2),
            ))
            if d.get("is_thread") and d.get("thread_tweets"):
                for j, t in enumerate(d["thread_tweets"], 1):
                    console.print(Panel(
                        t,
                        title=f"[green]  Thread tweet {j}[/green]",
                        border_style="dark_green",
                        padding=(0, 2),
                    ))

        console.print(
            "\n[bold yellow]→ Copy and paste the tweet(s) above to post them manually on X/Twitter.[/bold yellow]"
        )
    else:
        console.print("[yellow]No tweets approved in this session.[/yellow]")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Review and approve tweet drafts")
    parser.add_argument("--date", help="Target date YYYY-MM-DD (default: today)")
    parser.add_argument("--input", help="Path to drafts JSON file (overrides --date)")
    parser.add_argument("--dry-run", action="store_true", help="Show drafts without saving changes")
    args = parser.parse_args()

    TMP_DIR.mkdir(exist_ok=True)

    if args.input:
        drafts_file = Path(args.input)
        date_str = datetime.now().strftime("%Y-%m-%d")
    else:
        date_str = args.date or datetime.now().strftime("%Y-%m-%d")
        drafts_file = TMP_DIR / f"drafts_{date_str}.json"

    console.print(Panel(
        f"[bold cyan]Tweetify — Tweet Approval UI[/bold cyan]\n"
        f"[dim]Date: {date_str} | File: {drafts_file}[/dim]",
        expand=False,
    ))

    if not drafts_file.exists():
        console.print(f"[bold red]Error:[/bold red] {drafts_file} not found.\nRun: python tools/generate_tweets.py")
        sys.exit(1)

    with open(drafts_file, encoding="utf-8") as f:
        drafts = json.load(f)

    if not drafts:
        console.print("[bold yellow]No drafts found in file.[/bold yellow]")
        sys.exit(0)

    # Only show pending drafts in the review loop
    pending = [d for d in drafts if d.get("status", "pending") == "pending"]
    already_reviewed = [d for d in drafts if d.get("status") != "pending"]

    if not pending:
        console.print("[bold yellow]All drafts have already been reviewed.[/bold yellow]")
        show_summary(drafts, date_str)
        sys.exit(0)

    console.print(f"\n[bold]{len(pending)} pending draft(s) to review[/bold]  (press Ctrl+C to quit at any time)\n")

    for i, draft in enumerate(pending, 1):
        console.print(Rule())
        display_draft(draft, i, len(pending))

        if args.dry_run:
            console.print("[dim](DRY RUN — no changes will be saved)[/dim]")
            continue

        action = prompt_action(args.dry_run)

        if action == "q":
            console.print("[dim]Quitting review session...[/dim]")
            break
        elif action == "a":
            draft["status"] = "approved"
            draft["approved_at"] = datetime.now().isoformat()
            console.print(f"[bold green]✓ Approved![/bold green]\n")
        elif action == "e":
            draft = inline_edit(draft)
            draft["status"] = "approved"
            draft["approved_at"] = datetime.now().isoformat()
            console.print(f"[bold green]✓ Edited & approved![/bold green]\n")
            # Update reference in all_drafts
            idx_in_all = drafts.index(pending[i - 1])
            drafts[idx_in_all] = draft
            pending[i - 1] = draft
            continue
        elif action == "s":
            draft["status"] = "skipped"
            console.print("[dim]⊘ Skipped\n[/dim]")

        # Update in master drafts list
        idx_in_all = next(
            (j for j, d in enumerate(drafts) if d.get("generated_at") == draft.get("generated_at") and d.get("title") == draft.get("title")),
            -1,
        )
        if idx_in_all >= 0:
            drafts[idx_in_all] = draft

    # Save updated statuses
    if not args.dry_run:
        with open(drafts_file, "w", encoding="utf-8") as f:
            json.dump(drafts, f, indent=2, ensure_ascii=False)
        console.print(f"\n[dim]Saved review results → {drafts_file}[/dim]")

    console.print(Rule())
    show_summary(drafts, date_str)


if __name__ == "__main__":
    main()
