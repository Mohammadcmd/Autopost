"""SQLAlchemy models for import sessions, events, photos, and post records."""
from __future__ import annotations

import enum
import json
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Decision(str, enum.Enum):
    PENDING = "pending"
    KEEP = "keep"
    DELETE = "delete"


class PostStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    DRY_RUN = "dry_run"
    POSTED = "posted"
    FAILED = "failed"


class ImportSession(Base):
    __tablename__ = "import_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_path: Mapped[str] = mapped_column(String(1024))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    events: Mapped[list["Event"]] = relationship(back_populates="session")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("import_sessions.id"))
    event_date: Mapped[str] = mapped_column(String(10))
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime] = mapped_column(DateTime)

    website_event_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website_event_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    website_event_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website_event_organizations_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    caption_draft: Mapped[str | None] = mapped_column(Text, nullable=True)
    post_status: Mapped[PostStatus] = mapped_column(
        Enum(PostStatus), default=PostStatus.NOT_STARTED
    )

    session: Mapped[ImportSession] = relationship(back_populates="events")
    photos: Mapped[list["Photo"]] = relationship(
        back_populates="event", order_by="Photo.captured_at"
    )
    posts: Mapped[list["PostRecord"]] = relationship(back_populates="event")

    @property
    def photo_count(self) -> int:
        return len(self.photos)

    @property
    def website_event_organizations(self) -> list[str]:
        if not self.website_event_organizations_json:
            return []
        return json.loads(self.website_event_organizations_json)

    @website_event_organizations.setter
    def website_event_organizations(self, organizations: list[str]) -> None:
        self.website_event_organizations_json = json.dumps(organizations) if organizations else None


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    original_path: Mapped[str] = mapped_column(String(1024))
    edited_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime)
    decision: Mapped[Decision] = mapped_column(Enum(Decision), default=Decision.PENDING)

    event: Mapped[Event] = relationship(back_populates="photos")


class PostRecord(Base):
    __tablename__ = "post_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    platform: Mapped[str] = mapped_column(String(32))
    dry_run: Mapped[bool] = mapped_column(default=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    event: Mapped[Event] = relationship(back_populates="posts")
