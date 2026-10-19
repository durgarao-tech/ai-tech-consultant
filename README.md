
# AI Tech Consultant

An AI-assisted prototype with three components: Knowledge Brain, Inbox Agent, and Meeting to Scope.

## 1. Project Overview

### Task 1: Python Knowledge Brain
- Crawls Brilliant Directories support documentation.
- Stores article content, URLs, and timestamps.
- Provides keyword-based document search through a FastAPI API.
- Supports grounded answers using Claude when API access is available.
- Includes abstention handling, security checks, and incremental ingestion.

### Task 2: Inbox Agent
- Classifies incoming emails by category and priority.
- Searches the Knowledge Brain API for relevant documentation.
- Creates reply drafts for human review.
- Records review decisions in an audit log.
- Does not send emails automatically.

### Task 3: Meeting to Scope
- Extracts requirements from meeting transcripts.
- Records source lines for traceability.
- Searches the Knowledge Brain API for related documentation.
- Compares follow-up meeting notes.
- Creates preliminary estimates and records approval decisions.

## 2. Technologies

- Python
- FastAPI
- Requests and HTTPX
- Beautiful Soup and lxml
- Anthropic Python SDK
- python-dotenv
- unittest
- JSON and JSON Lines

## 3. Setup

Open a terminal in the project folder and activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install fastapi "uvicorn[standard]" httpx beautifulsoup4 lxml anthropic python-dotenv requests
```

For live Claude API calls, create a `.env` file with your own API key:

```text
ANTHROPIC_API_KEY=your_api_key_here
```

Never upload `.env` or share your API key.

## 4. Run the Project

Start the Knowledge Brain API:

```powershell
python -m uvicorn main:app --reload
```

Open the API documentation at:

http://127.0.0.1:8000/docs

In another terminal, run the Inbox Agent:

```powershell
python inbox_agent.py
```

Run Meeting to Scope:

```powershell
python meeting_scope.py
```

Run the combined test suite:

```powershell
python -m unittest test_search.py test_claude_brain.py test_main.py test_security.py test_inbox_agent.py test_meeting_scope.py -v
```

## 5. Testing and Limitations

The combined local test suite passed 28 tests on 18 October 2026. These tests validate prototype behavior and do not establish production readiness.

Live Claude generation has not been verified because the Anthropic API account has insufficient credits. Search currently uses keyword matching rather than a complete semantic and hybrid retrieval system. Email replies and scope proposals require human review. Further evaluation is needed for retrieval relevance, citation accuracy, prompt injection, requirement changes, and end-to-end workflows.

## 6. Project Files

- `ingest.py` — documentation ingestion
- `main.py` — Knowledge Brain API
- `claude_brain.py` — Claude answer generation
- `inbox_agent.py` — email classification and draft workflow
- `meeting_scope.py` — requirement extraction and scope workflow
- `test_*.py` — automated tests
- `EVALS.md` — evaluation results and limitations
- `DESIGN.md` — architecture and design decisions
- `AI_LOG.md` — AI-assisted development record
