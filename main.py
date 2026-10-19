
import json
import re
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query

from claude_brain import generate_grounded_answer


app = FastAPI(
    title="AI Tech Consultant - Knowledge Brain",
    description="Search Brilliant Directories support documentation",
    version="0.4.0",
)

DATA_FILE = Path(__file__).parent / "data" / "articles.json"


STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were",
    "how", "can", "i", "you", "we", "they",
    "what", "where", "when", "why", "who",
    "do", "does", "did", "to", "for", "of",
    "in", "on", "at", "with", "and", "or",
    "my", "your", "their", "it", "this", "that",
    "be", "by", "from", "as", "have", "has",
}


def load_articles():
    """Load the locally stored documentation articles."""
    if not DATA_FILE.exists():
        raise HTTPException(
            status_code=503,
            detail="Article data not found. Run ingest.py first.",
        )

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise HTTPException(
                status_code=500,
                detail="Article data must be a JSON list.",
            )

        return data

    except (OSError, json.JSONDecodeError) as error:
        raise HTTPException(
            status_code=500,
            detail=f"Could not read article data: {error}",
        )


def tokenize(text: str) -> list[str]:
    """Convert text into searchable words."""
    words = re.findall(r"\b[a-z0-9]+\b", text.lower())
    return [word for word in words if word not in STOP_WORDS]


def make_excerpt(content: str, query_terms: set[str]) -> str:
    """Create a short excerpt around a matching query term."""
    text = re.sub(r"\s+", " ", content).strip()

    noise_phrases = [
        "What Do You Need Help With?",
        "Enter your search term here...",
        "Search Solution home",
    ]

    for phrase in noise_phrases:
        text = re.sub(
            re.escape(phrase),
            "",
            text,
            flags=re.IGNORECASE,
        )

    text = re.sub(r"\s+", " ", text).strip()
    lowered = text.lower()

    positions = [
        lowered.find(term)
        for term in query_terms
        if len(term) > 2 and lowered.find(term) >= 0
    ]

    start = max(0, min(positions) - 100) if positions else 0
    excerpt = text[start:start + 350]

    if start > 0:
        excerpt = "..." + excerpt

    if start + 350 < len(text):
        excerpt += "..."

    return excerpt



def retrieve_articles(question: str, limit: int = 5) -> list[dict]:
    """Retrieve documentation articles using keyword matching."""
    articles = load_articles()
    query_terms = set(tokenize(question))

    if not query_terms:
        return []

    results = []

    for article in articles:
        title = article.get("title", "")
        content = article.get("content", "")

        title_terms = set(tokenize(title))
        content_terms = set(tokenize(content))

        matched_terms = query_terms & (title_terms | content_terms)
        coverage = len(matched_terms) / len(query_terms)

        # Require at least half of the query's meaningful terms to match.
        if coverage < 0.5:
            continue

        title_matches = len(query_terms & title_terms)
        content_matches = len(query_terms & content_terms)
        score = title_matches * 3 + content_matches

        if score > 0:
            results.append({
                "title": title,
                "url": article.get("url", ""),
                "content": content,
                "score": score,
                "excerpt": make_excerpt(content, query_terms),
                "matched_terms": len(matched_terms),
                "coverage": round(coverage, 2),
            })

    results.sort(key=lambda item: item["score"], reverse=True)

    return results[:limit]



@app.get("/")
def home():
    return {
        "message": "AI Tech Consultant Knowledge Brain is running!",
        "status": "success",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/search")
def search_articles(
    q: str = Query(min_length=2),
    limit: int = Query(default=5, ge=1, le=10),
):
    """Search documentation and return matching article excerpts."""
    articles = load_articles()
    query_terms = set(tokenize(q))
    results = []

    for article in articles:
        title = article.get("title", "")
        content = article.get("content", "")

        title_terms = set(tokenize(title))
        content_terms = set(tokenize(content))

        title_matches = len(query_terms & title_terms)
        content_matches = len(query_terms & content_terms)

        score = title_matches * 3 + content_matches

        if score > 0:
            results.append({
                "title": title,
                "url": article.get("url", ""),
                "score": score,
                "excerpt": make_excerpt(content, query_terms),
            })

    results.sort(key=lambda item: item["score"], reverse=True)
    returned_results = results[:limit]

    return {
        "query": q,
        "total_matches": len(results),
        "result_count": len(returned_results),
        "results": returned_results,
    }


@app.get("/answer")
def answer_question(
    q: str = Query(min_length=2),
    limit: int = Query(default=5, ge=1, le=5),
):
    """Generate an evidence-grounded answer through Claude."""
    query_terms = set(tokenize(q))

    if not query_terms:
        return {
            "status": "abstained",
            "answer": "Please ask a question about the documentation.",
            "sources": [],
        }

    evidence = retrieve_articles(q, limit=limit)

    if not evidence:
        return {
            "status": "abstained",
            "answer": (
                "I could not find enough relevant evidence "
                "in the documentation."
            ),
            "sources": [],
        }

    best_article = evidence[0]
    coverage = best_article["matched_terms"] / len(query_terms)

    if coverage < 0.5:
        return {
            "status": "abstained",
            "answer": (
                "I could not find enough relevant evidence "
                "in the documentation."
            ),
            "sources": [],
            "evidence_coverage": round(coverage, 2),
        }

    # Send full article content to Claude, not just search excerpts.
    claude_evidence = [
        {
            "title": item["title"],
            "url": item["url"],
            "content": item["content"],
        }
        for item in evidence
    ]

    result = generate_grounded_answer(q, claude_evidence)

    if result.get("status") == "success":
        result["sources"] = [
            {
                "title": item["title"],
                "url": item["url"],
            }
            for item in evidence
        ]

    result["evidence_coverage"] = round(coverage, 2)

    return result
