import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os
from pathlib import Path

# Add tools directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tools')))
import generate_tweets

class TestGenerateTweets(unittest.TestCase):
    def test_generate_tweet_dry_run(self):
        item = {"title": "Test Title", "source_newsletter": "Test News", "summary": "Test Summary", "key_insight": "Test Insight"}
        draft = generate_tweets.generate_tweet(item, dry_run=True)
        self.assertIsInstance(draft, dict)
        self.assertEqual(draft["title"], "Test Title")
        self.assertEqual(draft["status"], "pending")

    def test_tweet_length_enforcement_short(self):
        mock_item = {"title": "T", "source_newsletter": "N", "summary": "S", "key_insight": "I"}
        
        with patch('openai.OpenAI') as MockClient:
            mock_client_instance = MockClient.return_value
            mock_response = MagicMock()
            long_text = "A" * 300
            mock_response.choices[0].message.content = json.dumps({
                "text": long_text,
                "char_count": 300,
                "is_thread": False
            })
            mock_client_instance.chat.completions.create.return_value = mock_response
            
            with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test"}):
                draft = generate_tweets.generate_tweet(mock_item, dry_run=False)
                # Max for short is now 274
                self.assertEqual(len(draft["text"]), 274)
                self.assertTrue(draft["text"].endswith("..."))

    def test_tweet_length_enforcement_thread(self):
        mock_item = {"title": "T", "source_newsletter": "N", "summary": "S", "key_insight": "I"}
        
        with patch('openai.OpenAI') as MockClient:
            mock_client_instance = MockClient.return_value
            mock_response = MagicMock()
            long_text = "A" * 300
            mock_response.choices[0].message.content = json.dumps({
                "text": long_text,
                "char_count": 300,
                "is_thread": True
            })
            mock_client_instance.chat.completions.create.return_value = mock_response
            
            with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test"}):
                draft = generate_tweets.generate_tweet(mock_item, dry_run=False)
                # Max for thread is now 289
                self.assertEqual(len(draft["text"]), 289)

if __name__ == '__main__':
    unittest.main()
