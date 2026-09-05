"""Watch for newly-mounted removable storage (or configured folders) and
hand off newly detected volumes to a callback.

Real hotplug notifications differ per OS; the portable, dependency-light
approach used here is to poll ``psutil.disk_partitions()`` and diff the
mount points seen against the previous poll. Anything listed in
``settings.watch_paths`` is treated the same way, which is what makes this
testable without real hardware: point ``WATCH_PATHS`` at a folder full of
sample photos and the watcher treats it exactly like a freshly inserted card.
"""
from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable

import psutil

from app.config import settings

logger = logging.getLogger(__name__)

OnNewVolume = Callable[[str], None]


def current_mount_points() -> set[str]:
    mounts = {p.mountpoint for p in psutil.disk_partitions(all=False)}
    mounts.update(settings.watch_paths)
    return mounts


class StorageWatcher:
    """Polls for newly-mounted volumes and invokes a callback for each."""

    def __init__(
        self,
        on_new_volume: OnNewVolume,
        *,
        poll_interval_seconds: float | None = None,
    ) -> None:
        self._on_new_volume = on_new_volume
        self._poll_interval = poll_interval_seconds or settings.poll_interval_seconds
        self._seen: set[str] = set()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self, *, treat_existing_as_new: bool = False) -> None:
        if treat_existing_as_new:
            self._seen = set()
        else:
            self._seen = current_mount_points()

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=self._poll_interval * 2)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._poll_once()
            except Exception:
                logger.exception("Error while polling for removable storage")
            self._stop_event.wait(self._poll_interval)

    def _poll_once(self) -> None:
        current = current_mount_points()
        new_mounts = current - self._seen
        self._seen = current
        for mount in sorted(new_mounts):
            logger.info("Detected new volume: %s", mount)
            self._on_new_volume(mount)
