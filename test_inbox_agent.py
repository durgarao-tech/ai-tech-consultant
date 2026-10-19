
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import inbox_agent


class InboxAgentTests(unittest.TestCase):

    def test_billing_email_is_classified(self):
        result = inbox_agent.classify_email(
            "Invoice payment issue",
            "I need help with my invoice and payment.",
        )

        self.assertEqual(result["category"], "billing")
        self.assertEqual(result["method"], "keyword_rules")

    def test_urgent_email_gets_high_priority(self):
        result = inbox_agent.classify_email(
            "Urgent support request",
            "The system is down. Please help immediately.",
        )

        self.assertEqual(result["priority"], "high")

    def test_empty_email_is_rejected(self):
        with self.assertRaises(ValueError):
            inbox_agent.process_email({
                "subject": "",
                "body": "",
            })

    def test_human_approval_never_sends_email(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            audit_path = Path(temp_dir) / "audit.jsonl"

            with patch.object(inbox_agent, "AUDIT_FILE", audit_path):
                result = inbox_agent.record_human_decision(
                    "approved",
                    "Test subject",
                    "Reviewed by human",
                )

            self.assertEqual(result["decision"], "approved")
            self.assertFalse(result["email_sent"])

            record = json.loads(
                audit_path.read_text(encoding="utf-8").strip()
            )
            self.assertEqual(record["event"], "human_review")
            self.assertEqual(record["decision"], "approved")
            self.assertFalse(record["email_sent"])

    def test_invalid_human_decision_is_rejected(self):
        with self.assertRaises(ValueError):
            inbox_agent.record_human_decision(
                "send_automatically",
                "Test subject",
            )

    def test_draft_requires_human_review(self):
        email = {
            "subject": "How can I manage users?",
            "body": "Please explain account management.",
        }

        evidence = {
            "status": "success",
            "results": [
                {
                    "title": "Users API",
                    "url": "https://example.com/users",
                }
            ],
        }

        result = inbox_agent.build_draft(email, evidence)

        self.assertTrue(result["approval_required"])
        self.assertEqual(result["status"], "draft_ready_for_review")
        self.assertEqual(len(result["sources"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
