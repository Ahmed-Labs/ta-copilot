from __future__ import annotations
from typing import Optional, List

import json
import re
from functools import lru_cache

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings


def analyze_email(
    subject: str,
    body: str,
    current_classification: str = "unclassified",
    additional_context: Optional[str] = None,
):
    if settings.use_bedrock:
        try:
            result_text = _invoke_bedrock(
                model_id=settings.bedrock_model_id,
                prompt=_build_analysis_prompt(
                    subject=subject,
                    body=body,
                    current_classification=current_classification,
                    additional_context=additional_context,
                ),
            )
            parsed = _parse_bedrock_json(result_text)
            return _normalize_analysis(
                parsed,
                subject=subject,
                body=body,
                current_classification=current_classification,
            )
        except (ClientError, BotoCoreError, RuntimeError, ValueError):
            pass

    return _fallback_analysis(
        subject=subject,
        body=body,
        current_classification=current_classification,
    )


def generate_placeholder_reply(subject: str, body: str, classification: str):
    return analyze_email(
        subject=subject,
        body=body,
        current_classification=classification,
    )


@lru_cache(maxsize=1)
def _get_bedrock_client():
    return boto3.client("bedrock-runtime", region_name=settings.aws_region)


def _invoke_bedrock(model_id: str, prompt: str) -> str:
    response = _get_bedrock_client().converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 1200, "temperature": 0.2},
    )
    return response["output"]["message"]["content"][0]["text"]


def _build_analysis_prompt(
    subject: str,
    body: str,
    current_classification: str,
    additional_context: Optional[str] = None,
) -> str:
    context_block = ""
    if additional_context:
        context_block = f"""
Additional trusted course context:
{additional_context}
"""

    return f"""You are an AI teaching support agent for a university course inbox.

Analyze the student email and return ONLY valid JSON with this exact structure:
{{
  "classification": "routine|regrade|escalate",
  "sentiment": "positive|neutral|negative|frustrated|confused|urgent|unknown",
  "needs_escalation": true,
  "assigned_to": "automated|ta|instructor|admin",
  "insight_tags": ["tag1", "tag2"],
  "suggested_reply": "brief professional reply"
}}

Rules:
- Use "routine" for normal course questions that can receive a drafted reply.
- Use "regrade" for grade disputes, rubric disputes, marks review, or reassessment requests.
- Use "escalate" for personal, sensitive, unusual, angry, ambiguous, or high-risk messages.
- If additional trusted context includes announcements, assignments, grade, submission, or course data, use it.
- Prefer answering from the trusted Canvas context when it clearly resolves the question.
- Keep insight_tags short and specific.
- The suggested_reply should be safe for instructor review.

Current classification hint: {current_classification}
Subject: {subject}
Email body:
{body}
{context_block}
"""


def _parse_bedrock_json(result_text: str) -> dict:
    cleaned = result_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            raise ValueError("Bedrock response did not contain JSON")
        return json.loads(match.group(0))


def _normalize_analysis(
    parsed: dict,
    subject: str,
    body: str,
    current_classification: str,
) -> dict:
    raw_classification = str(parsed.get("classification", current_classification)).lower()
    classification = _normalize_classification(raw_classification, subject, body)
    insight_tags = parsed.get("insight_tags") or _build_insight_tags(
        subject=subject,
        body=body,
        classification=classification,
    )
    if not isinstance(insight_tags, list):
        insight_tags = [str(insight_tags)]

    needs_escalation = parsed.get("needs_escalation")
    if needs_escalation is None:
        needs_escalation = classification != "routine"

    assigned_to = str(parsed.get("assigned_to", "")).lower() or (
        "automated" if classification == "routine" else "instructor"
    )
    if assigned_to not in {"automated", "ta", "instructor", "admin"}:
        assigned_to = "instructor"

    sentiment = str(parsed.get("sentiment", "unknown")).lower()
    if sentiment not in {
        "positive",
        "neutral",
        "negative",
        "frustrated",
        "confused",
        "urgent",
        "unknown",
    }:
        sentiment = "unknown"

    suggested_reply = str(parsed.get("suggested_reply", "")).strip()
    if not suggested_reply:
        suggested_reply = _fallback_analysis(
            subject=subject,
            body=body,
            current_classification=classification,
        )["suggested_reply"]

    return {
        "classification": classification,
        "sentiment": sentiment,
        "needs_escalation": bool(needs_escalation),
        "assigned_to": assigned_to,
        "insight_tags": list(dict.fromkeys(str(tag).lower() for tag in insight_tags if str(tag).strip())),
        "suggested_reply": suggested_reply,
    }


def _normalize_classification(raw_classification: str, subject: str, body: str) -> str:
    combined = f"{raw_classification} {subject} {body}".lower()
    regrade_terms = [
        "regrade",
        "remark",
        "re-mark",
        "rubric",
        "partial credit",
        "partial marks",
        "deserve more",
        "grade appeal",
        "appeal my grade",
        "unfairly graded",
        "grading mistake",
        "points back",
        "lost marks",
    ]
    routine_grade_terms = [
        "grade posted",
        "grades posted",
        "grade release",
        "when will grades",
        "when are grades",
        "has my grade",
        "is my grade",
        "check my grade",
        "grade status",
    ]

    if any(term in combined for term in regrade_terms):
        return "regrade"
    if any(term in combined for term in routine_grade_terms):
        return "routine"
    if any(term in combined for term in ["complaint", "urgent", "sensitive", "exception", "appeal"]):
        return "escalate"
    if raw_classification in {"routine", "regrade", "escalate"}:
        return raw_classification
    if raw_classification in {"question", "request", "feedback", "other"}:
        return "routine"
    return "escalate"


def _fallback_analysis(subject: str, body: str, current_classification: str) -> dict:
    normalized_body = body.lower()
    classification = _normalize_classification(current_classification, subject, body)
    tags = _build_insight_tags(subject=subject, body=body, classification=classification)

    if classification == "routine":
        return {
            "classification": "routine",
            "sentiment": "neutral",
            "needs_escalation": False,
            "assigned_to": "automated",
            "insight_tags": tags,
            "suggested_reply": (
                f"Suggested reply: Thanks for your email about '{subject}'. "
                "This looks like a routine course question. Please check the syllabus, "
                "announcements, and assignment instructions first, and let us know if anything is still unclear."
            ),
        }

    if classification == "regrade":
        return {
            "classification": "regrade",
            "sentiment": "frustrated",
            "needs_escalation": True,
            "assigned_to": "instructor",
            "insight_tags": tags,
            "suggested_reply": (
                "Suggested reply: Thanks for your message. Your regrade request has been received "
                "and will be reviewed according to the course regrade process."
            ),
        }

    if "urgent" in normalized_body or "complaint" in normalized_body:
        classification = "escalate"

    return {
        "classification": classification,
        "sentiment": "negative" if classification == "escalate" else "unknown",
        "needs_escalation": True,
        "assigned_to": "instructor",
        "insight_tags": tags,
        "suggested_reply": (
            "Suggested reply: Thanks for your email. This message appears to need instructor review "
            "before a response is sent."
        ),
    }


def _build_insight_tags(subject: str, body: str, classification: str) -> List[str]:
    combined = f"{subject} {body}".lower()
    tags = [classification]

    if "assignment" in combined:
        tags.append("assignment")
    if "deadline" in combined or "due" in combined:
        tags.append("deadline")
    if "quiz" in combined:
        tags.append("quiz")
    if "regrade" in combined or "marks" in combined:
        tags.append("regrade")

    return list(dict.fromkeys(tags))
