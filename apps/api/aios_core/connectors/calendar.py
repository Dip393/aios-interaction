from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .base import (
    BaseConnector,
    ConnectorOperationError,
    ConnectorOperationRisk,
    ConnectorPermissionError,
    ConnectorResult,
    ConnectorStatus,
)


@dataclass
class CalendarEvent:
    """
    Standardized calendar event.
    """

    event_id: str

    title: str

    start: datetime
    end: datetime

    description: str = ""

    location: str | None = None

    attendees: list[str] = field(
        default_factory=list
    )

    reminder_minutes: int = 15

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: float = field(
        default_factory=time.time
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "title": self.title,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "description": self.description,
            "location": self.location,
            "attendees": list(
                self.attendees
            ),
            "reminder_minutes": (
                self.reminder_minutes
            ),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


class CalendarConnector(BaseConnector):
    """
    Calendar abstraction.

    Designed to later support Google Calendar, Outlook Calendar,
    CalDAV or another calendar provider.
    """

    name = "calendar"

    description = (
        "Calendar event and scheduling connector."
    )

    capabilities = (
        "list_events",
        "get_event",
        "create_event",
        "update_event",
        "delete_event",
    )

    requires_authentication = True

    def __init__(
        self,
        *,
        allow_write: bool = False,
    ) -> None:
        super().__init__()

        self.allow_write = allow_write

        self._events: dict[
            str,
            CalendarEvent,
        ] = {}

        self._lock = threading.RLock()

    def connect(
        self,
    ) -> ConnectorResult:
        self._set_status(
            ConnectorStatus.CONNECTED
        )

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation="connect",
            message=(
                "Calendar connector is ready "
                "in development mode."
            ),
            metadata={
                "real_calendar_connected": False,
            },
        )

    def list_events(
        self,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[CalendarEvent]:
        self.require_connected()

        with self._lock:
            events = list(
                self._events.values()
            )

        if start is not None:
            events = [
                event
                for event in events
                if event.end >= start
            ]

        if end is not None:
            events = [
                event
                for event in events
                if event.start <= end
            ]

        events.sort(
            key=lambda event: event.start
        )

        return events

    def get_event(
        self,
        event_id: str,
    ) -> CalendarEvent | None:
        self.require_connected()

        with self._lock:
            return self._events.get(event_id)

    def create_event(
        self,
        *,
        title: str,
        start: datetime,
        end: datetime,
        description: str = "",
        location: str | None = None,
        attendees: list[str] | None = None,
        reminder_minutes: int = 15,
        confirmed: bool = False,
    ) -> ConnectorResult:
        self.require_connected()

        if end <= start:
            raise ConnectorOperationError(
                "Event end must be after start."
            )

        if not self.allow_write:
            raise ConnectorPermissionError(
                "Calendar write operations are disabled."
            )

        if not confirmed:
            return ConnectorResult(
                success=False,
                connector=self.name,
                operation="create_event",
                message=(
                    "Creating a calendar event "
                    "requires confirmation."
                ),
                requires_confirmation=True,
                risk=ConnectorOperationRisk.MEDIUM,
            )

        event = CalendarEvent(
            event_id=str(uuid.uuid4()),
            title=title,
            start=start,
            end=end,
            description=description,
            location=location,
            attendees=list(attendees or []),
            reminder_minutes=max(
                0,
                reminder_minutes,
            ),
        )

        with self._lock:
            self._events[
                event.event_id
            ] = event

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation="create_event",
            data=event.to_dict(),
            risk=ConnectorOperationRisk.MEDIUM,
        )

    def update_event(
        self,
        event_id: str,
        *,
        confirmed: bool = False,
        **updates: Any,
    ) -> ConnectorResult:
        self.require_connected()

        if not self.allow_write:
            raise ConnectorPermissionError(
                "Calendar write operations are disabled."
            )

        if not confirmed:
            return ConnectorResult(
                success=False,
                connector=self.name,
                operation="update_event",
                message=(
                    "Updating a calendar event "
                    "requires confirmation."
                ),
                requires_confirmation=True,
                risk=ConnectorOperationRisk.MEDIUM,
            )

        with self._lock:
            event = self._events.get(event_id)

            if event is None:
                raise ConnectorOperationError(
                    f"Event not found: {event_id}"
                )

            allowed = {
                "title",
                "start",
                "end",
                "description",
                "location",
                "attendees",
                "reminder_minutes",
            }

            for key, value in updates.items():
                if key in allowed:
                    setattr(
                        event,
                        key,
                        value,
                    )

            if event.end <= event.start:
                raise ConnectorOperationError(
                    "Event end must be after start."
                )

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation="update_event",
            data=event.to_dict(),
            risk=ConnectorOperationRisk.MEDIUM,
        )

    def delete_event(
        self,
        event_id: str,
        *,
        confirmed: bool = False,
    ) -> ConnectorResult:
        self.require_connected()

        if not self.allow_write:
            raise ConnectorPermissionError(
                "Calendar write operations are disabled."
            )

        if not confirmed:
            return ConnectorResult(
                success=False,
                connector=self.name,
                operation="delete_event",
                message=(
                    "Deleting a calendar event "
                    "requires confirmation."
                ),
                requires_confirmation=True,
                risk=ConnectorOperationRisk.HIGH,
            )

        with self._lock:
            event = self._events.pop(
                event_id,
                None,
            )

        if event is None:
            raise ConnectorOperationError(
                f"Event not found: {event_id}"
            )

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation="delete_event",
            data=event.to_dict(),
            risk=ConnectorOperationRisk.HIGH,
        )

    def execute(
        self,
        operation: str,
        **kwargs: Any,
    ) -> ConnectorResult:
        operations = {
            "list": self.list_events,
            "get": self.get_event,
            "create": self.create_event,
            "update": self.update_event,
            "delete": self.delete_event,
        }

        handler = operations.get(operation)

        if handler is None:
            raise ConnectorOperationError(
                f"Unsupported calendar operation: "
                f"{operation}"
            )

        result = handler(**kwargs)

        if isinstance(result, ConnectorResult):
            return result

        if isinstance(result, CalendarEvent):
            data = result.to_dict()
        elif result is None:
            data = None
        else:
            data = [
                item.to_dict()
                for item in result
            ]

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation=operation,
            data=data,
        )