"""
AIOS Reminder Agent.

Handles reminders and alarm-like scheduling requests.

The base agent creates normalized reminder objects. Actual OS notifications,
push notifications, sound alarms or calendar notifications can later be
implemented by a scheduler/notification adapter.
"""

from __future__ import annotations

import re
import uuid
from typing import Any, Dict, Optional

from .base import Agent, AgentContext, AgentResult


class ReminderAgent(Agent):
    """Specialized agent for reminders and alarms."""

    name = "reminder_agent"

    description = (
        "Creates reminders and alarm requests for future scheduled actions."
    )

    capabilities = [
        "create_reminder",
        "create_alarm",
        "schedule_reminder",
        "cancel_reminder",
        "list_reminders",
    ]

    def _extract_time_hint(
        self,
        text: str,
    ) -> Optional[str]:
        """Extract simple natural-language time hints."""

        if not text:
            return None

        patterns = [
            r"\b\d{1,2}:\d{2}\s*(?:am|pm)?\b",
            r"\b\d{1,2}\s*(?:am|pm)\b",
            r"\bin\s+\d+\s+(?:minute|minutes|hour|hours|day|days)\b",
            r"\b(?:today|tomorrow|tonight|morning|evening)\b",
            r"\b(?:আজ|কাল|আগামীকাল|সকাল|রাত|বিকেল)\b",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if match:
                return match.group(0)

        return None

    async def run(
        self,
        context: AgentContext,
        params: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:

        params = params or {}

        operation = str(
            params.get(
                "operation",
                "create",
            )
        ).lower()

        raw_text = str(
            params.get(
                "text"
            )
            or context.input_text
            or ""
        ).strip()

        if operation in {
            "create",
            "schedule",
            "alarm",
            "remind",
        }:
            title = str(
                params.get(
                    "title"
                )
                or params.get(
                    "task"
                )
                or raw_text
                or "AIOS Reminder"
            ).strip()

            trigger = (
                params.get(
                    "trigger"
                )
                or params.get(
                    "time"
                )
                or params.get(
                    "date_time"
                )
                or self._extract_time_hint(
                    raw_text
                )
            )

            if not trigger:
                return self.needs_input(
                    context,
                    "When should I remind you?",
                    ["trigger"],
                )

            reminder_id = str(uuid.uuid4())

            reminder = {
                "id": reminder_id,
                "title": title,
                "trigger": trigger,
                "timezone": params.get(
                    "timezone",
                    context.timezone,
                ),
                "repeat": params.get(
                    "repeat"
                ),
                "notification_type": params.get(
                    "notification_type",
                    "system",
                ),
                "status": "scheduled",
            }

            context.set(
                "current_reminder",
                reminder,
            )

            return self.success(
                context,
                "Reminder prepared successfully.",
                {
                    "reminder": reminder,
                    "scheduler_required": True,
                },
                rollback_supported=True,
                rollback_token=reminder_id,
            )

        if operation == "cancel":
            reminder_id = params.get(
                "reminder_id"
            )

            if not reminder_id:
                return self.needs_input(
                    context,
                    "Which reminder should be cancelled?",
                    ["reminder_id"],
                )

            return self.success(
                context,
                "Reminder cancellation prepared.",
                {
                    "reminder_id": reminder_id,
                    "operation": "cancel",
                },
                rollback_supported=True,
                rollback_token=str(
                    reminder_id
                ),
            )

        if operation in {
            "list",
            "list_reminders",
        }:
            reminders = context.get(
                "reminders",
                [],
            )

            return self.success(
                context,
                "Reminder list retrieved.",
                {
                    "reminders": reminders,
                },
            )

        return self.failure(
            context,
            f"Unsupported reminder operation: {operation}",
            error="unsupported_operation",
        )