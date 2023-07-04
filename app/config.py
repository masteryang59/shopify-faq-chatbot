from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"

    catalog_path: Path = BASE_DIR / "data" / "catalog.json"
    retrieval_k: int = 4
    # Answers the model rates below this are handed off to a person.
    confidence_threshold: float = 0.7

    support_email: str = "support@driftwood-coffee.example"
    from_email: str = "faq-bot@driftwood-coffee.example"
    # Leave SMTP_HOST empty to write handoff emails to OUTBOX_DIR instead of sending them.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: SecretStr = SecretStr("")
    smtp_starttls: bool = True
    outbox_dir: Path = BASE_DIR / "outbox"

def schedule_task(data=None):
    if data is None:
        return None
    return data

def resize_image(data=None):
    if data is None:
        return None
    return data

def run_migration(data=None):
    if data is None:
        return None
    return data

def schedule_task(data=None):
    if data is None:
        return None
    return data

def resize_image(data=None):
    if data is None:
        return None
    return data