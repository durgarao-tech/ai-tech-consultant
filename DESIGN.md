
# AI Tech Consultant — Design Document

## 1. Overview

AI Tech Consultant is a Python prototype that connects three workflows:

1. Knowledge Brain — retrieves information from support documentation.
2. Inbox Agent — classifies emails and prepares drafts for human review.
3. Meeting to Scope — extracts meeting requirements and creates preliminary scope information.

Tasks 2 and 3 use the Knowledge Brain API as their documentation retrieval source.

## 2. Architecture

```text
Brilliant Directories Support Sitemap
                 |
                 v
           ingest.py
                 |
                 v
         data/articles.json
                 |
                 v
             main.py
          FastAPI endpoints
           /search /answer
                 |
         +-------+-------+
         |               |
         v               v
   inbox_agent.py   meeting_scope.py
         |               |
         v               v
 Email draft and     Requirements,
 human review        scope and estimate
         |               |
         +-------+-------+
                 |
                 v
            Audit logs
```

Claude answer generation is implemented in `claude_brain.py` and is called by the Knowledge Brain answer workflow. Live generation requires an Anthropic API account with sufficient credits.

## 3. Task 1 — Knowledge Brain

### Ingestion

`ingest.py` reads the support sitemap, downloads article pages, extracts article content, and saves records in JSON format. Each record includes fields such as title, content, URL, and fetch timestamp.

Incremental ingestion checks existing timestamps and skips recently fetched records under the configured refresh policy. Failed or missing records can be retried.

### Retrieval and API

`main.py` loads article records and performs keyword-based retrieval. The current implementation gives article-title matches additional weight and returns excerpts, matched terms, scores, and source URLs.

The FastAPI application exposes health, search, and answer endpoints. When the query lacks adequate evidence, the answer workflow can abstain. Claude generation is attempted when relevant evidence is available and API configuration permits it.

### Security

Documentation is treated as untrusted reference material in the Claude prompt. The prompt instructs the model not to follow embedded instructions or disclose secrets. API errors return limited error information.

These safeguards reduce risk but do not guarantee protection against every prompt-injection attack.

## 4. Task 2 — Inbox Agent

`inbox_agent.py` assigns an email category and priority using keyword rules. It queries the Knowledge Brain search API and creates a draft that requires human review.

Audit events are appended to `data/inbox_audit.jsonl`. Human approval is recorded separately. The prototype does not send email messages.

The current draft is a template, not a completed Claude-generated, evidence-grounded response. Future development should generate drafts from verified documentation, validate each factual claim, and evaluate a representative set of 50 emails.

## 5. Task 3 — Meeting to Scope

`meeting_scope.py` processes transcript lines into requirement records. It preserves source-line information so reviewers can trace each item back to the meeting text.

The workflow searches the Knowledge Brain for related documentation, compares follow-up notes with previous requirements, and flags new or changed text for review. A preliminary estimator uses an explicit hours-per-requirement assumption.

This is an initial prototype. It does not yet reliably distinguish facts from inferences, resolve complex requirement changes, or generate a complete validated proposal.

## 6. Key Design Decisions

- **Python:** A common language across the three workflows simplifies integration.
- **FastAPI:** Provides a lightweight HTTP interface between components.
- **JSON storage:** Keeps the prototype simple and inspectable.
- **Incremental ingestion:** Avoids repeatedly fetching recently updated articles.
- **Human approval:** Prevents drafts and proposals from being treated as automatically authorized actions.
- **Audit logs:** Record important workflow and review events.
- **Abstention:** Allows the Knowledge Brain to avoid answering when evidence is inadequate.
- **Explicit limitations:** Mocked tests and local tests are not presented as proof of live model accuracy.

## 7. Evaluation and Known Limitations

The combined local unit test suite passed 28 tests on 18 October 2026. Separate task-level evaluations were executed on 19 October 2026: Task 1 passed 17 of 20 cases, Task 2 passed 20 of 20 cases, and Task 3 passed 20 of 20 cases. These are local test results and do not establish live model accuracy or production readiness.

The current implementation does not yet provide complete semantic/hybrid retrieval, verified live Claude output, fully evidence-grounded inbox replies, or a production-grade meeting-to-proposal workflow. The detailed results, failures, and limitations are documented in `EVALS.md`.

## 8. Future Work

1. Implement semantic and hybrid retrieval.
2. Improve relevance ranking and claim-level source validation.
3. Add robust fact-versus-inference labeling.
4. Evaluate 50 representative emails.
5. Build at least 20 recorded evaluation cases per task.
6. Add feedback-based improvements and proposal version history.
7. Run live Claude evaluations when API access is available.
