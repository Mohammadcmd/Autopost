"""FastAPI application entry point."""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import routes_post, routes_review, routes_sessions
from app.db.session import SessionLocal, init_db
from app.ingest.service import NoEventFoundError, ingest_path
from app.ingest.watcher import StorageWatcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _on_new_volume(mount_point: str) -> None:
    db = SessionLocal()
    try:
        ingest_path(mount_point, db)
        logger.info("Ingested new volume: %s", mount_point)
    except NoEventFoundError:
        logger.info("No usable photos found on %s", mount_point)
    except Exception:
        logger.exception("Failed to ingest volume %s", mount_point)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    watcher: StorageWatcher | None = None
    if os.environ.get("AUTO_WATCH", "false").lower() == "true":
        watcher = StorageWatcher(_on_new_volume)
        watcher.start()

    yield

    if watcher is not None:
        watcher.stop()


app = FastAPI(title="Autopost", lifespan=lifespan)

app.include_router(routes_sessions.router)
app.include_router(routes_review.router)
app.include_router(routes_post.router)

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
