"""
The Loop — Pipeline Scheduler
APScheduler-based scheduling for pipeline triggers and publishing.
"""

import logging
from datetime import datetime, timedelta
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class PipelineScheduler:
    """
    Manages scheduled pipeline runs and content publishing times.
    Uses APScheduler for cron-based triggers.
    """

    def __init__(self):
        self._scheduler = None
        self._jobs = {}

    def _get_scheduler(self):
        """Lazy-load APScheduler."""
        if self._scheduler is None:
            try:
                from apscheduler.schedulers.asyncio import AsyncIOScheduler
                from apscheduler.triggers.cron import CronTrigger
                self._scheduler = AsyncIOScheduler()
            except ImportError:
                logger.error("APScheduler not installed. Install with: pip install apscheduler")
                return None
        return self._scheduler

    def start(self):
        """Start the scheduler."""
        scheduler = self._get_scheduler()
        if scheduler and not scheduler.running:
            scheduler.start()
            logger.info("[Scheduler] Started")

    def stop(self):
        """Stop the scheduler."""
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown()
            logger.info("[Scheduler] Stopped")

    def schedule_pipeline_run(
        self,
        callback: Callable,
        hour: int = 6,
        minute: int = 0,
        timezone: str = "UTC",
        job_id: str = "daily_pipeline",
    ):
        """
        Schedule a daily pipeline run.

        Args:
            callback: Async function to call when triggered
            hour: Hour to run (24h format)
            minute: Minute to run
            timezone: Timezone string
            job_id: Unique job identifier
        """
        scheduler = self._get_scheduler()
        if not scheduler:
            logger.error("[Scheduler] Cannot schedule — APScheduler not available")
            return

        try:
            from apscheduler.triggers.cron import CronTrigger

            trigger = CronTrigger(hour=hour, minute=minute, timezone=timezone)
            job = scheduler.add_job(
                callback,
                trigger=trigger,
                id=job_id,
                replace_existing=True,
                name=f"Pipeline Run ({hour:02d}:{minute:02d} {timezone})",
            )
            self._jobs[job_id] = job
            logger.info(f"[Scheduler] Pipeline scheduled: {hour:02d}:{minute:02d} {timezone}")

        except Exception as e:
            logger.error(f"[Scheduler] Failed to schedule pipeline: {e}")

    def schedule_publish(
        self,
        callback: Callable,
        publish_time: datetime,
        job_id: str = "scheduled_publish",
        **kwargs,
    ):
        """
        Schedule a one-time content publish at a specific time.

        Args:
            callback: Async function to call for publishing
            publish_time: When to publish
            job_id: Unique job identifier
        """
        scheduler = self._get_scheduler()
        if not scheduler:
            return

        try:
            from apscheduler.triggers.date import DateTrigger

            trigger = DateTrigger(run_date=publish_time)
            job = scheduler.add_job(
                callback,
                trigger=trigger,
                id=job_id,
                replace_existing=True,
                name=f"Publish at {publish_time.isoformat()}",
                kwargs=kwargs,
            )
            self._jobs[job_id] = job
            logger.info(f"[Scheduler] Publish scheduled for {publish_time.isoformat()}")

        except Exception as e:
            logger.error(f"[Scheduler] Failed to schedule publish: {e}")

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a scheduled job."""
        scheduler = self._get_scheduler()
        if scheduler:
            try:
                scheduler.remove_job(job_id)
                self._jobs.pop(job_id, None)
                logger.info(f"[Scheduler] Cancelled job: {job_id}")
                return True
            except Exception:
                return False
        return False

    def get_scheduled_jobs(self) -> list[dict]:
        """Get all currently scheduled jobs."""
        scheduler = self._get_scheduler()
        if not scheduler:
            return []

        jobs = []
        for job in scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
            })
        return jobs

    @staticmethod
    def get_optimal_times(platform: str, analytics: dict | None = None) -> list[dict]:
        """
        Get optimal posting times for a platform.
        Uses analytics data if available, otherwise returns defaults.
        """
        # Default optimal times (EST) based on industry research
        defaults = {
            "instagram": [
                {"time": "06:00", "label": "Early Morning", "reason": "Pre-work scroll"},
                {"time": "12:00", "label": "Lunch Break", "reason": "Midday engagement peak"},
                {"time": "19:00", "label": "Evening Wind-down", "reason": "Highest engagement window"},
            ],
            "tiktok": [
                {"time": "07:00", "label": "Morning Commute", "reason": "High discovery rate"},
                {"time": "12:00", "label": "Lunch Break", "reason": "FYP browsing peak"},
                {"time": "22:00", "label": "Late Night", "reason": "Extended scroll sessions"},
            ],
            "youtube": [
                {"time": "14:00", "label": "Afternoon", "reason": "Shorts discovery peak"},
                {"time": "17:00", "label": "After Work", "reason": "Subscriptions check"},
            ],
            "twitter": [
                {"time": "08:00", "label": "Morning", "reason": "News and threads"},
                {"time": "12:00", "label": "Lunch", "reason": "Engagement peak"},
                {"time": "17:00", "label": "End of Day", "reason": "Hot takes and discussions"},
            ],
            "linkedin": [
                {"time": "07:30", "label": "Pre-Work", "reason": "Professional browsing"},
                {"time": "12:00", "label": "Lunch", "reason": "Industry discussion"},
            ],
        }

        # If analytics data is available, use best performing time from data
        if analytics and analytics.get("aggregate_metrics", {}).get("best_performing_time"):
            best_time = analytics["aggregate_metrics"]["best_performing_time"]
            return [
                {"time": best_time, "label": "Data-Optimized", "reason": "Based on your analytics"},
                *defaults.get(platform, defaults["instagram"])[:1],
            ]

        return defaults.get(platform, defaults["instagram"])
