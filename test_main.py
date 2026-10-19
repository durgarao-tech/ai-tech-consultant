
import unittest
from unittest.mock import patch

import main


class AnswerEndpointTests(unittest.TestCase):

    @patch("main.generate_grounded_answer")
    def test_supported_question_returns_answer_and_sources(
        self, mock_claude
    ):
        mock_claude.return_value = {
            "status": "success",
            "answer": "Use the Users API to manage users.",
        }

        response = main.answer_question(
            q="How can I manage users with API calls?",
            limit=5,
        )

        self.assertEqual(response["status"], "success")
        self.assertIn("answer", response)
        self.assertTrue(response["sources"])
        self.assertEqual(response["evidence_coverage"], 1.0)
        mock_claude.assert_called_once()

    @patch("main.generate_grounded_answer")
    def test_unsupported_question_abstains(
        self, mock_claude
    ):
        response = main.answer_question(
            q="What is the weather on Mars today?",
            limit=5,
        )

        self.assertEqual(response["status"], "abstained")
        self.assertEqual(response["sources"], [])
        mock_claude.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
