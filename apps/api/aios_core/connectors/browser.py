from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

from .base import (
    BaseConnector,
    ConnectorOperationError,
    ConnectorOperationRisk,
    ConnectorPermissionError,
    ConnectorResult,
    ConnectorStatus,
)


@dataclass
class BrowserPage:
    """
    Represents the current browser state.
    """

    url: str

    title: str = ""

    content: str = ""

    loaded_at: float = field(
        default_factory=time.time
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "loaded_at": self.loaded_at,
            "metadata": dict(self.metadata),
        }


class BrowserConnector(BaseConnector):
    """
    Browser automation abstraction.

    This layer deliberately does not directly control a real browser.

    A Playwright/Selenium/browser-service adapter can implement the
    actual browser operations later.
    """

    name = "browser"

    description = (
        "Controlled web browser interaction connector."
    )

    capabilities = (
        "navigate",
        "read_page",
        "search",
        "click",
        "type",
        "back",
        "forward",
    )

    requires_authentication = False

    def __init__(
        self,
        *,
        allow_navigation: bool = True,
        allow_interaction: bool = False,
    ) -> None:
        super().__init__()

        self.allow_navigation = allow_navigation
        self.allow_interaction = allow_interaction

        self._current_page: BrowserPage | None = None

        self._history: list[str] = []
        self._history_index = -1

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
                "Browser connector is ready "
                "in controlled mode."
            ),
            metadata={
                "real_browser_connected": False,
            },
        )

    @staticmethod
    def _validate_url(
        url: str,
    ) -> None:
        parsed = urlparse(url)

        if parsed.scheme not in {
            "http",
            "https",
        }:
            raise ConnectorOperationError(
                "Only HTTP and HTTPS URLs are allowed."
            )

        if not parsed.netloc:
            raise ConnectorOperationError(
                "Invalid URL."
            )

    def navigate(
        self,
        url: str,
        *,
        confirmed: bool = False,
    ) -> ConnectorResult:
        self.require_connected()

        if not self.allow_navigation:
            raise ConnectorPermissionError(
                "Browser navigation is disabled."
            )

        self._validate_url(url)

        if not confirmed:
            return ConnectorResult(
                success=False,
                connector=self.name,
                operation="navigate",
                message=(
                    "Browser navigation requires "
                    "confirmation in controlled mode."
                ),
                requires_confirmation=True,
                risk=ConnectorOperationRisk.MEDIUM,
            )

        page = BrowserPage(
            url=url,
            title="",
            content="",
            metadata={
                "loaded": False,
                "adapter": None,
            },
        )

        with self._lock:
            self._current_page = page

            # Remove forward history.
            if (
                self._history_index
                < len(self._history) - 1
            ):
                self._history = self._history[
                    : self._history_index + 1
                ]

            self._history.append(url)

            self._history_index = (
                len(self._history) - 1
            )

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation="navigate",
            data=page.to_dict(),
            risk=ConnectorOperationRisk.MEDIUM,
        )

    def current_page(
        self,
    ) -> BrowserPage | None:
        self.require_connected()

        with self._lock:
            return self._current_page

    def back(
        self,
        *,
        confirmed: bool = False,
    ) -> ConnectorResult:
        self.require_connected()

        if not confirmed:
            return ConnectorResult(
                success=False,
                connector=self.name,
                operation="back",
                message=(
                    "Browser navigation requires "
                    "confirmation."
                ),
                requires_confirmation=True,
                risk=ConnectorOperationRisk.LOW,
            )

        with self._lock:
            if self._history_index <= 0:
                raise ConnectorOperationError(
                    "No previous browser page."
                )

            self._history_index -= 1

            url = self._history[
                self._history_index
            ]

            self._current_page = BrowserPage(
                url=url
            )

            page = self._current_page

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation="back",
            data=page.to_dict(),
        )

    def forward(
        self,
        *,
        confirmed: bool = False,
    ) -> ConnectorResult:
        self.require_connected()

        if not confirmed:
            return ConnectorResult(
                success=False,
                connector=self.name,
                operation="forward",
                message=(
                    "Browser navigation requires "
                    "confirmation."
                ),
                requires_confirmation=True,
                risk=ConnectorOperationRisk.LOW,
            )

        with self._lock:
            if (
                self._history_index
                >= len(self._history) - 1
            ):
                raise ConnectorOperationError(
                    "No next browser page."
                )

            self._history_index += 1

            url = self._history[
                self._history_index
            ]

            self._current_page = BrowserPage(
                url=url
            )

            page = self._current_page

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation="forward",
            data=page.to_dict(),
        )

    def click(
        self,
        selector: str,
        *,
        confirmed: bool = False,
    ) -> ConnectorResult:
        self.require_connected()

        if not self.allow_interaction:
            raise ConnectorPermissionError(
                "Browser interaction is disabled."
            )

        if not confirmed:
            return ConnectorResult(
                success=False,
                connector=self.name,
                operation="click",
                message=(
                    "Browser interaction requires "
                    "confirmation."
                ),
                requires_confirmation=True,
                risk=ConnectorOperationRisk.MEDIUM,
            )

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation="click",
            data={
                "selector": selector,
                "executed": False,
                "adapter_required": True,
            },
            message=(
                "Click request accepted; a real browser "
                "adapter is required for execution."
            ),
        )

    def type_text(
        self,
        selector: str,
        text: str,
        *,
        confirmed: bool = False,
    ) -> ConnectorResult:
        self.require_connected()

        if not self.allow_interaction:
            raise ConnectorPermissionError(
                "Browser interaction is disabled."
            )

        if not confirmed:
            return ConnectorResult(
                success=False,
                connector=self.name,
                operation="type",
                message=(
                    "Browser typing requires "
                    "confirmation."
                ),
                requires_confirmation=True,
                risk=ConnectorOperationRisk.MEDIUM,
            )

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation="type",
            data={
                "selector": selector,
                "text": text,
                "executed": False,
                "adapter_required": True,
            },
        )

    def execute(
        self,
        operation: str,
        **kwargs: Any,
    ) -> ConnectorResult:
        operations = {
            "navigate": self.navigate,
            "current_page": (
                lambda: ConnectorResult(
                    success=True,
                    connector=self.name,
                    operation="current_page",
                    data=(
                        self.current_page().to_dict()
                        if self.current_page()
                        else None
                    ),
                )
            ),
            "back": self.back,
            "forward": self.forward,
            "click": self.click,
            "type": self.type_text,
        }

        handler = operations.get(operation)

        if handler is None:
            raise ConnectorOperationError(
                f"Unsupported browser operation: "
                f"{operation}"
            )

        return handler(**kwargs)