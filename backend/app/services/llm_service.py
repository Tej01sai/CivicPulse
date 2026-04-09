"""LLM service using Claude 3.5 Sonnet for structured need extraction."""

import json
import logging
import base64
from typing import Optional

import anthropic

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# System prompt for need extraction (from PRD Appendix B)
EXTRACTION_SYSTEM_PROMPT = """You are an expert social worker and data analyst helping an NGO platform.
Your job is to extract structured community needs from messy field notes, survey text, or reports.
Always respond with valid JSON only — no explanation, no markdown, just the JSON object.

Extract these fields (use null if genuinely unknown, don't guess):
- need_type: one of [Housing, Food, Health, Transport, Home Repair, Job Training, Mental Health, Other]
- need_subtype: more specific description (e.g., "Structural - Roof", "Emergency Shelter")
- beneficiary_age_range: one of [child, teen, adult, senior, family, unknown]
- location_address: street address if mentioned
- location_district: district/area name if mentioned
- urgency: one of [CRITICAL, HIGH, MEDIUM, LOW] — based on described severity
- urgency_reason: 1-2 sentences explaining the urgency rating
- skills_needed: array of skills required (e.g., ["carpentry", "roofing", "social work"])
- affected_population: estimated number of people affected (integer)
- resource_gaps: what's missing to resolve this need
- estimated_effort_hours: rough hours to resolve (number)
- confidence_score: your confidence in this extraction, 0.0-1.0"""

RECOMMENDATION_PROMPT = """You are advising an NGO coordinator on how best to respond to a community need.
Based on the need details below, provide 1-2 concrete, actionable intervention recommendations.
Be specific. Reference similar intervention patterns if applicable.
Keep your response to 2-3 sentences maximum."""


def _get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def parse_need_from_text(text: str) -> dict:
    """
    Call Claude 3.5 to extract structured need data from unstructured field notes.
    Returns a dict matching ParseResponse schema.
    """
    client = _get_client()
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=EXTRACTION_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Extract the community need from this text:\n\n{text}"
                }
            ]
        )
        raw = response.content[0].text.strip()
        # Strip markdown code fences if Claude wraps output
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw)
        result["raw_input"] = text
        return result
    except json.JSONDecodeError as e:
        logger.error(f"Claude returned invalid JSON: {e}")
        return {"raw_input": text, "confidence_score": 0.0, "urgency": "MEDIUM"}
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        return {"raw_input": text, "confidence_score": 0.0, "urgency": "MEDIUM"}


def parse_need_from_image(image_bytes: bytes, content_type: str = "image/jpeg") -> dict:
    """
    Call Claude 3.5 Vision to extract need data from a survey photo.
    """
    client = _get_client()
    try:
        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        media_type = content_type if content_type in [
            "image/jpeg", "image/png", "image/gif", "image/webp"
        ] else "image/jpeg"

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            system=EXTRACTION_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": "This is a paper survey or field report photo. Extract the community need from it."
                        }
                    ],
                }
            ],
        )
        raw = response.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw)
        result["raw_input"] = "[Image upload]"
        return result
    except Exception as e:
        logger.error(f"Vision extraction failed: {e}")
        return {"raw_input": "[Image upload]", "confidence_score": 0.0, "urgency": "MEDIUM"}


def generate_recommendations(need_dict: dict) -> Optional[str]:
    """
    Generate 1-2 actionable intervention recommendations for a given need.
    Used in the needs detail view.
    """
    client = _get_client()
    try:
        need_summary = json.dumps({
            k: need_dict.get(k) for k in [
                "need_type", "urgency", "urgency_reason", "skills_needed",
                "location_district", "affected_population", "resource_gaps"
            ]
        }, indent=2)

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=256,
            system=RECOMMENDATION_PROMPT,
            messages=[
                {"role": "user", "content": f"Community need:\n{need_summary}"}
            ]
        )
        return response.content[0].text.strip()
    except Exception as e:
        logger.error(f"Recommendation generation failed: {e}")
        return None
