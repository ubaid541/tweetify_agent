import os
import json
from pathlib import Path
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def main():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)

    senders = ["techbrew@morningbrew.com", "futuretools@mail.beehiiv.com"]
    sender_query = " OR ".join(f"from:{s}" for s in senders)
    
    print(f"Searching for: {sender_query}")
    results = service.users().messages().list(userId="me", q=sender_query, maxResults=10).execute()
    messages = results.get("messages", [])

    if not messages:
        print("No messages found.")
        return

    for msg_meta in messages:
        msg = service.users().messages().get(userId="me", id=msg_meta['id'], format='minimal').execute()
        headers = msg['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
        print(f"ID: {msg_meta['id']}, Date: {date}, From: {from_email}, Subject: {subject}")

if __name__ == "__main__":
    main()
