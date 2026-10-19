
import unittest
from unittest.mock import patch, Mock

from meeting_scope import (
    extract_requirements,
    compare_meetings,
    create_estimate,
    record_approval,
    search_knowledge_brain,
)


class TestMeetingScope(unittest.TestCase):

    def test_empty_transcript_is_rejected(self):
        with self.assertRaises(ValueError):
            extract_requirements("")

    def test_transcript_lines_keep_source_locations(self):
        requirements = extract_requirements(
            "Customer: Manage users\nCustomer: Search by email"
        )
        self.assertEqual(len(requirements), 2)
        self.assertEqual(requirements[0]["source_line"], 1)
        self.assertEqual(requirements[1]["source_line"], 2)

    def test_requirements_are_marked_for_review(self):
        requirements = extract_requirements("Customer: Add a report")
        self.assertEqual(requirements[0]["type"], "needs_review")
        self.assertEqual(
            requirements[0]["confidence"], "not_assessed"
        )

    def test_follow_up_detects_unchanged_requirement(self):
        previous = extract_requirements("Customer: Manage users")
        result = compare_meetings(
            previous, "Customer: Manage users"
        )
        self.assertEqual(result["changes"][0]["change"], "unchanged")

    def test_follow_up_flags_new_requirement(self):
        previous = extract_requirements("Customer: Manage users")
        result = compare_meetings(
            previous, "Customer: Search users by email"
        )
        self.assertEqual(
            result["changes"][0]["change"],
            "new_or_changed_needs_review",
        )
        self.assertTrue(result["requires_human_review"])

    def test_estimate_is_calculated_from_explicit_assumption(self):
        requirements = [{"id": "REQ-001"}, {"id": "REQ-002"}]
        estimate = create_estimate(requirements, hours_per_requirement=4)
        self.assertEqual(estimate["estimated_hours"], 8)
        self.assertEqual(estimate["status"], "preliminary")
        self.assertTrue(estimate["approval_required"])

    def test_invalid_estimate_assumption_is_rejected(self):
        with self.assertRaises(ValueError):
            create_estimate([], hours_per_requirement=0)

    def test_approval_records_decision_without_external_action(self):
        with patch("meeting_scope.record_audit") as audit:
            result = record_approval("approved", "Proposal 1")
        self.assertEqual(result["decision"], "approved")
        self.assertFalse(result["external_action_taken"])
        audit.assert_called_once()

    def test_invalid_approval_decision_is_rejected(self):
        with self.assertRaises(ValueError):
            record_approval("maybe", "Proposal 1")

    @patch("meeting_scope.requests.get")
    def test_knowledge_brain_search_returns_sources(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [{"title": "User guide", "url": "https://example.com"}]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = search_knowledge_brain("manage users")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["results"][0]["title"], "User guide")


if __name__ == "__main__":
    unittest.main()
