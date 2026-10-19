import json
from datetime import datetime, timezone
from pathlib import Path

import requests

API = "http://127.0.0.1:8000/search"

CASES = [
    ("Users API management", "How to manage users with API calls", ["Users API"]),
    ("Users API reference", "API Reference Users", ["API Reference", "Users API"]),
    ("API key setup", "How to generate and manage API keys", ["API Keys", "API Key"]),
    ("Email management", "How to manage email accounts and email templates", ["Email Management"]),
    ("User consent", "How to configure user consent GDPR compliance", ["User Consent"]),
    ("Billing management", "How to manage billing and payments", ["Billing"]),
    ("Membership payments", "How to accept member payments", ["Payment", "Billing"]),
    ("User profiles", "How to manage user profile information", ["User", "Profile"]),
    ("Search directory", "How to configure directory search", ["Search"]),
    ("Website settings", "How to manage website settings", ["Website", "Settings"]),
    ("API authentication", "How to authenticate API requests with API keys", ["API", "Key"]),
    ("Create users", "How to create users through the API", ["Users API"]),
    ("Update users", "How to update users through API calls", ["Users API"]),
    ("Delete users", "How to delete users through API calls", ["Users API"]),
    ("Search users", "How to search users using the API", ["Users API"]),
    ("Email campaigns", "How to send an email campaign", ["Email"]),
    ("Manual payments", "How to accept cash or bank transfers", ["Manual Billing", "Billing"]),
    ("Developer documentation", "Where can I find API developer documentation", ["API"]),
    ("Account dashboard", "How to use the account dashboard", ["Account Dashboard"]),
    ("Unrelated question", "What is the weather on Mars today", []),
]

results = []

for case_id, (name, query, expected_terms) in enumerate(CASES, start=1):
    record = {
        "id": case_id,
        "name": name,
        "query": query,
        "expected_terms": expected_terms,
    }

    try:
        response = requests.get(API, params={"q": query}, timeout=30)
        response.raise_for_status()
        payload = response.json()
        articles = payload.get("results", [])

        titles = [item.get("title", "") for item in articles]
        combined = " ".join(
            (item.get("title", "") + " " + item.get("excerpt", ""))
            for item in articles
        ).casefold()

        if expected_terms:
            passed = any(term.casefold() in combined for term in expected_terms)
            reason = (
                "Expected keyword found in top-five results"
                if passed else
                "Expected keywords not found in top-five results"
            )
        else:
            passed = len(articles) == 0
            reason = (
                "No results returned for unsupported query"
                if passed else
                "Results returned; abstention must be checked through /answer"
            )

        record.update({
            "status": "PASS" if passed else "FAIL",
            "reason": reason,
            "result_count": len(articles),
            "top_titles": titles[:5],
        })

    except Exception as exc:
        record.update({
            "status": "ERROR",
            "reason": type(exc).__name__,
        })

    results.append(record)
    print(
        f'{case_id:02d}. {record["status"]}: {name} '
        f'({record.get("reason", "")})'
    )

passed_count = sum(item["status"] == "PASS" for item in results)
failed_count = sum(item["status"] == "FAIL" for item in results)
error_count = sum(item["status"] == "ERROR" for item in results)

report = {
    "evaluation_type": "Task 1 keyword retrieval",
    "evaluated_at_utc": datetime.now(timezone.utc).isoformat(),
    "api": API,
    "total_cases": len(results),
    "passed": passed_count,
    "failed": failed_count,
    "errors": error_count,
    "results": results,
}

Path("task1_eval_results.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("\n--- ACTUAL EVALUATION SUMMARY ---")
print(f"Total cases: {len(results)}")
print(f"Passed: {passed_count}")
print(f"Failed: {failed_count}")
print(f"Errors: {error_count}")
print("Detailed results: task1_eval_results.json")
