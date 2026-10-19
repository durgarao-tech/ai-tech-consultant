
import asyncio
import json
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

import httpx
from bs4 import BeautifulSoup


SITEMAP_URL = (
    "https://support.brilliantdirectories.com/support/sitemap.xml"
)

DATA_DIR = Path("data")
OUTPUT_FILE = DATA_DIR / "articles.json"
CHECKPOINT_FILE = DATA_DIR / "checkpoint.json"

HEADERS = {
    "User-Agent": "AI-Tech-Consultant-Student-Project/1.0"
}

# False = incremental mode.
# True = refresh every URL during the next run.
RECRAWL_ALL = False

# Refresh articles older than this many days.
REFRESH_AFTER_DAYS = 7

# Wait between requests to avoid overloading the website.
REQUEST_DELAY_SECONDS = 1

CONTENT_SELECTORS = [
    "[itemprop='articleBody']",
    ".solution-content",
    ".article-body",
    ".solution-body",
    ".article-content",
    ".solution-content-wrapper",
    "article",
    "main",
    "#content",
]


def clean_text(text):
    """Normalize whitespace and remove repeated or irrelevant lines."""
    cleaned_lines = []
    previous_line = ""

    unwanted_phrases = [
        "what do you need help with?",
        "enter your search term here",
        "solution home",
    ]

    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()

        if not line:
            continue

        if any(
            phrase in line.lower()
            for phrase in unwanted_phrases
        ):
            continue

        if line == previous_line:
            continue

        cleaned_lines.append(line)
        previous_line = line

    return "\n".join(cleaned_lines).strip()


def extract_page(soup, url):
    """Extract the page title and best available content."""

    for element in soup.select(
        "script, style, nav, footer, header, noscript, "
        "iframe, svg, form, button, input, select, textarea"
    ):
        element.decompose()

    for element in soup.select(
        ".breadcrumb, .breadcrumbs, .sidebar, "
        ".cookie-banner, .cookie-notice, .search-box, "
        ".search-form, .pagination, .social-share"
    ):
        element.decompose()

    title = (
        soup.title.get_text(" ", strip=True)
        if soup.title
        else url
    )

    content_region = None

    for selector in CONTENT_SELECTORS:
        candidate = soup.select_one(selector)

        if candidate:
            candidate_text = candidate.get_text(
                "\n", strip=True
            )

            if len(candidate_text) >= 200:
                content_region = candidate
                break

    if content_region is None:
        content_region = soup.body or soup

    raw_text = content_region.get_text("\n", strip=True)
    content = clean_text(raw_text)

    return title, content


def load_json(path, default):
    """Load JSON safely, or return the default if the file is absent."""
    if not path.exists():
        return default

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_progress(articles, completed):
    """Save article data and checkpoint without losing progress."""

    article_data = list(articles.values())

    temp_articles = OUTPUT_FILE.with_suffix(".tmp")
    temp_articles.write_text(
        json.dumps(
            article_data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    temp_articles.replace(OUTPUT_FILE)

    temp_checkpoint = CHECKPOINT_FILE.with_suffix(".tmp")
    temp_checkpoint.write_text(
        json.dumps(sorted(completed), indent=2),
        encoding="utf-8",
    )
    temp_checkpoint.replace(CHECKPOINT_FILE)


def should_fetch(url, completed, articles, now):
    """Decide whether a URL needs to be downloaded."""

    if RECRAWL_ALL:
        return True

    # Retry URLs that are not marked complete or have no saved article.
    if url not in completed or url not in articles:
        return True

    fetched_at = articles[url].get("fetched_at", "")

    try:
        fetched_date = datetime.fromisoformat(
            fetched_at.replace("Z", "+00:00")
        )

        if fetched_date.tzinfo is None:
            fetched_date = fetched_date.replace(
                tzinfo=timezone.utc
            )

        age = now - fetched_date

        # Refresh old articles.
        return age >= timedelta(days=REFRESH_AFTER_DAYS)

    except (ValueError, TypeError, AttributeError):
        # Retry records with missing or invalid timestamps.
        return True


async def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing articles and preserve their data.
    existing_records = load_json(OUTPUT_FILE, [])

    articles = {
        article["url"]: article
        for article in existing_records
        if isinstance(article, dict) and article.get("url")
    }

    # The checkpoint remains a JSON list of completed URLs.
    completed = set(load_json(CHECKPOINT_FILE, []))

    failed_urls = []
    processed = 0
    skipped = 0

    timeout = httpx.Timeout(30.0)

    async with httpx.AsyncClient(
        headers=HEADERS,
        timeout=timeout,
        follow_redirects=True,
    ) as client:

        print("Downloading sitemap...")

        response = await client.get(SITEMAP_URL)
        response.raise_for_status()

        root = ET.fromstring(response.content)

        namespace = {
            "sm": "http://www.sitemaps.org/schemas/sitemap/0.9"
        }

        urls = sorted({
            node.text.strip()
            for node in root.findall(".//sm:loc", namespace)
            if node.text and node.text.strip()
        })

        # Only crawl the official support website.
        urls = [
            url for url in urls
            if urlparse(url).scheme in ("http", "https")
            and urlparse(url).netloc.lower()
            == "support.brilliantdirectories.com"
        ]

        print(f"Found {len(urls)} URLs.")
        print(
            "Mode:",
            "FULL REFRESH" if RECRAWL_ALL else "INCREMENTAL",
        )

        now = datetime.now(timezone.utc)

        for index, url in enumerate(urls, start=1):

            if not should_fetch(url, completed, articles, now):
                skipped += 1
                continue

            try:
                page = await client.get(url)
                page.raise_for_status()

                soup = BeautifulSoup(page.text, "lxml")
                title, content = extract_page(soup, url)

                if not content:
                    failed_urls.append(url)
                    print(f"Empty page; will retry later: {url}")
                    continue

                # Save or update the article only after successful extraction.
                articles[url] = {
                    "url": url,
                    "title": title,
                    "content": content,
                    "fetched_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                }

                completed.add(url)
                processed += 1

                print(
                    f"Updated: {processed} | "
                    f"Checked: {index}/{len(urls)}"
                )

            except (httpx.HTTPError, ET.ParseError, ValueError) as error:
                failed_urls.append(url)
                print(f"Failed; will retry later: {url} — {error}")

            except Exception as error:
                failed_urls.append(url)
                print(f"Unexpected error for {url}: {error}")

            finally:
                # Save regularly, including after failed requests.
                if index % 10 == 0:
                    save_progress(articles, completed)
                    print(f"Progress saved at {index}/{len(urls)}")

                await asyncio.sleep(REQUEST_DELAY_SECONDS)

        # Save all final progress.
        save_progress(articles, completed)

    print("\nIngestion finished.")
    print(f"Articles saved: {len(articles)}")
    print(f"URLs skipped (still fresh): {skipped}")
    print(f"URLs updated successfully: {processed}")
    print(f"Failed or empty URLs: {len(failed_urls)}")
    print(f"Articles file: {OUTPUT_FILE.resolve()}")
    print(f"Checkpoint file: {CHECKPOINT_FILE.resolve()}")

    if failed_urls:
        print(
            "\nSome URLs failed. They were not newly marked complete "
            "and can be retried on a later run."
        )


if __name__ == "__main__":
    asyncio.run(main())
