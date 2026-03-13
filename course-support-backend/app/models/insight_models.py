from pydantic import BaseModel


class TopicCount(BaseModel):
    topic: str
    count: int


class InsightSummary(BaseModel):
    weekly_questions: int
    unanswered_questions: int
    regrade_count: int
    top_topics: list[TopicCount]
