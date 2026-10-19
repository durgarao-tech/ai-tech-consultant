
import unittest
from unittest.mock import patch

from claude_brain import generate_grounded_answer


class ClaudeBrainTests(unittest.TestCase):

    def test_empty_question_is_rejected(self):
        result = generate_grounded_answer("", [{"title": "Test"}])
        self.assertEqual(result["status"], "error")

    def test_no_evidence_abstains_without_api_call(self):
        result = generate_grounded_answer(
            "How can I manage users?", []
        )
        self.assertEqual(result["status"], "abstained")
        self.assertEqual(result["sources"], [])

    def test_missing_api_key_is_handled(self):
        with patch.dict("os.environ", {}, clear=True):
            result = generate_grounded_answer(
                "How can I manage users?",
                [{"title": "Users API", "url": "https://example.com",
                  "content": "Documentation about users."}],
            )

        self.assertEqual(result["status"], "unavailable")
        self.assertIn("not configured", result["error"])

    def test_successful_response_can_be_mocked(self):
        fake_response = type(
            "FakeResponse",
            (),
            {
                "content": [
                    type(
                        "TextBlock",
                        (),
                        {"type": "text", "text": "Use the Users API."},
                    )()
                ]
            },
        )()

        with patch("claude_brain.Anthropic") as mock_anthropic:
            mock_client = mock_anthropic.return_value
            mock_client.messages.create.return_value = fake_response

            with patch.dict(
                "os.environ",
                {"ANTHROPIC_API_KEY": "test-only-placeholder"},
            ):
                result = generate_grounded_answer(
                    "How can I manage users?",
                    [{
                        "title": "Users API",
                        "url": "https://example.com/users",
                        "content": "The Users API manages users.",
                    }],
                )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["answer"], "Use the Users API.")
        mock_client.messages.create.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
