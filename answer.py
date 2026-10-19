
import json
import re
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "articles.json"

STOP_WORDS = {
    "how", "what", "when", "where", "why", "can",
    "the", "for", "with", "and", "are", "you",
    "does", "this", "that", "from", "have", "get",
    "use", "using", "about", "into", "your", "manage",
    "is", "at", "a", "an", "of", "to", "in", "on",
    "who", "tell", "me", "please", "i"
}

SENSITIVE_PATTERNS = [
    r"\bhome address\b",
    r"\bpersonal address\b",
    r"\bprivate address\b",
    r"\bphone number\b",
    r"\bprivate email\b",
]


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"\b[a-z0-9]+\b", text.lower()))


def abstain(message: str) -> dict:
    return {
        "answer": message,
        "sources": [],
        "note": "Local prototype; no AI-generated answer.",
    }


def clean_content(content: str) -> str:
    content = re.sub(r"https?://\S+", " ", content)
    content = re.sub(
        r"\bLink:\s*", " ", content, flags=re.IGNORECASE
    )
    return re.sub(r"\s+", " ", content).strip()


def answer_question(question: str) -> dict:
    if not question.strip():
        return abstain("Please enter a question.")

    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, question, re.IGNORECASE):
            return abstain(
                "I cannot provide private personal contact details. "
                "Please use official public contact channels instead."
            )

    if not DATA_FILE.exists():
        return abstain("Knowledge data is unavailable. Run ingest.py first.")

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            articles = json.load(file)
    except (OSError, json.JSONDecodeError):
        return abstain("Could not read the knowledge data.")

    if not isinstance(articles, list) or not articles:
        return abstain("No knowledge articles are available.")

    question_words = tokenize(question) - STOP_WORDS
    if not question_words:
        return abstain("Please ask a more specific question.")

    # Find the best matching article.
    best_article = None
    best_score = 0
    best_matches = set()

    for article in articles:
        title = article.get("title", "")
        content = article.get("content", "")

        title_matches = question_words & tokenize(title)
        content_matches = question_words & tokenize(content)
        score = 3 * len(title_matches) + len(content_matches)

        if score > best_score:
            best_score = score
            best_article = article
            best_matches = title_matches | content_matches

    if best_article is None:
        return abstain("I could not find relevant documentation.")

    coverage = len(best_matches) / len(question_words)
    if coverage < 0.5:
        return abstain(
            "I could not find enough relevant evidence in the documentation."
        )

    title = best_article.get("title", "").strip()
    content = clean_content(best_article.get("content", ""))

    # The content heading is shorter than the metadata title.
    short_title = title.split("|")[0].strip()
    if short_title:
        content = re.sub(
            r"^\s*" + re.escape(short_title) + r"\s*",
            "",
            content,
            count=1,
            flags=re.IGNORECASE,
        ).strip(" :-|")

    # Select relevant sentences.
    sentences = re.split(r"(?<=[.!?])\s+", content)
    ranked_sentences = []
    seen_sentences = set()

    for sentence in sentences:
        sentence = sentence.strip()
        normalized = sentence.lower().rstrip(":").strip()

        if len(sentence) < 35 or len(sentence) > 450:
            continue

        matching_words = question_words & tokenize(sentence)
        if len(matching_words) < 2:
            continue

        if normalized in seen_sentences:
            continue

        ranked_sentences.append((len(matching_words), sentence))
        seen_sentences.add(normalized)

    ranked_sentences.sort(key=lambda item: item[0], reverse=True)
    selected_sentences = [
        sentence for _, sentence in ranked_sentences[:3]
    ]

    if not selected_sentences:
        return abstain(
            "I found a related article, but could not extract enough "
            "relevant evidence to answer confidently."
        )

    answer_text = " ".join(selected_sentences)

    # Remove the short heading if it remains in the answer.
    if short_title:
        answer_text = re.sub(
            re.escape(short_title),
            "",
            answer_text,
            count=1,
            flags=re.IGNORECASE,
        ).strip(" :-|")

    if not answer_text:
        return abstain("I could not extract a useful answer.")

    if len(answer_text) > 700:
        answer_text = answer_text[:697].rsplit(" ", 1)[0] + "..."

    source_url = best_article.get("url", "")

    return {
        "question": question,
        "answer": answer_text,
        "sources": (
            [{"title": title or "Untitled", "url": source_url}]
            if source_url else []
        ),
        "retrieval_score": best_score,
        "evidence_coverage": round(coverage, 2),
        "note": "Local prototype; no AI-generated answer.",
    }


if __name__ == "__main__":
    print("=== AI TECH CONSULTANT: KNOWLEDGE BRAIN ===")
    question = input("\nEnter your question: ").strip()
    result = answer_question(question)
    print("\n=== RESPONSE ===")
    print(json.dumps(result, indent=2, ensure_ascii=False))
