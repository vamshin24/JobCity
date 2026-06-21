"""Background scheduler for periodic ATS job ingestion.

Uses APScheduler's AsyncIOScheduler so we share the FastAPI event loop.
The actual fetching/normalizing/upserting lives in ``ingest.runner``.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger("jobcity.scheduler")
_scheduler: AsyncIOScheduler | None = None
_state: dict = {
    "running": False,
    "last_run_at": None,
    "last_summary": None,
    "last_error": None,
}


def state() -> dict:
    return dict(_state)


async def _run_job():
    from ingest.runner import run_ingest
    _state["running"] = True
    try:
        summary = await run_ingest()
        _state["last_summary"] = summary
        _state["last_run_at"] = datetime.now(timezone.utc).isoformat()
        _state["last_error"] = None
        logger.info("ingest run finished: %s", summary)
    except Exception as e:  # noqa: BLE001
        _state["last_error"] = str(e)
        logger.exception("ingest run failed: %s", e)
    finally:
        _state["running"] = False


def start() -> None:
    """Boot the scheduler. Idempotent — calling twice is a no-op."""
    global _scheduler
    if _scheduler is not None:
        return
    if os.environ.get("INGEST_SCHEDULER_DISABLED") == "1":
        logger.info("INGEST_SCHEDULER_DISABLED=1 — skipping background scheduler")
        return

    interval_hours = int(os.environ.get("INGEST_INTERVAL_HOURS", "6"))
    startup_delay_s = int(os.environ.get("INGEST_STARTUP_DELAY_S", "30"))

    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(
        _run_job,
        "interval",
        hours=interval_hours,
        id="ingest_periodic",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    _scheduler.add_job(
        _run_job,
        "date",
        run_date=datetime.now(timezone.utc) + timedelta(seconds=startup_delay_s),
        id="ingest_initial",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        "scheduler started (initial in %ss, every %sh)", startup_delay_s, interval_hours
    )


def stop() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
