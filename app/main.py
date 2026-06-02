from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import requests
from bs4 import BeautifulSoup

from app.extractor import extract_article
from app.annotator import annotate_article


app = FastAPI(
    title="Open Ministry Miner",
    description="Extracts ministry and political information from news article links.",
    version="0.1.0",
)

class ArticleRequest(BaseModel):
    url: str

class BatchRequest(BaseModel):
    source: str = "thehindu"
    limit: int = 20

def get_the_hindu_urls(limit: int = 20) -> list[str]:
    """Fetch article URLs from The Hindu Kerala section."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
    }
    try:
        res = requests.get(
            "https://www.thehindu.com/news/national/kerala/",
            headers=headers,
            timeout=30,
        )
        soup = BeautifulSoup(res.text, "html.parser")
        urls = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("/"):
                href = f"https://www.thehindu.com{href}"
            if "/kerala/" in href and "/article" in href:
                urls.add(href.split("?")[0])
        return list(urls)[:limit]
    except Exception as e:
        return []
    
@app.get("/")
def home():
    return {
        "app": "Open Ministry Miner",
        "status": "running",
        "endpoints": {
            "mine": "POST /mine — mine a single article URL",
            "batch": "POST /batch — scrape and mine latest articles",
            "extract": "POST /extract — extract article without annotation",
        },
    }

@app.post("/extract")
def extract_only(request: ArticleRequest):
    article = extract_article(request.url)
    return article

@app.post("/mine")
def mine_article(request: ArticleRequest):
    article = extract_article(request.url)
    annotation = annotate_article(article)
    return {
        "article": article,
        "annotation": annotation,
    }

@app.post("/batch")
def batch_mine(request: BatchRequest):
    """
    Scrape latest articles from a source and mine them all.
    Returns structured statements ready for openMinistry.
    """
    if request.source == "thehindu":
        urls = get_the_hindu_urls(request.limit)
    else:
        return {"error": f"Unknown source: {request.source}"}

    results = []
    errors = []

    for url in urls:
        try:
            article = extract_article(url)
            annotation = annotate_article(article)

            # Only return articles with useful political content
            speaker_briefs = annotation.get("speaker_briefs", [])
            if not speaker_briefs:
                continue

            results.append({
                "url": url,
                "title": article.get("title"),
                "published_at": article.get("published_at"),
                "source": article.get("source"),
                "language": article.get("language_hint"),
                "speaker_briefs": speaker_briefs,
                "topics": annotation.get("topics", []),
                "overall_quality": annotation.get(
                    "overall_extraction_quality_stars"
                ),
            })
        except Exception as e:
            errors.append({"url": url, "error": str(e)})

    return {
        "processed": len(urls),
        "articles_with_statements": len(results),
        "errors": len(errors),
        "results": results,
    }