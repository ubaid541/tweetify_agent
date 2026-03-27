import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os
from pathlib import Path

# Add tools directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tools')))
import extract_ai_content

class TestExtractAIContent(unittest.TestCase):
    def test_extract_with_llm_dry_run(self):
        # Test dry-run returns sample data
        items = extract_ai_content.extract_with_llm("some content", "Source A", dry_run=True)
        self.assertIsInstance(items, list)
        self.assertTrue(len(items) > 0)
        self.assertEqual(items[0]["source_newsletter"], "Source A")

    def test_llm_response_parsing_list_of_objects(self):
        with patch('openai.OpenAI') as MockClient:
            mock_client_instance = MockClient.return_value
            mock_response = MagicMock()
            mock_response.choices[0].message.content = json.dumps([
                {"title": "Title 1", "summary": "Sum 1", "key_insight": "In 1", "source_newsletter": "N1", "url": None, "significance": "high"}
            ])
            mock_client_instance.chat.completions.create.return_value = mock_response
            
            with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"}):
                items = extract_ai_content.extract_with_llm("content", "N1", dry_run=False)
                self.assertEqual(len(items), 1)
                self.assertEqual(items[0]["title"], "Title 1")

    def test_llm_response_parsing_wrapped_list(self):
        with patch('openai.OpenAI') as MockClient:
            mock_client_instance = MockClient.return_value
            mock_response = MagicMock()
            mock_response.choices[0].message.content = json.dumps({
                "items": [
                    {"title": "Title 1", "summary": "Sum 1", "key_insight": "In 1", "source_newsletter": "N1", "url": None, "significance": "high"}
                ]
            })
            mock_client_instance.chat.completions.create.return_value = mock_response
            
            with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test_key"}):
                items = extract_ai_content.extract_with_llm("content", "N1", dry_run=False)
                self.assertEqual(len(items), 1)
                self.assertEqual(items[0]["title"], "Title 1")

if __name__ == '__main__':
    unittest.main()
