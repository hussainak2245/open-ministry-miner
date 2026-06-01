import os
import json
from collections import defaultdict

from dotenv import load_dotenv
from groq import Groq

from app.prompts import SYSTEM_PROMPT, build_annotation_prompt


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

if not GROQ_API_KEY:
    raise ValueError("Missing GROQ_API_KEY. Add it to your .env file.")


client = Groq(api_key=GROQ_API_KEY)


def clamp_stars(value):
    # LLMs sometimes return strings like "5" or "high".
    # We keep the app friendly and force stars into 1 to 5.
    try:
        stars = int(value)
    except Exception:
        return 3

    return max(1, min(stars, 5))


def normalize_quality_stars(annotation: dict) -> dict:
    annotation["overall_extraction_quality_stars"] = clamp_stars(
        annotation.get("overall_extraction_quality_stars", 3)
    )

    for entity in annotation.get("political_entities", []):
        entity["confidence_stars"] = clamp_stars(entity.get("confidence_stars", 3))

    for brief in annotation.get("speaker_briefs", []):
        brief["extraction_quality_stars"] = clamp_stars(
            brief.get("extraction_quality_stars", 3)
        )

    return annotation


def merge_same_speaker_briefs(annotation: dict) -> dict:
    briefs = annotation.get("speaker_briefs", [])

    merged = {}

    for brief in briefs:
        name = brief.get("speaker_name") or "Unknown"
        role = brief.get("speaker_role") or "Unknown"

        key = f"{name.lower()}::{role.lower()}"

        if key not in merged:
            merged[key] = {
                "speaker_name": brief.get("speaker_name"),
                "speaker_role": brief.get("speaker_role"),
                "state": brief.get("state"),
                "timestamp": brief.get("timestamp"),
                "topics": [],
                "combined_context_description": brief.get("combined_context_description"),
                "statements": [],
                "extraction_quality_stars": clamp_stars(
                    brief.get("extraction_quality_stars", 3)
                ),
            }

        merged[key]["statements"].extend(brief.get("statements", []))

        for topic in brief.get("topics", []):
            if topic not in merged[key]["topics"]:
                merged[key]["topics"].append(topic)

        old_stars = merged[key]["extraction_quality_stars"]
        new_stars = clamp_stars(brief.get("extraction_quality_stars", 3))
        merged[key]["extraction_quality_stars"] = max(old_stars, new_stars)

    annotation["speaker_briefs"] = list(merged.values())

    return annotation


def annotate_article(article: dict) -> dict:
    prompt = build_annotation_prompt(
        json.dumps(article, ensure_ascii=False, indent=2)
    )

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        response_format={"type": "json_object"},
    )

    raw_output = response.choices[0].message.content
    annotation = json.loads(raw_output)

    # The prompt asks the LLM to merge speakers.
    # This backup merge keeps things clean even if the LLM forgets.
    annotation = merge_same_speaker_briefs(annotation)
    annotation = normalize_quality_stars(annotation)

    return annotation