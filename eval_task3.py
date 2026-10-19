import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from meeting_scope import (
    extract_requirements,
    compare_meetings,
    create_estimate,
    record_approval,
    search_knowledge_brain,
)

results = []

def check(case_id, fn):
    try:
        passed, detail = fn()
        results.append({
            "case_id": case_id,
            "passed": bool(passed),
            "details": str(detail),
        })
    except Exception as exc:
        results.append({
            "case_id": case_id,
            "passed": False,
            "details": f"Exception: {type(exc).__name__}: {exc}",
        })

def case_nonempty_transcript():
    reqs = extract_requirements("Customer: Manage users")
    return len(reqs) == 1, f"requirements={len(reqs)}"

def case_empty_transcript_rejected():
    try:
        extract_requirements("")
        return False, "Empty transcript was accepted"
    except ValueError:
        return True, "Empty transcript rejected"

def case_source_line_one():
    reqs = extract_requirements("Customer: Manage users")
    return reqs[0]["source_line"] == 1, str(reqs[0].get("source_line"))

def case_source_line_multiple():
    reqs = extract_requirements("Customer: Manage users\nCustomer: Search users")
    lines = [r["source_line"] for r in reqs]
    return lines == [1, 2], str(lines)

def case_review_required():
    reqs = extract_requirements("Customer: Add reports")
    return all(r["type"] == "needs_review" for r in reqs), str([r["type"] for r in reqs])

def case_confidence_unassessed():
    reqs = extract_requirements("Customer: Add reports")
    return all(r["confidence"] == "not_assessed" for r in reqs), str([r["confidence"] for r in reqs])

def case_unchanged_meeting():
    previous = extract_requirements("Customer: Manage users")
    result = compare_meetings(previous, "Customer: Manage users")
    return result["changes"][0]["change"] == "unchanged", str(result["changes"])

def case_changed_meeting_needs_review():
    previous = extract_requirements("Customer: Manage users")
    result = compare_meetings(previous, "Customer: Search users")
    ok = result["requires_human_review"] and result["changes"][0]["change"] == "new_or_changed_needs_review"
    return ok, str(result["changes"])

def case_estimate_two_requirements():
    estimate = create_estimate([{"id": "REQ-1"}, {"id": "REQ-2"}], hours_per_requirement=4)
    return estimate["estimated_hours"] == 8, str(estimate)

def case_estimate_assumption_visible():
    estimate = create_estimate([{"id": "REQ-1"}], hours_per_requirement=4)
    ok = estimate["status"] == "preliminary" and estimate["approval_required"] is True
    return ok, str(estimate)

def case_zero_hours_rejected():
    try:
        create_estimate([], hours_per_requirement=0)
        return False, "Zero-hour assumption accepted"
    except ValueError:
        return True, "Zero-hour assumption rejected"

def case_negative_hours_rejected():
    try:
        create_estimate([], hours_per_requirement=-1)
        return False, "Negative-hour assumption accepted"
    except ValueError:
        return True, "Negative-hour assumption rejected"

def case_empty_requirements_estimate():
    estimate = create_estimate([], hours_per_requirement=4)
    return estimate["estimated_hours"] == 0, str(estimate)

def case_approval_does_not_act_externally():
    with patch("meeting_scope.record_audit"):
        result = record_approval("approved", "Test proposal")
    return result["external_action_taken"] is False, str(result)

def case_rejection_does_not_act_externally():
    with patch("meeting_scope.record_audit"):
        result = record_approval("rejected", "Test proposal")
    return result["external_action_taken"] is False, str(result)

def case_invalid_approval_rejected():
    try:
        record_approval("maybe", "Test proposal")
        return False, "Invalid decision accepted"
    except ValueError:
        return True, "Invalid decision rejected"

def case_knowledge_api_success():
    from unittest.mock import Mock
    response = Mock()
    response.json.return_value = {"results": [{"title": "Guide", "url": "https://example.com"}]}
    response.raise_for_status.return_value = None
    with patch("meeting_scope.requests.get", return_value=response):
        result = search_knowledge_brain("manage users")
    return result["status"] == "success" and len(result["results"]) == 1, str(result)

def case_knowledge_api_unavailable():
    import requests
    with patch("meeting_scope.requests.get", side_effect=requests.ConnectionError()):
        result = search_knowledge_brain("manage users")
    return result["status"] == "unavailable", str(result)

def case_fact_inference_distinction():
    reqs = extract_requirements(
        "Customer: We need a reporting dashboard"
    )
    item = reqs[0]
    ok = (
        item.get("classification") == "unclassified_needs_review"
        and item.get("classification_requires_human_review") is True
    )
    return ok, f"classification={item.get('classification')}"

def case_requirement_has_source_text():
    reqs = extract_requirements("Customer: Export reports to CSV")
    ok = "source_text" in reqs[0] and "Export reports to CSV" in reqs[0]["source_text"]
    return ok, str(reqs[0])

def case_separate_multiple_requirements():
    reqs = extract_requirements("Customer: Add reports\nCustomer: Export CSV\nCustomer: Manage users")
    return len(reqs) == 3, f"requirements={len(reqs)}"

checks = [
    ("nonempty_transcript", case_nonempty_transcript),
    ("empty_transcript_rejected", case_empty_transcript_rejected),
    ("source_line_one", case_source_line_one),
    ("source_line_multiple", case_source_line_multiple),
    ("requirements_marked_for_review", case_review_required),
    ("confidence_unassessed", case_confidence_unassessed),
    ("unchanged_meeting", case_unchanged_meeting),
    ("changed_meeting_requires_review", case_changed_meeting_needs_review),
    ("estimate_two_requirements", case_estimate_two_requirements),
    ("estimate_preliminary_and_approval", case_estimate_assumption_visible),
    ("zero_hours_rejected", case_zero_hours_rejected),
    ("negative_hours_rejected", case_negative_hours_rejected),
    ("empty_requirements_estimate", case_empty_requirements_estimate),
    ("approval_no_external_action", case_approval_does_not_act_externally),
    ("rejection_no_external_action", case_rejection_does_not_act_externally),
    ("invalid_approval_rejected", case_invalid_approval_rejected),
    ("knowledge_api_success", case_knowledge_api_success),
    ("knowledge_api_unavailable", case_knowledge_api_unavailable),
    ("fact_inference_distinction", case_fact_inference_distinction),
    ("requirement_source_text", case_requirement_has_source_text),
]

for case_id, fn in checks:
    check(case_id, fn)

output = {
    "task": "Task 3 - Meeting to Scope",
    "evaluation_type": "local code evaluation; mocked Knowledge Brain requests",
    "total": len(results),
    "passed": sum(r["passed"] for r in results),
    "failed": sum(not r["passed"] for r in results),
    "results": results,
}

Path("task3_eval_results.json").write_text(
    json.dumps(output, indent=2), encoding="utf-8"
)

print(json.dumps({
    "total": output["total"],
    "passed": output["passed"],
    "failed": output["failed"],
}, indent=2))

for result in results:
    if not result["passed"]:
        print("FAILED:", result)
