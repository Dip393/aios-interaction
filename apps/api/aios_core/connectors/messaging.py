from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
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
class Message:
    """
    Generic messaging representation.

    The connector can later be adapted to WhatsApp, Telegram,
    SMS, Discord, Slack or another messaging platform.
    """

    message_id: str

    platform: str

    recipient: str

    content: str

    sender: str | None = None

    timestamp: float = field(
        default_factory=time.time
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "platform": self.platform,
            "recipient": self.recipient,
            "content": self.content,
            "sender": self.sender,
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata),
        }


class MessagingConnector(BaseConnector):
    """
    Generic messaging connector.

    Sending is disabled by default.

    Actual WhatsApp/Telegram/SMS integration should be implemented
    by provider-specific adapters.
    """

    name = "messaging"

    description = (
        "Generic external messaging connector."
    )

    capabilities = (
        "resolve_contact",
        "send_message",
        "list_messages",
    )

    requires_authentication = True

    def __init__(
        self,
        *,
        allow_send: bool = False,
    ) -> None:
        super().__init__()

        self.allow_send = allow_send

        self._contacts: dict[
            str,
            str,
        ] = {}

        self._messages: list[
            Message
        ] = []

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
                "Messaging connector is ready "
                "in development mode."
            ),
            metadata={
                "real_provider_connected": False,
            },
        )

    def add_contact(
        self,
        name: str,
        identifier: str,
    ) -> None:
        if not name.strip():
            raise ValueError(
                "Contact name cannot be empty."
            )

        if not identifier.strip():
            raise ValueError(
                "Contact identifier cannot be empty."
            )

        with self._lock:
            self._contacts[
                name.lower()
            ] = identifier

    def resolve_contact(
        self,
        name: str,
    ) -> str | None:
        self.require_connected()

        with self._lock:
            return self._contacts.get(
                name.lower()
            )

    def send(
        self,
        *,
        recipient: str,
        content: str,
        platform: str = "generic",
        confirmed: bool = False,
    ) -> ConnectorResult:
        self.require_connected()

        if not recipient.strip():
            raise ConnectorOperationError(
                "Recipient is required."
            )

        if not content.strip():
            raise ConnectorOperationError(
                "Message content cannot be empty."
            )

        if not self.allow_send:
            raise ConnectorPermissionError(
                "Messaging send operations are disabled."
            )

        if not confirmed:
            return ConnectorResult(
                success=False,
                connector=self.name,
                operation="send_message",
                message=(
                    "Sending a message requires "
                    "explicit confirmation."
                ),
                requires_confirmation=True,
                risk=ConnectorOperationRisk.HIGH,
            )

        message = Message(
            message_id=str(uuid.uuid4()),
            platform=platform,
            recipient=recipient,
            content=content,
        )

        with self._lock:
            self._messages.append(
                message
            )

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation="send_message",
            data=message.to_dict(),
            risk=ConnectorOperationRisk.HIGH,
        )

    def list_messages(
        self,
        *,
        limit: int = 50,
    ) -> list[Message]:
        self.require_connected()

        limit = max(1, min(limit, 200))

        with self._lock:
            return list(
                self._messages[-limit:]
            )

    def execute(
        self,
        operation: str,
        **kwargs: Any,
    ) -> ConnectorResult:
        operations = {
            "resolve_contact": self.resolve_contact,
            "send": self.send,
            "list": self.list_messages,
        }

        handler = operations.get(operation)

        if handler is None:
            raise ConnectorOperationError(
                f"Unsupported messaging operation: "
                f"{operation}"
            )

        result = handler(**kwargs)

        if isinstance(result, ConnectorResult):
            return result

        if isinstance(result, Message):
            data = result.to_dict()
        elif isinstance(result, list):
            data = [
                item.to_dict()
                for item in result
            ]
        else:
            data = result

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation=operation,
            data=data,
        )