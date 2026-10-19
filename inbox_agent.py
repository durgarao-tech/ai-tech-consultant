
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import requests


BRAIN_API_URL = "http://127.0.0.1:8000"
AUDIT_FILE = Path("data") / "inbox_audit.jsonl"

CATEGORIES = {
    "technical_support": [
    "error", "bug", "broken", "not working", "issue",
    "problem", "api", "setup", "configure",
    "critical", "system down", "security breach",
],
    "billing": [
        "billing", "invoice", "payment", "refund", "charge",
        "subscription", "price",
    ],
    "account": [
        "account", "login", "password", "user", "access",
        "profile", "permission",
    ],
    "sales": [
        "pricing", "demo", "purchase", "plan", "features",
        "upgrade",
    ],
}


def classify_email(subject: str, body: str) -> dict:
    """Classify an email using transparent keyword rules."""
    text = f"{subject} {body}".lower()

    scores = {
        category: sum(
            1 for keyword in keywords if keyword in text
        )
        for category, keywords in CATEGORIES.items()
    }

    best_category = max(scores, key=scores.get)

    if scores[best_category] == 0:
        best_category = "general"

    urgent_terms = [
        "urgent", "asap", "immediately", "critical",
        "system down", "security breach",
    ]

    priority = (
        "high"
        if any(term in text for term in urgent_terms)
        else "normal"
    )

    return {
        "category": best_category,
        "priority": priority,
        "method": "keyword_rules",
        "category_scores": scores,
    }


def search_knowledge_brain(question: str) -> dict:
    """Retrieve evidence using the Task 1 API."""
    try:
        response = requests.get(
            f"{BRAIN_API_URL}/search",
            params={"q": question},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        return {
            "status": "success",
            "query": question,
            "results": data.get("results", []),
        }

    except requests.RequestException as error:
        return {
            "status": "unavailable",
            "error": type(error).__name__,
            "results": [],
        }


def build_draft(email: dict, evidence_result: dict) -> dict:
    """Build a reviewable draft; never send email."""
    subject = str(email.get("subject", "")).strip()
    body = str(email.get("body", "")).strip()

    classification = classify_email(subject, body)

    if evidence_result.get("status") != "success":
        draft = (
            "Thank you for contacting us. We are unable to verify "
            "the relevant documentation at the moment. Your request "
            "needs human review before we can provide a confirmed answer."
        )
        sources = []
        status = "needs_human_review"

    else:
        results = evidence_result.get("results", [])

        if not results:
            draft = (
                "Thank you for contacting us. I could not find "
                "supporting documentation for your question. "
                "Our team needs to review this before providing "
                "a confirmed answer."
            )
            sources = []
            status = "needs_human_review"

        else:
            # This is a template, not a Claude-generated answer.
            # The retrieved articles are evidence for a human reviewer.
            draft = (
                "Thank you for contacting us.\n\n"
                "I found potentially relevant documentation for "
                "your request. Our support team will review the "
                "details and confirm the appropriate next steps.\n\n"
                "Please see the references below."
            )
            sources = [
                {
                    "title": item.get("title", "Untitled"),
                    "url": item.get("url", ""),
                }
                for item in results[:5]
            ]
            status = "draft_ready_for_review"

    return {
        "email_subject": subject,
        "classification": classification,
        "draft_reply": draft,
        "sources": sources,
        "status": status,
        "approval_required": True,
    }


def record_audit(event: dict) -> None:
    """Append an audit event as one JSON object per line."""
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **event,
    }

    with AUDIT_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")


def process_email(email: dict) -> dict:
    """Classify, retrieve evidence, draft, and record the result."""
    subject = str(email.get("subject", "")).strip()
    body = str(email.get("body", "")).strip()

    if not subject and not body:
        raise ValueError("Email must contain a subject or body.")

    # Email text is untrusted input. It is used as a search query,
    # not as instructions to execute.
    evidence = search_knowledge_brain(f"{subject} {body}".strip())
    result = build_draft(email, evidence)

    record_audit({
        "event": "draft_created",
        "classification": result["classification"],
        "status": result["status"],
        "source_count": len(result["sources"]),
        "approval_required": True,
    })

    return result


def record_human_decision(
    decision: str,
    email_subject: str,
    feedback: str = "",
) -> dict:
    """Record approval or rejection without sending email."""
    allowed = {"approved", "rejected"}

    if decision not in allowed:
        raise ValueError("Decision must be approved or rejected.")

    record_audit({
        "event": "human_review",
        "decision": decision,
        "email_subject": email_subject,
        "feedback": feedback,
        "email_sent": False,
    })

    return {
        "decision": decision,
        "email_sent": False,
        "message": (
            "Decision recorded. This prototype does not send emails."
        ),
    }


if __name__ == "__main__":
    example_email = {
        "subject": "How can I manage users?",
        "body": (
            "I need documentation about user management "
            "and account access."
        ),
    }

    result = process_email(example_email)
    print(json.dumps(result, indent=2))
