from __future__ import annotations

import sys
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings


EMAIL_SEED_ITEMS = [
    {
        "email_id": "1",
        "course_id": "ECE101",
        "sender": "student1@university.com",
        "subject": "Question about assignment deadline",
        "body": "Hi professor, is the assignment due tonight at 11:59 PM?",
        "received_at": "2026-03-13T10:00:00Z",
        "status": "pending_review",
        "classification": "routine",
        "sentiment": "neutral",
        "needs_escalation": False,
        "insight_tags": ["assignment", "deadline"],
        "suggested_reply": "Hi, yes, the assignment is due tonight at 11:59 PM as stated on the course page.",
    },
    {
        "email_id": "2",
        "course_id": "ECE101",
        "sender": "student2@university.com",
        "subject": "Regrade request for quiz 2",
        "body": "Hello, I think my short answer for question 3 deserves more marks.",
        "received_at": "2026-03-13T11:00:00Z",
        "status": "flagged",
        "classification": "regrade",
        "sentiment": "frustrated",
        "needs_escalation": True,
        "insight_tags": ["regrade", "quiz2"],
        "suggested_reply": "Thanks for reaching out. Your request has been noted and will be reviewed according to the course regrade policy.",
    },
]


def main() -> None:
    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)

    ensure_table(
        dynamodb=dynamodb,
        table_name=settings.emails_table,
        partition_key="email_id",
    )
    ensure_table(
        dynamodb=dynamodb,
        table_name=settings.regrade_requests_table,
        partition_key="request_id",
    )

    emails_table = dynamodb.Table(settings.emails_table)
    for item in EMAIL_SEED_ITEMS:
        emails_table.put_item(Item=item)

    print(f"Seeded {len(EMAIL_SEED_ITEMS)} email records into {settings.emails_table}.")
    print(
        "DynamoDB bootstrap complete. Set USE_DYNAMODB=true and run the FastAPI app."
    )


def ensure_table(dynamodb, table_name: str, partition_key: str) -> None:
    existing_tables = dynamodb.meta.client.list_tables()["TableNames"]
    if table_name in existing_tables:
        print(f"Table {table_name} already exists.")
        return

    print(f"Creating table {table_name}...")
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{"AttributeName": partition_key, "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": partition_key, "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        time.sleep(1)
        print(f"Table {table_name} created.")
    except ClientError as exc:
        raise RuntimeError(f"Failed to create table {table_name}: {exc}") from exc


if __name__ == "__main__":
    try:
        main()
    except NoCredentialsError as exc:
        raise SystemExit(
            "AWS credentials were not found. Configure credentials first, then rerun "
            "`venv\\Scripts\\python.exe scripts\\bootstrap_dynamodb.py`."
        ) from exc
