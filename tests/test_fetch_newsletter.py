import unittest
from unittest.mock import MagicMock, patch
import json
import base64
from pathlib import Path
import sys
import os

# Add tools directory to path so we can import fetch_newsletter
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tools')))
import fetch_newsletter

class TestFetchNewsletter(unittest.TestCase):
    def test_decode_body(self):
        # Test basic base64url decoding
        test_str = "SGVsbG8gV29ybGQ" # "Hello World" without padding
        decoded = fetch_newsletter.decode_body(test_str)
        self.assertEqual(decoded, "Hello World")

    def test_extract_html_or_text_plain(self):
        payload = {
            "mimeType": "text/plain",
            "body": {"data": base64.urlsafe_b64encode(b"Plain text body").decode()}
        }
        content, mime = fetch_newsletter.extract_html_or_text(payload)
        self.assertEqual(content, "Plain text body")
        self.assertEqual(mime, "plain")

    def test_extract_html_or_text_html(self):
        payload = {
            "mimeType": "text/html",
            "body": {"data": base64.urlsafe_b64encode(b"<html><body>HTML body</body></html>").decode()}
        }
        content, mime = fetch_newsletter.extract_html_or_text(payload)
        self.assertEqual(content, "<html><body>HTML body</body></html>")
        self.assertEqual(mime, "html")

    def test_extract_html_or_text_multipart(self):
        payload = {
            "mimeType": "multipart/alternative",
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": base64.urlsafe_b64encode(b"Plain part").decode()}
                },
                {
                    "mimeType": "text/html",
                    "body": {"data": base64.urlsafe_b64encode(b"HTML part").decode()}
                }
            ]
        }
        content, mime = fetch_newsletter.extract_html_or_text(payload)
        self.assertEqual(content, "HTML part")
        self.assertEqual(mime, "html")

    @patch('fetch_newsletter.PROCESSED_IDS_FILE', Path('.tmp/test_processed_ids.json'))
    def test_processed_ids_storage(self):
        # Ensure .tmp exists
        Path('.tmp').mkdir(exist_ok=True)
        
        ids = {"id1", "id2"}
        fetch_newsletter.save_processed_ids(ids)
        
        loaded_ids = fetch_newsletter.load_processed_ids()
        self.assertEqual(loaded_ids, ids)
        
        # Cleanup
        if Path('.tmp/test_processed_ids.json').exists():
            Path('.tmp/test_processed_ids.json').unlink()

if __name__ == '__main__':
    unittest.main()
