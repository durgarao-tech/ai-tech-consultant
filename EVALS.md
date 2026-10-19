
# Evaluation Report

**Project:** AI Tech Consultant  
**Evaluation date:** 19 October 2026  
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

## 4. Task-Level Evaluation Summary

Each task has a dedicated evaluation script and a recorded result file. These local results measure the specific checks implemented in each script; they do not establish production readiness or live AI accuracy.

| Task | Evaluation cases | Passed | Failed |
|---|---:|---:|---:|
| Task 1 — Knowledge Brain | 20 | 17 | 3 |
| Task 2 — Inbox Agent | 20 | 20 | 0 |
| Task 3 — Meeting to Scope | 20 | 20 | 0 |

Task 1's three failures are documented below. Tasks 2 and 3 passed their current predefined local evaluation checks. All results are limited to the tested behavior and stated limitations. 
## 5. Next Improvements

1. Improve search relevance and implement semantic or hybrid retrieval.
2. Review the two Task 1 keyword-evaluation failures and improve the search criteria.
3. Evaluate citation accuracy and prompt-injection resistance more thoroughly.
4. Improve Inbox Agent drafts with evidence-grounded responses when live AI access is available.
5. Improve requirement extraction, change detection, and proposal version history.
6. Run live Claude evaluations when API credits are available.
7. Continue recording failures, limitations, and actual test results.

## Task 1 — Actual Retrieval Evaluation (19 October 2026)

Evaluation script: `eval_task1.py`
Detailed machine-readable results: `task1_eval_results.json`

- Total retrieval cases: 20
- Passed under the script's keyword-matching criteria: 17
- Failed: 3
- Execution errors: 0
- Observed baseline pass rate: 85% (17/20)

### Observed failures

1. Email management: the returned titles appeared relevant, but the expected keywords were not found by the evaluation criterion.
2. Create users: the API Reference - Users article appeared in the results, but the expected keyword check failed.
3. Unrelated weather question: keyword search returned unrelated support articles instead of an empty result.

### Separate abstention check

Query: `What is the weather on Mars today`

Observed `/answer` response:
- Status: `abstained`
- Answer: `I could not find enough relevant evidence in the documentation.`
- Sources: empty list

This separate abstention check passed. It is not included in the 20-case retrieval score.

### Limitations

These cases evaluate basic keyword matching, not semantic retrieval or full answer correctness. The two apparent keyword-criterion failures need review. Live Claude answer generation could not be validated because the Anthropic API account had insufficient credits. No live Claude success is claimed.

## Task 2 — Inbox Agent Evaluation (19 October 2026)

Evaluation script: `eval_task2.py`
Machine-readable results: `task2_eval_results.json`

- Evaluation cases: 20
- Final passed: 20
- Final failed: 0
- Final observed pass rate: 100%
- Existing unit tests: 6 passed

### Improvement identified

The initial evaluation passed 18 of 20 cases. The `critical` and `security` cases received high priority but were incorrectly classified as `general`. Adding `critical`, `system down`, and `security breach` to the technical-support keywords resolved both failures. The evaluation was rerun and all 20 cases passed.

### Evaluation scope and limitations

These are local code-level checks using predefined email examples, mocked evidence for selected scenarios, and temporary audit files. They do not demonstrate live Claude-generated replies, production email integration, or end-to-end performance with a live Knowledge Brain API. The draft remains a template requiring human review; emails are not sent automatically.

## Task 3 — Meeting to Scope Evaluation (19 October 2026)

Evaluation script: `eval_task3.py`
Machine-readable results: `task3_eval_results.json`

- Local evaluation cases: 20
- Passed: 20
- Failed: 0
- Observed pass rate: 100%
- Unit tests: 10 passed

### Evaluation scope

Cases cover transcript validation, source-line tracking, human-review flags, follow-up text comparison, estimate calculations and assumptions, approval/rejection audit safety, and Knowledge Brain API success/unavailable behavior using mocked requests.

### Important limitations

The fact-versus-inference test verifies that extracted requirements are marked `unclassified_needs_review` and require human review. It does not demonstrate automatic fact/inference classification. Requirements are currently created from transcript lines rather than robust semantic extraction. Follow-up comparison uses exact text matching and does not reliably identify changed versions, maintain full proposal history, or automatically re-estimate changed scope. Estimates use a simple hours-per-requirement assumption and require human review. Live Claude and production integration were not validated.
