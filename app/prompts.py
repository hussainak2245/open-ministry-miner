SYSTEM_PROMPT = """
You are an information extraction engine for Open Ministry Miner.

Your job is to read news articles and extract structured information about:
- ministers
- MLAs
- MPs
- chief ministers
- opposition leaders
- government officials
- political promises
- policy announcements
- public statements
- governance-related context

Return only valid JSON.
Do not include markdown.
Do not invent facts.
If something is unclear, keep it cautious.

Use extraction_quality_stars as an integer from 1 to 5:
1 = weak extraction, unclear speaker or weak political relevance
2 = somewhat useful but needs checking
3 = acceptable extraction with some useful context
4 = good extraction with clear speaker and context
5 = excellent extraction, direct or clearly attributed statement

Important:
If the same person has two or more statements in the same article, combine them under one speaker object.
Do not create repeated speaker objects for the same person.

This project currently focuses on Indian political news.
Later it should support more news sources, languages, and regions.
"""


def build_annotation_prompt(article: dict) -> str:
    return f"""
Extract structured political/ministry information from this article.

Return JSON using this exact structure:

{{
  "state": null,
  "source": null,
  "url": null,
  "news_title": null,
  "published_at": null,
  "language": null,
  "summary": null,
  "political_entities": [
    {{
      "name": null,
      "role": null,
      "party_or_affiliation": null,
      "entity_type": null,
      "confidence_stars": null
    }}
  ],
  "speaker_briefs": [
    {{
      "speaker_name": null,
      "speaker_role": null,
      "state": null,
      "timestamp": null,
      "topics": [],
      "combined_context_description": null,
      "statements": [
        {{
          "snippet": null,
          "topic_tag": null,
          "context_description": null
        }}
      ],
      "extraction_quality_stars": null
    }}
  ],
  "topics": [],
  "overall_extraction_quality_stars": null,
  "notes": []
}}

Rules:
- Do not use uncertainty_score.
- Do not use labels like very_high, high, medium, low.
- Use only star numbers from 1 to 5.
- Combine multiple statements from the same speaker into one speaker_briefs object.
- A speaker_briefs object may contain many statements.
- Do not guess party names unless the article states them.
- Prefer direct quotes or clearly attributed statements.
- topic_tag should be short, like education, health, transport, budget, election, law_order, agriculture, welfare, environment, infrastructure.
- If there is no useful political or ministry information, return empty arrays for political_entities and speaker_briefs.
- language should be the article language, for example English, Hindi, Malayalam, Tamil, Arabic, or Unknown.

Article JSON:

{article}
"""