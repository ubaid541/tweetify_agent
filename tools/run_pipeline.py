"""
run_pipeline.py
---------------
Orchestrates the full Tweetify workflow:
1. Check catch-up logic (14-hour rule).
2. Fetch newsletters (today only).
3. Extract AI content.
4. Generate tweet drafts.

Usage:
    python tools/run_pipeline.py
    python tools/run_pipeline.py --force  # bypass catch-up check
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Setup logging
LOG_FILE = Path(".tmp/pipeline.log")
STATE_FILE = Path(".tmp/state.json")

# Ensure we run from the project root regardless of where we are called from
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
os.chdir(PROJECT_ROOT)

Path(".tmp").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

def get_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def run_command(command_list):
    """Run a shell command and return its exit code and output."""
    logging.info(f"Running: {' '.join(command_list)}")
    try:
        result = subprocess.run(
            command_list,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            check=False
        )
        if result.returncode != 0:
            logging.error(f"Command failed with code {result.returncode}")
            logging.error(f"Stderr: {result.stderr}")
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        logging.error(f"Exception during command execution: {e}")
        return 1, "", str(e)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Tweetify Pipeline Orchestrator")
    parser.add_argument("--force", action="store_true", help="Bypass catch-up logic and run now")
    parser.add_argument("--scheduled", action="store_true", help="Indicate this is a scheduled run (bypasses catch-up check)")
    parser.add_argument("--dry-run", action="store_true", help="Run the entire pipeline in dry-run mode (using sample data, no API calls)")
    args = parser.parse_args()

    state = get_state()
    last_run_str = state.get("last_successful_run")
    now = datetime.now()
    
    # Run conditions
    is_catchup_run = False
    if last_run_str:
        last_run = datetime.fromisoformat(last_run_str)
        hours_since = (now - last_run).total_seconds() / 3600
        if hours_since >= 14:
            is_catchup_run = True

    should_run = args.force or args.scheduled or args.dry_run or not last_run_str or is_catchup_run

    if not should_run:
        logging.info("Pipeline run not required at this time (not scheduled and < 14h since last run).")
        return

    if is_catchup_run and not args.scheduled:
        logging.info("Catch-up triggered: > 14 hours since last run.")

    logging.info(f"--- Starting Tweetify Pipeline ({'DRY RUN' if args.dry_run else 'Scheduled' if args.scheduled else 'Manual/Catch-up'}) ---")

    common_args = ["--dry-run"] if args.dry_run else []

    # Step 1: Fetch
    code, stdout, stderr = run_command([sys.executable, "tools/fetch_newsletter.py"] + common_args)
    if code != 0:
        logging.error("Fetch failed. Aborting pipeline.")
        return

    if "No newsletters fetched" in stdout or "All recent emails have already been processed" in stdout:
        logging.info("No new content to process. Pipeline ended.")
        # We still mark this as a 'check' but maybe not a 'successful content run'?
        # User said: "generate tweet drafts from it" - implying if none, do nothing.
        return

    # Step 2: Extract
    code, stdout, stderr = run_command([sys.executable, "tools/extract_ai_content.py"] + common_args)
    if code != 0:
        logging.error("Extraction failed. Aborting pipeline.")
        return

    if "No AI content extracted" in stdout:
        logging.info("Extraction produced no items. Pipeline ended.")
        return

    # Step 3: Generate
    code, stdout, stderr = run_command([sys.executable, "tools/generate_tweets.py", "--count", "5"] + common_args)
    if code != 0:
        logging.error("Generation failed. Aborting pipeline.")
        return

    # Success!
    if not args.dry_run:
        state["last_successful_run"] = now.isoformat()
        save_state(state)
    logging.info("--- Pipeline Completed Successfully ---")

if __name__ == "__main__":
    main()
