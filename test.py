import sys
import json
from pathlib import Path

from app.extractor import extract_article
from app.annotator import annotate_article


def save_json(data: dict, filename: str) -> None:
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    path = output_dir / filename

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Saved: {path}")


def main():
    if len(sys.argv) != 2:
        print("Usage:")
        print('  python3 test.py "https://example.com/news/article"')
        sys.exit(1)

    url = sys.argv[1]

    print("Step 1: extracting the article")
    article = extract_article(url)

    print("\nArticle preview:")
    print(json.dumps({
        "title": article.get("title"),
        "source": article.get("source"),
        "language_hint": article.get("language_hint"),
        "published_at": article.get("published_at"),
        "section": article.get("section"),
        "location": article.get("location"),
        "paragraph_count": article.get("paragraph_count"),
        "text_preview": article.get("text", "")[:500],
    }, indent=2, ensure_ascii=False))

    save_json(article, "article_output.json")

    print("\nStep 2: asking Groq to annotate the article")
    annotation = annotate_article(article)

    print("\nAnnotation result:")
    print(json.dumps(annotation, indent=2, ensure_ascii=False))

    save_json(annotation, "annotation_output.json")


if __name__ == "__main__":
    main()