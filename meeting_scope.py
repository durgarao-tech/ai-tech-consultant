
import json
from datetime import datetime, timezone
from pathlib import Path

import requests

BRAIN_API_URL = "http://127.0.0.1:8000"
AUDIT_FILE = Path("data") / "meeting_scope_audit.jsonl"


def search_knowledge_brain(question):
    """Search Task 1 for documentation related to a requirement."""
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
            "results": data.get("results", []),
        }
    except requests.RequestException as error:
        return {
            "status": "unavailable",
            "error": type(error).__name__,
            "results": [],
        }


def extract_requirements(transcript, meeting_name="Meeting 1"):
    """Create traceable requirement records from a meeting transcript."""
    if not transcript or not transcript.strip():
        raise ValueError("Meeting transcript cannot be empty.")

    requirements = []

    for line_number, line in enumerate(transcript.splitlines(), start=1):
        text = line.strip()

        if not text:
            continue

        requirements.append({
            "id": f"REQ-{len(requirements) + 1:03d}",
            "meeting": meeting_name,
            "source_line": line_number,
            "source_text": text,
             "type": "needs_review",
            "classification": "unclassified_needs_review",
            "requirement": text,
            "confidence": "not_assessed",
            "classification_requires_human_review": True,
        })

    return requirements


def build_scope(transcript, meeting_name="Meeting 1"):
    """Build an initial scope draft with evidence from the Knowledge Brain."""
    requirements = extract_requirements(transcript, meeting_name)

    evidence = []
    for requirement in requirements:
        result = search_knowledge_brain(requirement["requirement"])
        requirement["knowledge_status"] = result["status"]

        if result["status"] == "success":
            sources = result["results"][:3]
            requirement["knowledge_sources"] = [
                {
                    "title": source.get("title", "Untitled"),
                    "url": source.get("url", ""),
                }
                for source in sources
            ]
            evidence.extend(requirement["knowledge_sources"])
        else:
            requirement["knowledge_sources"] = []

    return {
        "meeting": meeting_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "requirements": requirements,
        "scope_status": "draft_requires_human_review",
        "estimate": {
            "status": "not_estimated",
            "reason": "Effort must be estimated after requirements are reviewed.",
        },
        "knowledge_sources": evidence,
        "approval_required": True,
    }


def record_audit(event):
    """Append one audit event to a JSON Lines file."""
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **event,
    }

    with AUDIT_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")


def compare_meetings(previous_requirements, follow_up_transcript):
    """Compare a follow-up transcript with previously recorded requirements."""
    follow_up_lines = [
        line.strip()
        for line in follow_up_transcript.splitlines()
        if line.strip()
    ]

    previous_texts = {
        item["source_text"].strip().lower(): item
        for item in previous_requirements
    }

    changes = []
    next_id = len(previous_requirements) + 1

    for line_number, text in enumerate(follow_up_lines, start=1):
        key = text.lower()

        if key in previous_texts:
            changes.append({
                "change": "unchanged",
                "source_line": line_number,
                "text": text,
                "previous_requirement_id": previous_texts[key]["id"],
            })
        else:
            changes.append({
                "change": "new_or_changed_needs_review",
                "proposed_id": f"REQ-{next_id:03d}",
                "source_line": line_number,
                "text": text,
                "previous_version": None,
                "requires_human_review": True,
            })
            next_id += 1

    return {
        "changes": changes,
        "requires_human_review": True,
    }


def create_estimate(requirements, hours_per_requirement=4):
    """Create a rough planning estimate, not a confirmed delivery commitment."""
    if hours_per_requirement <= 0:
        raise ValueError("Hours per requirement must be greater than zero.")

    count = len(requirements)
    estimated_hours = count * hours_per_requirement

    return {
        "status": "preliminary",
        "requirement_count": count,
        "assumed_hours_per_requirement": hours_per_requirement,
        "estimated_hours": estimated_hours,
        "assumption": (
            "The hours-per-requirement value is an illustrative assumption. "
            "A developer must review complexity, dependencies, and testing."
        ),
        "approval_required": True,
    }


def record_approval(decision, proposal_name, feedback=""):
    """Record a human decision; this does not authorize external actions."""
    if decision not in {"approved", "rejected"}:
        raise ValueError("Decision must be 'approved' or 'rejected'.")

    record_audit({
        "event": "proposal_review",
        "proposal_name": proposal_name,
        "decision": decision,
        "feedback": feedback,
        "external_action_taken": False,
    })

    return {
        "decision": decision,
        "external_action_taken": False,
        "message": "Decision recorded. No proposal was sent externally.",
    }

if __name__ == "__main__":
    sample_transcript = """
    Customer: We need a page where staff can manage users.
    Customer: Staff should be able to search for a user by email.
    Customer: We may need different permissions for different staff.
    """

    scope = build_scope(sample_transcript)
    record_audit({
        "event": "scope_draft_created",
        "meeting": scope["meeting"],
        "requirement_count": len(scope["requirements"]),
        "approval_required": True,
    })

    print(json.dumps(scope, indent=2))
