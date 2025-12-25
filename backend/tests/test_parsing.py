import unittest
import sys
import os

# Add parent directory to path so we can import backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.council import parse_ranking_from_text

class TestParsing(unittest.TestCase):
    def test_json_parsing_markdown(self):
        text = """
        Here is my evaluation...
        
        ```json
        {
            "ranking": ["Response A", "Response B", "Response C"]
        }
        ```
        """
        result = parse_ranking_from_text(text)
        self.assertEqual(result, ["Response A", "Response B", "Response C"])

    def test_json_parsing_plain(self):
        text = """
        Evaluation finished.
        {
            "ranking": ["Response C", "Response A"]
        }
        """
        result = parse_ranking_from_text(text)
        self.assertEqual(result, ["Response C", "Response A"])

    def test_regex_fallback_numbered(self):
        text = """
        FINAL RANKING:
        1. Response B
        2. Response A
        """
        result = parse_ranking_from_text(text)
        self.assertEqual(result, ["Response B", "Response A"])

    def test_regex_fallback_plain(self):
        text = """
        FINAL RANKING:
        Response C
        Response A
        Response B
        """
        result = parse_ranking_from_text(text)
        self.assertEqual(result, ["Response C", "Response A", "Response B"])

if __name__ == '__main__':
    unittest.main()
