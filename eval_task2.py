import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import inbox_agent


CASES = [
    ("billing", "Invoice payment problem", "I need a refund for my charge.", "billing", "normal"),
    ("technical", "API error", "The API is broken and not working.", "technical_support", "normal"),
    ("account", "Login access", "I forgot my password and cannot login.", "account", "normal"),
    ("sales", "Request a demo", "I want a demo before purchase.", "sales", "normal"),
    ("general", "Thank you", "Thank you for your help.", "general", "normal"),
    ("urgent", "Urgent billing issue", "Please refund this payment ASAP.", "billing", "high"),
    ("critical", "Critical system down", "Our service is down.", "technical_support", "high"),
    ("security", "Security breach", "We have a security breach.", "technical_support", "high"),
    ("normal", "Feature question", "Can you explain the available features?", "sales", "normal"),
    ("subscription", "Subscription price", "What is the subscription price?", "billing", "normal"),
    ("permissions", "User permissions", "I need permission to access my profile.", "account", "normal"),
    ("setup", "Setup help", "I need help to configure the application.", "technical_support", "normal"),
    ("refund", "Payment refund", "Please help with a refund.", "billing", "normal"),
    ("purchase", "Purchase plan", "I want to purchase an upgrade plan.", "sales", "normal"),
    ("empty", "", "", None, None),
    ("review_no_evidence", "Unknown topic", "Please explain an undocumented topic.", None, None),
    ("review_api_down", "Account help", "I cannot access my account.", None, None),
    ("source_citation", "API question", "How does the API work?", None, None),
    ("approval", "Test approval", "Please review this reply.", None, None),
    ("rejection", "Test rejection", "This draft is incorrect.", None, None),
]


def evaluate():
    results = []

    for case_id, subject, body, expected_category, expected_priority in CASES:
        checks = {}
        details = ""

        if case_id == "empty":
            try:
                inbox_agent.process_email({"subject": subject, "body": body})
                checks["empty_rejected"] = False
            except ValueError:
                checks["empty_rejected"] = True

        elif case_id in ("review_no_evidence", "review_api_down"):
            evidence = (
                {"status": "unavailable", "results": []}
                if case_id == "review_api_down"
                else {"status": "success", "results": []}
            )
            draft = inbox_agent.build_draft(
                {"subject": subject, "body": body}, evidence
            )
            checks["human_review_required"] = (
                draft["status"] == "needs_human_review"
                and draft["approval_required"] is True
                and draft["sources"] == []
            )

        elif case_id == "source_citation":
            evidence = {
                "status": "success",
                "results": [
                    {"title": "API Guide", "url": "https://example.com/api"}
                ],
            }
            draft = inbox_agent.build_draft(
                {"subject": subject, "body": body}, evidence
            )
            checks["source_preserved"] = (
                len(draft["sources"]) == 1
                and draft["sources"][0]["title"] == "API Guide"
                and draft["approval_required"] is True
            )

        elif case_id in ("approval", "rejection"):
            decision = "approved" if case_id == "approval" else "rejected"
            with tempfile.TemporaryDirectory() as directory:
                audit_path = Path(directory) / "audit.jsonl"
                with patch.object(inbox_agent, "AUDIT_FILE", audit_path):
                    result = inbox_agent.record_human_decision(
                        decision, subject, "Evaluation test"
                    )
                event = json.loads(audit_path.read_text(encoding="utf-8"))
            checks["decision_recorded"] = (
                result["decision"] == decision
                and result["email_sent"] is False
                and event["decision"] == decision
                and event["email_sent"] is False
            )

        else:
            actual = inbox_agent.classify_email(subject, body)
            checks["category"] = actual["category"] == expected_category
            checks["priority"] = actual["priority"] == expected_priority
            details = (
                f"expected={expected_category}/{expected_priority}, "
                f"actual={actual['category']}/{actual['priority']}"
            )

        passed = all(checks.values())
        results.append({
            "case_id": case_id,
            "passed": passed,
            "checks": checks,
            "details": details,
        })

    return results


if __name__ == "__main__":
    results = evaluate()
    output = {
        "task": "Task 2 - Inbox Agent",
        "evaluation_type": "local code evaluation; mocked evidence and audit actions",
        "total": len(results),
        "passed": sum(item["passed"] for item in results),
        "failed": sum(not item["passed"] for item in results),
        "results": results,
    }

    Path("task2_eval_results.json").write_text(
        json.dumps(output, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "total": output["total"],
        "passed": output["passed"],
        "failed": output["failed"],
    }, indent=2))
    for item in results:
        if not item["passed"]:
            print("FAILED:", item)
