
# Evaluation Report

**Project:** AI Tech Consultant  
**Evaluation date:** 18 October 2026  
**Environment:** Python virtual environment on Windows

## 1. Evaluation Approach

The project uses Python's `unittest` framework to test the Knowledge Brain API, Claude integration handling, security behavior, Inbox Agent, and Meeting-to-Scope workflow.

Tests use mocks where external services are not needed. A passing mocked test verifies the tested code path; it does not prove that live Claude answers are factually correct.

## 2. Recorded Automated Test Results

The following combined test command was executed:

```powershell
python -m unittest test_search.py test_claude_brain.py test_main.py test_security.py test_inbox_agent.py test_meeting_scope.py -v
```

**Recorded result: 28 tests passed.**

| Component | Test coverage |
|---|---|
| Knowledge Brain search | Search behavior and result retrieval |
| Claude integration | Empty input, missing evidence, configuration, mocked response, and API error handling |
| API | Answer endpoint behavior and source handling |
| Security | Prompt-injection safeguards, source references, and error-detail handling |
| Inbox Agent | Email classification, priority, validation, human review, and audit behavior |
| Meeting to Scope | Transcript validation, source-line traceability, change detection, estimates, approvals, and API search |

## 3. Important Limitations

- **Live Claude:** Not verified. The Anthropic API returned an insufficient-credit error.
- **Retrieval:** The current implementation uses keyword matching. Semantic retrieval and a full hybrid search approach remain incomplete.
- **Citations:** Search results provide source URLs, but claim-by-claim citation accuracy has not been fully evaluated.
- **Inbox Agent:** Draft generation currently uses a template. Live Claude-generated replies and a complete 50-email evaluation have not been verified.
- **Meeting to Scope:** Transcript lines are recorded as review-needed items. Reliable fact-versus-inference classification and complete proposal generation remain incomplete.
- **Prompt injection:** Existing tests check safeguards and prompt construction; they do not establish resistance to every attack.
- **Estimates:** The current estimate is based on an explicit hours-per-requirement assumption, not validated project delivery data.

## 4. Required Evaluation Plan

The assignment requires at least 20 evaluation cases for each task. The 28 automated unit tests above must not be counted as 28 complete task-level evaluation cases.

| Task | Evaluation cases needed | Status |
|---|---:|---|
| Task 1 — Knowledge Brain | At least 20 | Additional task-level cases and recorded outcomes needed |
| Task 2 — Inbox Agent | At least 20 | Additional task-level cases and recorded outcomes needed |
| Task 3 — Meeting to Scope | At least 20 | Additional task-level cases and recorded outcomes needed |

Each evaluation case should record its input, expected behavior, actual observed result, pass/fail status, and any notes. Results must come from actual execution; do not report unrun cases as passed.

## 5. Next Improvements

1. Add at least 20 task-specific evaluation cases per task.
2. Measure search relevance, abstention, and source correctness.
3. Evaluate email classification, urgency, evidence use, and human approval.
4. Evaluate requirement extraction, change detection, estimates, and traceability.
5. Repeat live Claude evaluations only when API access is available.
6. Record failures and limitations alongside passing results.
