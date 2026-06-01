from fastapi import FastAPI
from pydantic import BaseModel

from app.extractor import extract_article
from app.annotator import annotate_article


app = FastAPI(
    title="Open Ministry Miner",
    description="Extracts ministry and political information from news article links.",
    version="0.1.0",
)


class ArticleRequest(BaseModel):
    url: str


@app.get("/")
def home():
    return {
        "app": "Open Ministry Miner",
        "status": "running",
        "message": "Send a news article URL to /mine",
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