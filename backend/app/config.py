"""Environment-driven configuration for the Autopost backend."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("AUTOPOST_DATA_DIR", BASE_DIR / "data"))
MEDIA_DIR = DATA_DIR / "media"


def _split_paths(value: str) -> list[str]:
    return [p.strip() for p in value.split(",") if p.strip()]


@dataclass
class Settings:
    # Ingestion
    watch_paths: list[str] = field(
        default_factory=lambda: _split_paths(os.environ.get("WATCH_PATHS", ""))
    )
    poll_interval_seconds: float = float(os.environ.get("POLL_INTERVAL_SECONDS", "3"))
    min_photos_per_event: int = int(os.environ.get("MIN_PHOTOS_PER_EVENT", "1"))
    max_lookback_days: int = int(os.environ.get("MAX_LOOKBACK_DAYS", "365"))
    burst_gap_minutes: float = float(os.environ.get("BURST_GAP_MINUTES", "45"))

    # Storage
    database_url: str = os.environ.get(
        "DATABASE_URL", f"sqlite:///{DATA_DIR / 'app.db'}"
    )
    media_dir: Path = MEDIA_DIR

    # Events website
    events_website_base_url: str = os.environ.get("EVENTS_WEBSITE_BASE_URL", "")
    events_website_api_key: str = os.environ.get("EVENTS_WEBSITE_API_KEY", "")
    stub_events_file: str = os.environ.get(
        "STUB_EVENTS_FILE", str(BASE_DIR / "app" / "events" / "sample_events.json")
    )

    # Meta / Graph API
    meta_access_token: str = os.environ.get("META_ACCESS_TOKEN", "")
    meta_page_id: str = os.environ.get("META_PAGE_ID", "")
    ig_business_account_id: str = os.environ.get("IG_BUSINESS_ACCOUNT_ID", "")
    graph_api_base_url: str = os.environ.get(
        "GRAPH_API_BASE_URL", "https://graph.facebook.com/v19.0"
    )
    public_base_url: str = os.environ.get("PUBLIC_BASE_URL", "")

    @property
    def meta_configured(self) -> bool:
        return bool(self.meta_access_token and self.meta_page_id)


settings = Settings()

DATA_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
