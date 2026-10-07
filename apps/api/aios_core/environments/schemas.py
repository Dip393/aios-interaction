"""
AIOS Environment Schemas.

Defines the core data structures used by the environment subsystem.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


def utc_now() -> str:
    """Return current UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


class EnvironmentType(str, Enum):
    """Standard AIOS environment types."""

    GENERAL = "general"

    WRITING = "writing"

    DOCUMENT = "document"

    EMAIL = "email"

    CALENDAR = "calendar"

    CODE = "code"

    PROJECT = "project"

    FILE = "file"

    SEARCH = "search"

    RESEARCH = "research"

    REMINDER = "reminder"

    COMMUNICATION = "communication"

    MEDIA = "media"

    CUSTOM = "custom"


class EnvironmentStatus(str, Enum):
    """Lifecycle state of an environment."""

    CREATED = "created"

    INITIALIZING = "initializing"

    ACTIVE = "active"

    PAUSED = "paused"

    COMPLETED = "completed"

    ERROR = "error"

    DESTROYED = "destroyed"


class EnvironmentCapability(str, Enum):
    """Capabilities an environment can expose."""

    TEXT_INPUT = "text_input"

    VOICE_INPUT = "voice_input"

    IMAGE_INPUT = "image_input"

    CAMERA_INPUT = "camera_input"

    FILE_INPUT = "file_input"

    FILE_OUTPUT = "file_output"

    WEB_SEARCH = "web_search"

    CODE_EXECUTION = "code_execution"

    DOCUMENT_EDITING = "document_editing"

    EMAIL = "email"

    CALENDAR = "calendar"

    REMINDER = "reminder"

    COLLABORATION = "collaboration"

    UI_GENERATION = "ui_generation"


@dataclass
class EnvironmentConfig:
    """Configuration controlling an AIOS environment."""

    name: str

    environment_type: EnvironmentType = (
        EnvironmentType.GENERAL
    )

    description: str = ""

    capabilities: List[
        EnvironmentCapability
    ] = field(
        default_factory=list
    )

    persistent: bool = True

    auto_save: bool = True

    allow_external_actions: bool = False

    allow_network: bool = False

    allow_file_system: bool = False

    max_memory_items: int = 1000

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""

        return {
            "name": self.name,
            "environment_type": (
                self.environment_type.value
            ),
            "description": self.description,
            "capabilities": [
                capability.value
                for capability
                in self.capabilities
            ],
            "persistent": self.persistent,
            "auto_save": self.auto_save,
            "allow_external_actions": (
                self.allow_external_actions
            ),
            "allow_network": (
                self.allow_network
            ),
            "allow_file_system": (
                self.allow_file_system
            ),
            "max_memory_items": (
                self.max_memory_items
            ),
            "metadata": self.metadata,
        }


@dataclass
class Environment:
    """
    Represents a dynamic AIOS workspace/environment.
    """

    id: str = field(
        default_factory=lambda: str(
            uuid.uuid4()
        )
    )

    name: str = "AIOS Environment"

    environment_type: EnvironmentType = (
        EnvironmentType.GENERAL
    )

    description: str = ""

    status: EnvironmentStatus = (
        EnvironmentStatus.CREATED
    )

    capabilities: List[
        EnvironmentCapability
    ] = field(
        default_factory=list
    )

    session_id: Optional[str] = None

    user_id: Optional[str] = None

    parent_environment_id: Optional[str] = None

    config: Optional[
        EnvironmentConfig
    ] = None

    data: Dict[str, Any] = field(
        default_factory=dict
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    created_at: str = field(
        default_factory=utc_now
    )

    updated_at: str = field(
        default_factory=utc_now
    )

    def __post_init__(self) -> None:
        """Initialize missing configuration."""

        if self.config is None:
            self.config = EnvironmentConfig(
                name=self.name,
                environment_type=(
                    self.environment_type
                ),
                description=self.description,
                capabilities=list(
                    self.capabilities
                ),
            )

    def activate(self) -> None:
        """Activate environment."""

        self.status = EnvironmentStatus.ACTIVE
        self.touch()

    def pause(self) -> None:
        """Pause environment."""

        self.status = EnvironmentStatus.PAUSED
        self.touch()

    def complete(self) -> None:
        """Mark environment as completed."""

        self.status = EnvironmentStatus.COMPLETED
        self.touch()

    def destroy(self) -> None:
        """Mark environment as destroyed."""

        self.status = EnvironmentStatus.DESTROYED
        self.touch()

    def fail(self) -> None:
        """Mark environment as failed."""

        self.status = EnvironmentStatus.ERROR
        self.touch()

    def touch(self) -> None:
        """Update modification timestamp."""

        self.updated_at = utc_now()

    def set_data(
        self,
        key: str,
        value: Any,
    ) -> None:
        """Set environment data."""

        self.data[key] = value
        self.touch()

    def get_data(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Get environment data."""

        return self.data.get(
            key,
            default,
        )

    def remove_data(
        self,
        key: str,
    ) -> Any:
        """Remove environment data."""

        value = self.data.pop(
            key,
            None,
        )

        self.touch()

        return value

    def has_capability(
        self,
        capability: EnvironmentCapability,
    ) -> bool:
        """Check whether environment supports a capability."""

        return capability in self.capabilities

    def to_dict(self) -> Dict[str, Any]:
        """Serialize environment."""

        return {
            "id": self.id,
            "name": self.name,
            "environment_type": (
                self.environment_type.value
            ),
            "description": self.description,
            "status": self.status.value,
            "capabilities": [
                capability.value
                for capability
                in self.capabilities
            ],
            "session_id": self.session_id,
            "user_id": self.user_id,
            "parent_environment_id": (
                self.parent_environment_id
            ),
            "config": (
                self.config.to_dict()
                if self.config
                else None
            ),
            "data": self.data,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }