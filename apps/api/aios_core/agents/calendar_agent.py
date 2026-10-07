"""
AIOS Calendar Agent.

Responsible for preparing calendar events.

The default implementation does not contact Google Calendar or another
calendar provider. It creates a normalized event payload which can later
be consumed by a calendar connector.
"""

from __future__ import annotations

import re
import uuid
from typing import Any, Dict, Optional

from .base import Agent, AgentContext, AgentResult


class CalendarAgent(Agent):
    """Specialized agent for calendar and meeting operations."""

    name = "calendar_agent"

    description = (
        "Creates and prepares meetings, appointments and calendar events."
    )

    capabilities = [
        "create_event",
        "schedule_meeting",
        "prepare_event",
        "parse_time_hint",
        "calendar_preview",
    ]

    def _extract_time_hint(self, text: str) -> Optional[str]:
        """Extract common time expressions from natural language."""

        if not text:
            return None

        patterns = [
            r"\b\d{1,2}:\d{2}\s*(?:am|pm)?\b",
            r"\b\d{1,2}\s*(?:am|pm)\b",
            r"\b(?:today|tomorrow|tonight|morning|afternoon|evening)\b",
            r"\b(?:আজ|আগামীকাল|কাল|সকাল|দুপুর|বিকেল|রাত)\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)

        return None

    def _extract_title(self, text: str) -> str:
        """Try to infer a short event title."""

        if not text:
            return "AIOS Meeting"

        match = re.search(
            r"(?:meeting|appointment|event|মিটিং|সভা)\s*(?:with|সঙ্গে|এর সাথে)?\s*(.+)?",
            text,
            re.IGNORECASE,
        )

        if match and match.group(1):
            title = match.group(1).strip()

            title = re.sub(
                r"\b(?:today|tomorrow|at|on|আজ|কাল|আগামীকাল)\b.*$",
                "",
                title,
                flags=re.IGNORECASE,
            )

            if title:
                return title[:120]

        return "AIOS Meeting"

    async def run(
        self,
        context: AgentContext,
        params: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:

        params = params or {}

        operation = str(
            params.get("operation", "create")
        ).lower()

        raw_text = str(
            params.get("text")
            or context.input_text
            or ""
        ).strip()

        title = (
            params.get("title")
            or params.get("name")
            or self._extract_title(raw_text)
        )

        start = (
            params.get("start")
            or params.get("date_time")
            or params.get("datetime")
            or self._extract_time_hint(raw_text)
        )

        if operation not in {
            "create",
            "schedule",
            "prepare",
            "preview",
        }:
            return self.failure(
                context,
                f"Unsupported calendar operation: {operation}",
                error="unsupported_operation",
            )

        if not start:
            return self.needs_input(
                context,
                "When should the event or meeting happen?",
                ["start"],
            )

        event_id = str(uuid.uuid4())

        event = {
            "id": event_id,
            "title": title,
            "start": start,
            "end": params.get("end"),
            "timezone": params.get(
                "timezone",
                context.timezone,
            ),
            "location": params.get("location"),
            "description": params.get(
                "description",
                raw_text,
            ),
            "attendees": params.get(
                "attendees",
                [],
            ),
            "status": "prepared",
            "calendar_provider": "connector_required",
        }

        context.set("current_calendar_event", event)

        return self.success(
            context,
            "Calendar event prepared successfully.",
            {
                "event": event,
                "ready_for_calendar_connector": True,
            },
            rollback_supported=True,
            rollback_token=event_id,
        )