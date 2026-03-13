import os
from dotenv import load_dotenv

load_dotenv()


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    def __init__(self) -> None:
        self.app_name = os.getenv("APP_NAME", "Course Support Backend")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.use_dynamodb = _parse_bool(os.getenv("USE_DYNAMODB"), default=False)
        self.use_bedrock = _parse_bool(os.getenv("USE_BEDROCK"), default=True)
        self.bedrock_model_id = os.getenv(
            "BEDROCK_MODEL_ID", "us.amazon.nova-2-lite-v1:0"
        )
        self.use_canvas_mcp = _parse_bool(os.getenv("USE_CANVAS_MCP"), default=False)
        self.canvas_mcp_url = os.getenv(
            "CANVAS_MCP_URL", "https://mcp.illinihunt.org/mcp"
        )
        self.canvas_api_url = os.getenv("CANVAS_API_URL", "")
        self.canvas_api_token = os.getenv("CANVAS_API_TOKEN", "")
        self.emails_table = os.getenv("EMAILS_TABLE", "Emails")
        self.regrade_requests_table = os.getenv(
            "REGRADE_REQUESTS_TABLE", "RegradeRequests"
        )
        cors_origins = os.getenv("CORS_ORIGINS", "*")
        self.cors_origins = [
            origin.strip() for origin in cors_origins.split(",") if origin.strip()
        ] or ["*"]


settings = Settings()
