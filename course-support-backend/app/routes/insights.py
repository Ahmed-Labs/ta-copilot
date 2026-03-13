from fastapi import APIRouter
from app.models.insight_models import InsightSummary, TopicCount
from app.services.dynamodb_service import get_all_emails, get_all_regrade_requests

router = APIRouter()


@router.get("/summary", response_model=InsightSummary)
def get_summary():
    emails = get_all_emails()

    weekly_questions = len(emails)
    unanswered_questions = sum(
        1 for email in emails if email.status != "review_ready"
    )
    regrade_count = len(get_all_regrade_requests())

    topic_counts: dict[str, int] = {}
    for email in emails:
        for tag in email.insight_tags:
            topic_counts[tag] = topic_counts.get(tag, 0) + 1

    top_topics = sorted(
        topic_counts.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    return {
        "weekly_questions": weekly_questions,
        "unanswered_questions": unanswered_questions,
        "regrade_count": regrade_count,
        "top_topics": [
            TopicCount(topic=topic, count=count)
            for topic, count in top_topics
        ],
    }
