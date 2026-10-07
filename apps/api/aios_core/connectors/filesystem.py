from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from .base import (
    BaseConnector,
    ConnectorOperationError,
    ConnectorOperationRisk,
    ConnectorPermissionError,
    ConnectorResult,
    ConnectorStatus,
)


class FilesystemConnector(BaseConnector):
    """
    Controlled local filesystem connector.

    By default the connector operates in read-only mode.

    A sandbox/root directory can be provided to prevent AIOS from
    accidentally accessing arbitrary parts of the host filesystem.
    """

    name = "filesystem"

    description = (
        "Controlled local filesystem connector."
    )

    capabilities = (
        "list",
        "read",
        "exists",
        "write",
        "create_directory",
        "delete",
    )

    requires_authentication = False

    def __init__(
        self,
        *,
        root: str | None = None,
        allow_write: bool = False,
        allow_delete: bool = False,
    ) -> None:
        super().__init__()

        self.root = (
            Path(root).expanduser().resolve()
            if root
            else None
        )

        self.allow_write = allow_write
        self.allow_delete = allow_delete

        self._lock = threading.RLock()

    def connect(
        self,
    ) -> ConnectorResult:
        if self.root is not None:
            self.root.mkdir(
                parents=True,
                exist_ok=True,
            )

        self._set_status(
            ConnectorStatus.CONNECTED
        )

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation="connect",
            data={
                "root": (
                    str(self.root)
                    if self.root
                    else None
                ),
                "read_only": not self.allow_write,
            },
        )

    def _resolve(
        self,
        path: str,
    ) -> Path:
        candidate = Path(path).expanduser()

        if self.root is not None:
            if not candidate.is_absolute():
                candidate = (
                    self.root / candidate
                )

            candidate = candidate.resolve()

            try:
                candidate.relative_to(
                    self.root
                )
            except ValueError as exc:
                raise ConnectorPermissionError(
                    "Path escapes filesystem sandbox."
                ) from exc

            return candidate

        return candidate.resolve()

    def exists(
        self,
        path: str,
    ) -> bool:
        self.require_connected()

        return self._resolve(path).exists()

    def list_directory(
        self,
        path: str = ".",
    ) -> list[dict[str, Any]]:
        self.require_connected()

        target = self._resolve(path)

        if not target.exists():
            raise ConnectorOperationError(
                f"Path does not exist: {path}"
            )

        if not target.is_dir():
            raise ConnectorOperationError(
                f"Path is not a directory: {path}"
            )

        entries = []

        for item in sorted(
            target.iterdir(),
            key=lambda p: p.name.lower(),
        ):
            entries.append(
                {
                    "name": item.name,
                    "path": str(item),
                    "type": (
                        "directory"
                        if item.is_dir()
                        else "file"
                    ),
                    "size": (
                        item.stat().st_size
                        if item.is_file()
                        else None
                    ),
                }
            )

        return entries

    def read(
        self,
        path: str,
        *,
        encoding: str = "utf-8",
    ) -> str:
        self.require_connected()

        target = self._resolve(path)

        if not target.exists():
            raise ConnectorOperationError(
                f"File does not exist: {path}"
            )

        if not target.is_file():
            raise ConnectorOperationError(
                f"Path is not a file: {path}"
            )

        try:
            return target.read_text(
                encoding=encoding
            )
        except OSError as exc:
            raise ConnectorOperationError(
                f"Unable to read file: {path}"
            ) from exc

    def write(
        self,
        path: str,
        content: str,
        *,
        encoding: str = "utf-8",
        confirmed: bool = False,
    ) -> ConnectorResult:
        self.require_connected()

        if not self.allow_write:
            raise ConnectorPermissionError(
                "Filesystem write operations are disabled."
            )

        if not confirmed:
            return ConnectorResult(
                success=False,
                connector=self.name,
                operation="write",
                message=(
                    "Filesystem writes require "
                    "confirmation."
                ),
                requires_confirmation=True,
                risk=ConnectorOperationRisk.MEDIUM,
            )

        target = self._resolve(path)

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            target.write_text(
                content,
                encoding=encoding,
            )
        except OSError as exc:
            raise ConnectorOperationError(
                f"Unable to write file: {path}"
            ) from exc

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation="write",
            data={
                "path": str(target),
                "size": target.stat().st_size,
            },
            risk=ConnectorOperationRisk.MEDIUM,
        )

    def create_directory(
        self,
        path: str,
        *,
        confirmed: bool = False,
    ) -> ConnectorResult:
        self.require_connected()

        if not self.allow_write:
            raise ConnectorPermissionError(
                "Filesystem write operations are disabled."
            )

        if not confirmed:
            return ConnectorResult(
                success=False,
                connector=self.name,
                operation="create_directory",
                message=(
                    "Creating directories requires "
                    "confirmation."
                ),
                requires_confirmation=True,
                risk=ConnectorOperationRisk.MEDIUM,
            )

        target = self._resolve(path)

        target.mkdir(
            parents=True,
            exist_ok=True,
        )

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation="create_directory",
            data={
                "path": str(target),
            },
            risk=ConnectorOperationRisk.MEDIUM,
        )

    def delete(
        self,
        path: str,
        *,
        confirmed: bool = False,
    ) -> ConnectorResult:
        self.require_connected()

        if not self.allow_delete:
            raise ConnectorPermissionError(
                "Filesystem delete operations are disabled."
            )

        if not confirmed:
            return ConnectorResult(
                success=False,
                connector=self.name,
                operation="delete",
                message=(
                    "Filesystem deletion requires "
                    "explicit confirmation."
                ),
                requires_confirmation=True,
                risk=ConnectorOperationRisk.CRITICAL,
            )

        target = self._resolve(path)

        if not target.exists():
            raise ConnectorOperationError(
                f"Path does not exist: {path}"
            )

        if target.is_dir():
            raise ConnectorOperationError(
                "Recursive directory deletion is "
                "not supported by the safe connector."
            )

        target.unlink()

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation="delete",
            data={
                "path": str(target),
            },
            risk=ConnectorOperationRisk.CRITICAL,
        )

    def execute(
        self,
        operation: str,
        **kwargs: Any,
    ) -> ConnectorResult:
        operations = {
            "exists": self.exists,
            "list": self.list_directory,
            "read": self.read,
            "write": self.write,
            "create_directory": self.create_directory,
            "delete": self.delete,
        }

        handler = operations.get(operation)

        if handler is None:
            raise ConnectorOperationError(
                f"Unsupported filesystem operation: "
                f"{operation}"
            )

        result = handler(**kwargs)

        if isinstance(result, ConnectorResult):
            return result

        return ConnectorResult(
            success=True,
            connector=self.name,
            operation=operation,
            data=result,
        )