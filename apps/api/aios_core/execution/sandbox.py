"""
AIOS Execution Sandbox.

The sandbox provides controlled boundaries for filesystem and command-like
operations.

Important:
This implementation does NOT execute arbitrary shell commands.

It provides path validation and operation restrictions that can later be
connected to a stronger OS/container sandbox.
"""

from __future__ import annotations

import os
import shlex
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Sequence


class SandboxViolation(Exception):
    """Raised when an operation violates sandbox rules."""


@dataclass
class SandboxConfig:
    """Configuration for the AIOS execution sandbox."""

    enabled: bool = True

    root_directory: str = "./aios_workspace"

    allow_file_read: bool = True

    allow_file_write: bool = True

    allow_file_delete: bool = False

    allow_file_move: bool = False

    allow_process_execution: bool = False

    allow_network: bool = False

    allowed_extensions: Optional[List[str]] = None

    blocked_extensions: List[str] = field(
        default_factory=lambda: [
            ".exe",
            ".dll",
            ".sys",
            ".bat",
            ".cmd",
            ".ps1",
            ".msi",
        ]
    )

    max_file_size_bytes: int = 10 * 1024 * 1024

    def normalized_root(self) -> Path:
        """Return absolute normalized sandbox root."""
        return Path(
            self.root_directory
        ).expanduser().resolve()


class Sandbox:
    """
    Controlled execution environment.

    The sandbox currently focuses on:
    - filesystem boundaries
    - path traversal prevention
    - file extension filtering
    - command execution policy

    It can later be replaced or extended with:
    - Docker
    - Firejail
    - subprocess isolation
    - WASM
    - microVM
    """

    def __init__(
        self,
        config: Optional[SandboxConfig] = None,
    ) -> None:

        self.config = (
            config
            or SandboxConfig()
        )

        self.root = (
            self.config.normalized_root()
        )

        if self.config.enabled:
            self.root.mkdir(
                parents=True,
                exist_ok=True,
            )

    def ensure_enabled(self) -> None:
        """Ensure sandbox is enabled."""

        if not self.config.enabled:
            raise SandboxViolation(
                "Sandbox is disabled."
            )

    def resolve_path(
        self,
        path: str,
    ) -> Path:
        """
        Resolve a path and ensure it stays inside sandbox root.
        """

        self.ensure_enabled()

        if not path:
            raise SandboxViolation(
                "A filesystem path is required."
            )

        candidate = Path(
            path
        ).expanduser()

        if not candidate.is_absolute():
            candidate = (
                self.root / candidate
            )

        resolved = candidate.resolve()

        try:
            resolved.relative_to(
                self.root
            )
        except ValueError as exc:
            raise SandboxViolation(
                "Path escapes the AIOS sandbox."
            ) from exc

        return resolved

    def validate_extension(
        self,
        path: Path,
    ) -> None:
        """Validate a file extension."""

        extension = (
            path.suffix.lower()
        )

        if extension in {
            item.lower()
            for item in self.config.blocked_extensions
        }:
            raise SandboxViolation(
                f"File extension '{extension}' is blocked."
            )

        if (
            self.config.allowed_extensions
            and extension
            not in {
                item.lower()
                for item in self.config.allowed_extensions
            }
        ):
            raise SandboxViolation(
                f"File extension '{extension}' is not allowed."
            )

    def validate_file_read(
        self,
        path: str,
    ) -> Path:
        """Validate a file-read operation."""

        self.ensure_enabled()

        if not self.config.allow_file_read:
            raise SandboxViolation(
                "File reading is disabled."
            )

        resolved = self.resolve_path(
            path
        )

        self.validate_extension(
            resolved
        )

        return resolved

    def validate_file_write(
        self,
        path: str,
        size_bytes: int = 0,
    ) -> Path:
        """Validate a file-write operation."""

        self.ensure_enabled()

        if not self.config.allow_file_write:
            raise SandboxViolation(
                "File writing is disabled."
            )

        if (
            size_bytes
            > self.config.max_file_size_bytes
        ):
            raise SandboxViolation(
                "File exceeds sandbox size limit."
            )

        resolved = self.resolve_path(
            path
        )

        self.validate_extension(
            resolved
        )

        return resolved

    def validate_file_delete(
        self,
        path: str,
    ) -> Path:
        """Validate a file-delete operation."""

        self.ensure_enabled()

        if not self.config.allow_file_delete:
            raise SandboxViolation(
                "File deletion is disabled."
            )

        resolved = self.resolve_path(
            path
        )

        self.validate_extension(
            resolved
        )

        return resolved

    def validate_file_move(
        self,
        source: str,
        destination: str,
    ) -> tuple[Path, Path]:
        """Validate a file move operation."""

        self.ensure_enabled()

        if not self.config.allow_file_move:
            raise SandboxViolation(
                "File moving is disabled."
            )

        source_path = self.resolve_path(
            source
        )

        destination_path = self.resolve_path(
            destination
        )

        self.validate_extension(
            source_path
        )

        self.validate_extension(
            destination_path
        )

        return (
            source_path,
            destination_path,
        )

    def validate_command(
        self,
        command: str,
        allowed_commands: Optional[
            Sequence[str]
        ] = None,
    ) -> List[str]:
        """
        Validate a command without executing it.

        This function intentionally only parses and validates the command.
        """

        self.ensure_enabled()

        if not self.config.allow_process_execution:
            raise SandboxViolation(
                "Process execution is disabled."
            )

        if not command.strip():
            raise SandboxViolation(
                "Command cannot be empty."
            )

        parts = shlex.split(
            command
        )

        if not parts:
            raise SandboxViolation(
                "Invalid command."
            )

        executable = os.path.basename(
            parts[0]
        ).lower()

        if allowed_commands:
            allowed = {
                os.path.basename(
                    item
                ).lower()
                for item in allowed_commands
            }

            if executable not in allowed:
                raise SandboxViolation(
                    f"Command '{executable}' is not allowed."
                )

        return parts

    def is_inside(
        self,
        path: str,
    ) -> bool:
        """Check whether a path is inside the sandbox."""

        try:
            self.resolve_path(
                path
            )
            return True
        except SandboxViolation:
            return False

    def info(self) -> dict:
        """Return sandbox configuration information."""

        return {
            "enabled": self.config.enabled,
            "root_directory": str(
                self.root
            ),
            "allow_file_read": (
                self.config.allow_file_read
            ),
            "allow_file_write": (
                self.config.allow_file_write
            ),
            "allow_file_delete": (
                self.config.allow_file_delete
            ),
            "allow_file_move": (
                self.config.allow_file_move
            ),
            "allow_process_execution": (
                self.config.allow_process_execution
            ),
            "allow_network": (
                self.config.allow_network
            ),
            "max_file_size_bytes": (
                self.config.max_file_size_bytes
            ),
        }