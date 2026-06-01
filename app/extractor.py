import re
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    response = requests.get(url, headers=headers, timeout=20)
    response.raise_for_status()
    return response.text


def clean_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None

    return re.sub(r"\s+", " ", text).strip()


def get_meta(soup: BeautifulSoup, name: str) -> Optional[str]:
    tag = soup.find("meta", attrs={"name": name})

    if not tag:
        tag = soup.find("meta", attrs={"property": name})

    if tag:
        return clean_text(tag.get("content"))

    return None


def detect_source(url: str) -> str:
    domain = urlparse(url).netloc.replace("www.", "")

    # Right now we only tested The Hindu.
    # Later this can become a source registry: HinduExtractor, IndianExpressExtractor, etc.
    if "thehindu.com" in domain:
        return "The Hindu"

    return domain


def detect_language_hint(soup: BeautifulSoup) -> Optional[str]:
    html_tag = soup.find("html")

    if html_tag:
        lang = html_tag.get("lang")
        if lang:
            return lang

    return None


def is_noise_paragraph(text: str) -> bool:
    noise_phrases = [
        "you don’t have any active subscription",
        "you don't have any active subscription",
        "subscribed with another email",
        "additional subscription benefits",
        "need help with your subscription",
        "unlock these with subscription",
        "comments have to be in english",
        "we have migrated to a new commenting platform",
        "copyright",
        "terms & conditions",
        "institutional subscriber",
        "the view from india",
        "first day first show",
        "today's cache",
        "science for all",
        "data point",
        "thedge",
        "health matters",
        "gender agenda",
        "the hindu on books",
    ]

    lowered = text.lower()
    return any(phrase in lowered for phrase in noise_phrases)


def extract_location_from_line(text: str) -> Optional[str]:
    # Example:
    # Published - June 01, 2026 02:42 pm IST - Thiruvananthapuram
    match = re.search(r"IST\s*-\s*([A-Za-z\s]+)$", text)

    if match:
        return clean_text(match.group(1))

    return None


def get_article_paragraphs(soup: BeautifulSoup) -> list[str]:
    article_tag = soup.find("article")
    candidate_paragraphs = article_tag.find_all("p") if article_tag else soup.find_all("p")

    paragraphs = []

    for p in candidate_paragraphs:
        text = clean_text(p.get_text())

        if not text:
            continue

        if len(text) < 40:
            continue

        if is_noise_paragraph(text):
            continue

        paragraphs.append(text)

    return paragraphs


def extract_article(url: str) -> dict:
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")

    title_tag = soup.find("h1")

    title = (
        get_meta(soup, "og:title")
        or (clean_text(title_tag.get_text()) if title_tag else None)
    )

    description = (
        get_meta(soup, "og:description")
        or get_meta(soup, "description")
    )

    author = (
        get_meta(soup, "author")
        or get_meta(soup, "article:author")
    )

    published_at = (
        get_meta(soup, "article:published_time")
        or get_meta(soup, "publish-date")
        or get_meta(soup, "publish_date")
    )

    updated_at = (
        get_meta(soup, "article:modified_time")
        or get_meta(soup, "modified-date")
        or get_meta(soup, "last-modified")
    )

    section = (
        get_meta(soup, "article:section")
        or get_meta(soup, "section")
    )

    image = get_meta(soup, "og:image")

    paragraphs = get_article_paragraphs(soup)

    location = None

    # We check paragraph by paragraph so location does not accidentally capture the next sentence.
    for paragraph in paragraphs:
        possible_location = extract_location_from_line(paragraph)
        if possible_location:
            location = possible_location
            break

    article_text = "\n\n".join(paragraphs)

    return {
        "url": url,
        "source": detect_source(url),
        "language_hint": detect_language_hint(soup),
        "title": title,
        "description": description,
        "author": author,
        "published_at": published_at,
        "updated_at": updated_at,
        "section": section,
        "location": location,
        "image": image,
        "text": article_text,
        "paragraphs": paragraphs,
        "paragraph_count": len(paragraphs),
    }