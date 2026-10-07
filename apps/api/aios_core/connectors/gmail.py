from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

from .base import (
    BaseConnector,
    ConnectorOperationRisk,
    ConnectorOperationError,
    ConnectorPermissionError,
    ConnectorResult,
    ConnectorStatus,
)


@dataclass
class EmailMessage:
    """
    Standardized email representation.
    """

    message_id: str

    sender: str
    recipients: list[str]

    subject: str
    body: str

    cc: list[str] = field(
        default_factory=list
    )

    bcc: list[str] = field(
        default_factory=list
    )

    timestamp: float = field(
        default_factory=time.time
    )

    is_read: bool = False

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "sender": self.sender,
            "recipients": list(
                self.recipients
            ),
            "subject": self.subject,
            "body": self.body,
            "cc": list(self.cc),
            "bcc": list(self.bcc),
            "timestamp": self.timestamp,
            "is_read": self.is_read,
            "metadata": dict(self.metadata),
        }


class GmailConnector(BaseConnector):
    """
    Gmail connector abstraction.

    This implementation intentionally does not depend on the
    Google API package.

    A production Google OAuth/Gmail API adapter can later be
    attached without changing the AIOS connector interface.
    """

    name = "gmail"

    description = (
        "Gmail email and mailbox connector."
    )

    capabilities = (
        "read_email",
        "search_email",
        "draft_email",
        "send_email",
    )

    requires_authentication = True

    def __init__(
        self,
        *,
        allow_send: bool = False,
    ) -> None:
        super().__init__()

        self.allow_send = allow_send

        self._messages: dict[
            str,
            EmailMessage,
        ] = {}

        self._drafts: dict[
            str,
            EmailMessage,
        ] = {}

        self._lock = threading.RLock()

    def connect(
        self,
    ) -> ConnectorResult:
        """
        Development connection.

        Real OAuth authentication should be implemented by a
        production Gmail adapter.
        """

        self._set_status(
            ConnectorStatus.CONNECTED
        )

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation="connect",
            message=(
                "Gmail connector is ready in "
                "development mode."
            ),
            metadata={
                "authentication_required": True,
                "real_api_connected": False,
            },
        )

    def add_test_message(
        self,
        message: EmailMessage,
    ) -> None:
        """
        Add an email to the local development mailbox.
        """

        with self._lock:
            self._messages[
                message.message_id
            ] = message

    def list_messages(
        self,
        *,
        limit: int = 20,
        unread_only: bool = False,
    ) -> list[EmailMessage]:
        self.require_connected()

        limit = max(1, min(limit, 100))

        with self._lock:
            messages = list(
                self._messages.values()
            )

        if unread_only:
            messages = [
                message
                for message in messages
                if not message.is_read
            ]

        messages.sort(
            key=lambda item: item.timestamp,
            reverse=True,
        )

        return messages[:limit]

    def search_messages(
        self,
        query: str,
        *,
        limit: int = 20,
    ) -> list[EmailMessage]:
        self.require_connected()

        if not query.strip():
            return []

        query_lower = query.lower()

        with self._lock:
            messages = list(
                self._messages.values()
            )

        matches = [
            message
            for message in messages
            if (
                query_lower
                in message.subject.lower()
                or query_lower
                in message.body.lower()
                or query_lower
                in message.sender.lower()
            )
        ]

        matches.sort(
            key=lambda item: item.timestamp,
            reverse=True,
        )

        return matches[: max(1, min(limit, 100))]

    def get_message(
        self,
        message_id: str,
    ) -> EmailMessage | None:
        self.require_connected()

        with self._lock:
            return self._messages.get(
                message_id
            )

    def mark_read(
        self,
        message_id: str,
    ) -> ConnectorResult:
        self.require_connected()

        with self._lock:
            message = self._messages.get(
                message_id
            )

            if message is None:
                raise ConnectorOperationError(
                    f"Email not found: {message_id}"
                )

            message.is_read = True

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation="mark_read",
            data=message.to_dict(),
        )

    def draft(
        self,
        *,
        message_id: str,
        sender: str,
        recipients: list[str],
        subject: str,
        body: str,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
    ) -> ConnectorResult:
        self.require_connected()

        message = EmailMessage(
            message_id=message_id,
            sender=sender,
            recipients=list(recipients),
            subject=subject,
            body=body,
            cc=list(cc or []),
            bcc=list(bcc or []),
        )

        with self._lock:
            self._drafts[
                message_id
            ] = message

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation="draft_email",
            data=message.to_dict(),
            message="Email draft created.",
            risk=ConnectorOperationRisk.LOW,
        )

    def send(
        self,
        *,
        sender: str,
        recipients: list[str],
        subject: str,
        body: str,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        confirmed: bool = False,
    ) -> ConnectorResult:
        self.require_connected()

        if not recipients:
            raise ConnectorOperationError(
                "At least one recipient is required."
            )

        if not self.allow_send:
            raise ConnectorPermissionError(
                "Gmail sending is disabled."
            )

        if not confirmed:
            return ConnectorResult(
                success=False,
                connector=self.name,
                operation="send_email",
                message=(
                    "Email sending requires "
                    "explicit confirmation."
                ),
                requires_confirmation=True,
                risk=ConnectorOperationRisk.HIGH,
            )

        message_id = (
            f"sent-{int(time.time() * 1000)}"
        )

        message = EmailMessage(
            message_id=message_id,
            sender=sender,
            recipients=list(recipients),
            subject=subject,
            body=body,
            cc=list(cc or []),
            bcc=list(bcc or []),
            is_read=True,
        )

        with self._lock:
            self._messages[
                message_id
            ] = message

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation="send_email",
            data=message.to_dict(),
            message="Email sent.",
            risk=ConnectorOperationRisk.HIGH,
        )

    def execute(
        self,
        operation: str,
        **kwargs: Any,
    ) -> ConnectorResult:
        operations = {
            "list": self.list_messages,
            "search": self.search_messages,
            "mark_read": self.mark_read,
            "draft": self.draft,
            "send": self.send,
        }

        handler = operations.get(operation)

        if handler is None:
            raise ConnectorOperationError(
                f"Unsupported Gmail operation: "
                f"{operation}"
            )

        result = handler(**kwargs)

        if isinstance(result, ConnectorResult):
            return result

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation=operation,
            data=[
                item.to_dict()
                for item in result
            ],
        )