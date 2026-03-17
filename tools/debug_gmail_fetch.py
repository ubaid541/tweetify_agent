import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# Basic setup from fetch_newsletter.py
TOKEN_FILE = "token.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
DEFAULT_SENDERS = ["techbrew@morningbrew.com", "futuretools@mail.beehiiv.com"]

def main():
    if not os.path.exists(TOKEN_FILE):
        print(f"Error: {TOKEN_FILE} not found.")
        return

    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    service = build("gmail", "v1", credentials=creds)

    # Broaden search to last 2 days to see what's there
    yesterday = (datetime.now() - timedelta(days=2)).strftime("%Y/%m/%d")
    sender_query = " OR ".join(f"from:{s}" for s in DEFAULT_SENDERS)
    query = f"({sender_query}) after:{yesterday}"
    
    print(f"Searching with query: {query}")
    results = service.users().messages().list(userId="me", q=query, maxResults=20).execute()
    messages = results.get("messages", [])

    if not messages:
        print("No messages found.")
        return

    print(f"Found {len(messages)} candidate messages:")
    for msg_meta in messages:
        msg = service.users().messages().get(userId="me", id=msg_meta["id"], format="metadata").execute()
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        print(f"- ID: {msg_meta['id']}")
        print(f"  From: {headers.get('From')}")
        print(f"  Subject: {headers.get('Subject')}")
        print(f"  Date: {headers.get('Date')}")
        internal_date = int(msg['internalDate']) / 1000
        print(f"  Internal Date: {datetime.fromtimestamp(internal_date).isoformat()}")
        print("-" * 20)

if __name__ == "__main__":
    main()
