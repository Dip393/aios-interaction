from __future__ import annotations

import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ConnectorError(Exception):
    """Base exception for connector errors."""


class ConnectorNotConfiguredError(ConnectorError):
    """Raised when a connector has not been configured."""


class ConnectorPermissionError(ConnectorError):
    """Raised when an operation is not permitted."""


class ConnectorOperationError(ConnectorError):
    """Raised when a connector operation fails."""


class ConnectorStatus(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    DISABLED = "disabled"


class ConnectorOperationRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ConnectorResult:
    """
    Standardized result returned by connector operations.
    """

    success: bool

    connector: str
    operation: str

    data: Any = None
    message: str | None = None

    requires_confirmation: bool = False

    risk: ConnectorOperationRisk = (
        ConnectorOperationRisk.LOW
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    created_at: float = field(
        default_factory=time.time
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "connector": self.connector,
            "operation": self.operation,
            "data": self.data,
            "message": self.message,
            "requires_confirmation": (
                self.requires_confirmation
            ),
            "risk": self.risk.value,
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
        }


@dataclass
class ConnectorInfo:
    """
    Describes a connector registered with AIOS.
    """

    name: str
    description: str

    status: ConnectorStatus = (
        ConnectorStatus.DISCONNECTED
    )

    capabilities: list[str] = field(
        default_factory=list
    )

    requires_authentication: bool = False

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "capabilities": list(self.capabilities),
            "requires_authentication": (
                self.requires_authentication
            ),
            "metadata": dict(self.metadata),
        }


class BaseConnector(ABC):
    """
    Base class for every AIOS external connector.

    A connector is an adapter between AIOS and an external
    service/resource.

    Examples:

        Gmail
        Google Calendar
        Browser
        Filesystem
        Messaging
    """

    name = "base"
    description = "Base AIOS connector"

    capabilities: tuple[str, ...] = ()

    requires_authentication = False

    def __init__(self) -> None:
        self._status = ConnectorStatus.DISCONNECTED
        self._last_error: str | None = None
        self._lock = threading.RLock()

    @property
    def status(self) -> ConnectorStatus:
        with self._lock:
            return self._status

    @property
    def last_error(self) -> str | None:
        with self._lock:
            return self._last_error

    def info(self) -> ConnectorInfo:
        return ConnectorInfo(
            name=self.name,
            description=self.description,
            status=self.status,
            capabilities=list(
                self.capabilities
            ),
            requires_authentication=(
                self.requires_authentication
            ),
        )

    def _set_status(
        self,
        status: ConnectorStatus,
        *,
        error: str | None = None,
    ) -> None:
        with self._lock:
            self._status = status
            self._last_error = error

    def connect(self) -> ConnectorResult:
        """
        Connect/authenticate the connector.

        Base implementation is suitable for connectors that do
        not require an external connection.
        """

        self._set_status(
            ConnectorStatus.CONNECTED
        )

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation="connect",
            message=(
                f"{self.name} connector connected."
            ),
        )

    def disconnect(self) -> ConnectorResult:
        self._set_status(
            ConnectorStatus.DISCONNECTED
        )

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation="disconnect",
            message=(
                f"{self.name} connector disconnected."
            ),
        )

    def health_check(self) -> ConnectorResult:
        connected = (
            self.status
            == ConnectorStatus.CONNECTED
        )

        return ConnectorResult(
            success=connected,
            connector=self.name,
            operation="health_check",
            data={
                "status": self.status.value,
            },
            message=(
                "Connector is healthy."
                if connected
                else "Connector is not connected."
            ),
        )

    def require_connected(self) -> None:
        if self.status != ConnectorStatus.CONNECTED:
            raise ConnectorNotConfiguredError(
                f"Connector '{self.name}' is not connected."
            )

    @abstractmethod
    def execute(
        self,
        operation: str,
        **kwargs: Any,
    ) -> ConnectorResult:
        """
        Execute a connector operation.
        """
        raise NotImplementedError


class ConnectorRegistry:
    """
    Thread-safe registry for AIOS connectors.
    """

    def __init__(self) -> None:
        self._connectors: dict[
            str,
            BaseConnector,
        ] = {}

        self._lock = threading.RLock()

    def register(
        self,
        connector: BaseConnector,
        *,
        replace: bool = False,
    ) -> None:
        with self._lock:
            if (
                connector.name in self._connectors
                and not replace
            ):
                raise ConnectorError(
                    f"Connector already registered: "
                    f"{connector.name}"
                )

            self._connectors[
                connector.name
            ] = connector

    def unregister(
        self,
        name: str,
    ) -> bool:
        with self._lock:
            return (
                self._connectors.pop(
                    name,
                    None,
                )
                is not None
            )

    def get(
        self,
        name: str,
    ) -> BaseConnector | None:
        with self._lock:
            return self._connectors.get(name)

    def require(
        self,
        name: str,
    ) -> BaseConnector:
        connector = self.get(name)

        if connector is None:
            raise ConnectorError(
                f"Connector not found: {name}"
            )

        return connector

    def list(
        self,
    ) -> list[BaseConnector]:
        with self._lock:
            return list(
                self._connectors.values()
            )

    def names(self) -> list[str]:
        with self._lock:
            return list(
                self._connectors.keys()
            )

    def infos(self) -> list[ConnectorInfo]:
        return [
            connector.info()
            for connector in self.list()
        ]

    def clear(self) -> None:
        with self._lock:
            self._connectors.clear()

    def __contains__(
        self,
        name: str,
    ) -> bool:
        with self._lock:
            return name in self._connectors

    def __len__(self) -> int:
        with self._lock:
            return len(self._connectors)