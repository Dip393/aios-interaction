"""
AIOS Scheduler.

Background scheduler responsible for time-based AIOS events such as:

    - Reminders
    - Scheduled tasks
    - Future actions
    - Recurring events

The scheduler itself does NOT execute arbitrary external actions.
It only detects due records and marks/dispatches them safely.

Designed to run inside the FastAPI application lifespan.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable, Optional

from .db import execute, now, rows


# ============================================================================
# Configuration
# ============================================================================

DEFAULT_INTERVAL = 15

logger = logging.getLogger(
    "aios.scheduler"
)


# ============================================================================
# Types
# ============================================================================

ReminderCallback = Callable[
    [dict[str, Any]],
    Optional[Awaitable[Any]],
]


# ============================================================================
# Scheduler
# ============================================================================

class AIOSScheduler:
    """
    Persistent AIOS background scheduler.

    The scheduler periodically checks the database for due reminders and
    dispatches them to an optional callback.

    Example:

        scheduler = AIOSScheduler()

        await scheduler.run()
    """

    def __init__(
        self,
        interval: int = DEFAULT_INTERVAL,
        callback: Optional[
            ReminderCallback
        ] = None,
    ) -> None:
        self.interval = max(
            1,
            int(interval),
        )

        self.callback = callback

        self._running = False
        self._task: Optional[
            asyncio.Task[Any]
        ] = None

        self._triggered_count = 0
        self._error_count = 0

    # ---------------------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------------------

    async def start(self) -> None:
        """
        Start the scheduler as a background asyncio task.

        Calling start() multiple times is safe.
        """

        if self._running:
            return

        self._running = True

        self._task = asyncio.create_task(
            self.run(),
            name="aios-scheduler",
        )

        logger.info(
            "AIOS scheduler started."
        )

    async def stop(self) -> None:
        """
        Stop the scheduler gracefully.
        """

        self._running = False

        task = self._task

        if task is None:
            return

        self._task = None

        if task.done():
            return

        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        logger.info(
            "AIOS scheduler stopped."
        )

    async def run(self) -> None:
        """
        Main scheduler loop.

        This method can be used directly by the FastAPI lifespan if desired.
        """

        self._running = True

        try:
            while self._running:
                try:
                    await self.tick()
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    self._error_count += 1

                    logger.exception(
                        "Scheduler tick failed: %s",
                        exc,
                    )

                await asyncio.sleep(
                    self.interval
                )

        except asyncio.CancelledError:
            logger.debug(
                "Scheduler task cancelled."
            )
            raise

        finally:
            self._running = False

    # ---------------------------------------------------------------------
    # Tick
    # ---------------------------------------------------------------------

    async def tick(self) -> int:
        """
        Process all currently due reminders.

        Returns the number of reminders triggered.
        """

        due_reminders = rows(
            """
            SELECT *
            FROM reminders
            WHERE status = 'pending'
              AND due_at IS NOT NULL
              AND due_at <= ?
            ORDER BY due_at ASC, id ASC
            """,
            (now(),),
        )

        triggered = 0

        for reminder in due_reminders:
            try:
                if await self._trigger_reminder(
                    reminder
                ):
                    triggered += 1

            except asyncio.CancelledError:
                raise

            except Exception as exc:
                self._error_count += 1

                logger.exception(
                    "Failed to process reminder %s: %s",
                    reminder.get("id"),
                    exc,
                )

        return triggered

    # ---------------------------------------------------------------------
    # Reminder processing
    # ---------------------------------------------------------------------

    async def _trigger_reminder(
        self,
        reminder: dict[str, Any],
    ) -> bool:
        """
        Atomically transition a pending reminder to triggered.

        This prevents the same reminder from being processed repeatedly
        on subsequent scheduler ticks.
        """

        reminder_id = reminder.get(
            "id"
        )

        if reminder_id is None:
            logger.warning(
                "Skipping reminder without ID."
            )
            return False

        # Conditional UPDATE is important.
        #
        # If another scheduler instance already processed this reminder,
        # rowcount should be zero and we do not dispatch it again.
        result = execute(
            """
            UPDATE reminders
            SET
                status = 'triggered',
                updated_at = ?
            WHERE id = ?
              AND status = 'pending'
            """,
            (
                now(),
                reminder_id,
            ),
        )

        # db.execute normally returns affected-row count. Some older
        # implementations may return another integer-like value, so keep
        # this defensive.
        try:
            affected = int(
                result
            )
        except (
            TypeError,
            ValueError,
        ):
            affected = 1

        if affected <= 0:
            return False

        self._triggered_count += 1

        title = str(
            reminder.get(
                "title",
                "Untitled reminder",
            )
        )

        logger.info(
            "[AIOS REMINDER] %s",
            title,
        )

        # Optional application-level callback.
        if self.callback is not None:
            callback_result = self.callback(
                reminder
            )

            if asyncio.iscoroutine(
                callback_result
            ):
                await callback_result

        return True

    # ---------------------------------------------------------------------
    # Manual processing
    # ---------------------------------------------------------------------

    async def trigger_reminder(
        self,
        reminder_id: int | str,
    ) -> bool:
        """
        Manually trigger one pending reminder.

        Useful for tests and administrative controls.
        """

        reminder_rows = rows(
            """
            SELECT *
            FROM reminders
            WHERE id = ?
              AND status = 'pending'
            LIMIT 1
            """,
            (reminder_id,),
        )

        if not reminder_rows:
            return False

        return await self._trigger_reminder(
            reminder_rows[0]
        )

    # ---------------------------------------------------------------------
    # Status
    # ---------------------------------------------------------------------

    @property
    def running(self) -> bool:
        """Return whether the scheduler is currently running."""

        return self._running

    def status(self) -> dict[str, Any]:
        """
        Return scheduler runtime statistics.
        """

        return {
            "running": self._running,
            "interval_seconds": self.interval,
            "triggered_count": self._triggered_count,
            "error_count": self._error_count,
        }


# ============================================================================
# Default scheduler instance
# ============================================================================

_scheduler = AIOSScheduler()


# ============================================================================
# Public compatibility function
# ============================================================================

async def scheduler_loop() -> None:
    """
    Backward-compatible scheduler entry point.

    Existing main.py code can continue to use:

        scheduler_task = asyncio.create_task(
            scheduler_loop()
        )

    The function runs until cancelled.
    """

    await _scheduler.run()


# ============================================================================
# Convenience API
# ============================================================================

def get_scheduler() -> AIOSScheduler:
    """
    Return the shared AIOS scheduler instance.
    """

    return _scheduler


async def start_scheduler() -> None:
    """
    Start the shared scheduler.
    """

    await _scheduler.start()


async def stop_scheduler() -> None:
    """
    Stop the shared scheduler.
    """

    await _scheduler.stop()


async def process_scheduler_tick() -> int:
    """
    Execute one scheduler cycle immediately.

    Useful for tests and manual administrative operations.
    """

    return await _scheduler.tick()


def scheduler_status() -> dict[str, Any]:
    """
    Return shared scheduler status.
    """

    return _scheduler.status()


__all__ = [
    "AIOSScheduler",
    "scheduler_loop",
    "get_scheduler",
    "start_scheduler",
    "stop_scheduler",
    "process_scheduler_tick",
    "scheduler_status",
]