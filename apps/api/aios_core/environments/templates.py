"""
AIOS Environment Templates.

Templates allow the kernel to create specialized environments quickly.

Example:

    Writing Environment
    Code Environment
    Research Environment
    Email Environment
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .schemas import (
    EnvironmentCapability,
    EnvironmentConfig,
    EnvironmentType,
)


@dataclass
class EnvironmentTemplate:
    """Template used to create an environment."""

    name: str

    environment_type: EnvironmentType

    description: str

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

    initial_data: Dict[str, Any] = field(
        default_factory=dict
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def create_config(
        self,
        *,
        name: Optional[str] = None,
    ) -> EnvironmentConfig:
        """Create EnvironmentConfig from this template."""

        return EnvironmentConfig(
            name=name or self.name,
            environment_type=(
                self.environment_type
            ),
            description=self.description,
            capabilities=list(
                self.capabilities
            ),
            persistent=self.persistent,
            auto_save=self.auto_save,
            allow_external_actions=(
                self.allow_external_actions
            ),
            allow_network=(
                self.allow_network
            ),
            allow_file_system=(
                self.allow_file_system
            ),
            metadata=dict(
                self.metadata
            ),
        )


class EnvironmentTemplateRegistry:
    """Registry of environment templates."""

    def __init__(self) -> None:

        self._templates: Dict[
            str,
            EnvironmentTemplate,
        ] = {}

    def register(
        self,
        template: EnvironmentTemplate,
    ) -> EnvironmentTemplate:
        """Register a template."""

        if not isinstance(
            template,
            EnvironmentTemplate,
        ):
            raise TypeError(
                "template must be an EnvironmentTemplate."
            )

        self._templates[
            template.name.lower()
        ] = template

        return template

    def get(
        self,
        name: str,
    ) -> Optional[
        EnvironmentTemplate
    ]:
        """Get template by name."""

        return self._templates.get(
            name.lower()
        )

    def require(
        self,
        name: str,
    ) -> EnvironmentTemplate:
        """Get template or raise KeyError."""

        template = self.get(
            name
        )

        if template is None:
            raise KeyError(
                f"Environment template "
                f"'{name}' does not exist."
            )

        return template

    def unregister(
        self,
        name: str,
    ) -> bool:
        """Remove a template."""

        return (
            self._templates.pop(
                name.lower(),
                None,
            )
            is not None
        )

    def list(
        self,
    ) -> List[
        EnvironmentTemplate
    ]:
        """List all templates."""

        return list(
            self._templates.values()
        )


def create_default_template_registry() -> (
    EnvironmentTemplateRegistry
):
    """Create the standard AIOS environment templates."""

    registry = EnvironmentTemplateRegistry()

    # --------------------------------------------------------------
    # GENERAL
    # --------------------------------------------------------------

    registry.register(
        EnvironmentTemplate(
            name="general",
            environment_type=(
                EnvironmentType.GENERAL
            ),
            description=(
                "General-purpose AIOS workspace."
            ),
            capabilities=[
                EnvironmentCapability.TEXT_INPUT,
                EnvironmentCapability.UI_GENERATION,
            ],
        )
    )

    # --------------------------------------------------------------
    # WRITING
    # --------------------------------------------------------------

    registry.register(
        EnvironmentTemplate(
            name="writing",
            environment_type=(
                EnvironmentType.WRITING
            ),
            description=(
                "Dynamic workspace for writing, "
                "editing and document creation."
            ),
            capabilities=[
                EnvironmentCapability.TEXT_INPUT,
                EnvironmentCapability.VOICE_INPUT,
                EnvironmentCapability.DOCUMENT_EDITING,
                EnvironmentCapability.FILE_OUTPUT,
                EnvironmentCapability.UI_GENERATION,
            ],
            allow_file_system=True,
            initial_data={
                "document": None,
                "cursor_position": 0,
                "suggestions": [],
            },
        )
    )

    # --------------------------------------------------------------
    # DOCUMENT
    # --------------------------------------------------------------

    registry.register(
        EnvironmentTemplate(
            name="document",
            environment_type=(
                EnvironmentType.DOCUMENT
            ),
            description=(
                "Workspace for creating and editing documents."
            ),
            capabilities=[
                EnvironmentCapability.TEXT_INPUT,
                EnvironmentCapability.VOICE_INPUT,
                EnvironmentCapability.DOCUMENT_EDITING,
                EnvironmentCapability.FILE_INPUT,
                EnvironmentCapability.FILE_OUTPUT,
                EnvironmentCapability.UI_GENERATION,
            ],
            allow_file_system=True,
        )
    )

    # --------------------------------------------------------------
    # EMAIL
    # --------------------------------------------------------------

    registry.register(
        EnvironmentTemplate(
            name="email",
            environment_type=(
                EnvironmentType.EMAIL
            ),
            description=(
                "Workspace for composing, reviewing "
                "and preparing emails."
            ),
            capabilities=[
                EnvironmentCapability.TEXT_INPUT,
                EnvironmentCapability.VOICE_INPUT,
                EnvironmentCapability.EMAIL,
                EnvironmentCapability.UI_GENERATION,
            ],
            allow_external_actions=False,
            initial_data={
                "recipient": None,
                "subject": "",
                "body": "",
                "draft": None,
            },
        )
    )

    # --------------------------------------------------------------
    # CALENDAR
    # --------------------------------------------------------------

    registry.register(
        EnvironmentTemplate(
            name="calendar",
            environment_type=(
                EnvironmentType.CALENDAR
            ),
            description=(
                "Workspace for meetings and calendar events."
            ),
            capabilities=[
                EnvironmentCapability.TEXT_INPUT,
                EnvironmentCapability.VOICE_INPUT,
                EnvironmentCapability.CALENDAR,
                EnvironmentCapability.UI_GENERATION,
            ],
            initial_data={
                "event": None,
                "attendees": [],
            },
        )
    )

    # --------------------------------------------------------------
    # CODE
    # --------------------------------------------------------------

    registry.register(
        EnvironmentTemplate(
            name="code",
            environment_type=(
                EnvironmentType.CODE
            ),
            description=(
                "Development workspace for software projects."
            ),
            capabilities=[
                EnvironmentCapability.TEXT_INPUT,
                EnvironmentCapability.VOICE_INPUT,
                EnvironmentCapability.FILE_INPUT,
                EnvironmentCapability.FILE_OUTPUT,
                EnvironmentCapability.CODE_EXECUTION,
                EnvironmentCapability.UI_GENERATION,
            ],
            allow_file_system=True,
            initial_data={
                "project": None,
                "files": {},
                "terminal_output": [],
            },
        )
    )

    # --------------------------------------------------------------
    # PROJECT
    # --------------------------------------------------------------

    registry.register(
        EnvironmentTemplate(
            name="project",
            environment_type=(
                EnvironmentType.PROJECT
            ),
            description=(
                "Workspace for multi-step project creation."
            ),
            capabilities=[
                EnvironmentCapability.TEXT_INPUT,
                EnvironmentCapability.FILE_INPUT,
                EnvironmentCapability.FILE_OUTPUT,
                EnvironmentCapability.CODE_EXECUTION,
                EnvironmentCapability.UI_GENERATION,
            ],
            allow_file_system=True,
        )
    )

    # --------------------------------------------------------------
    # FILE
    # --------------------------------------------------------------

    registry.register(
        EnvironmentTemplate(
            name="file",
            environment_type=(
                EnvironmentType.FILE
            ),
            description=(
                "Workspace for file management."
            ),
            capabilities=[
                EnvironmentCapability.TEXT_INPUT,
                EnvironmentCapability.FILE_INPUT,
                EnvironmentCapability.FILE_OUTPUT,
                EnvironmentCapability.UI_GENERATION,
            ],
            allow_file_system=True,
        )
    )

    # --------------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------------

    registry.register(
        EnvironmentTemplate(
            name="search",
            environment_type=(
                EnvironmentType.SEARCH
            ),
            description=(
                "Workspace for web and knowledge search."
            ),
            capabilities=[
                EnvironmentCapability.TEXT_INPUT,
                EnvironmentCapability.VOICE_INPUT,
                EnvironmentCapability.WEB_SEARCH,
                EnvironmentCapability.UI_GENERATION,
            ],
            allow_network=False,
        )
    )

    # --------------------------------------------------------------
    # RESEARCH
    # --------------------------------------------------------------

    registry.register(
        EnvironmentTemplate(
            name="research",
            environment_type=(
                EnvironmentType.RESEARCH
            ),
            description=(
                "Workspace for multi-step research and information analysis."
            ),
            capabilities=[
                EnvironmentCapability.TEXT_INPUT,
                EnvironmentCapability.VOICE_INPUT,
                EnvironmentCapability.WEB_SEARCH,
                EnvironmentCapability.FILE_INPUT,
                EnvironmentCapability.FILE_OUTPUT,
                EnvironmentCapability.DOCUMENT_EDITING,
                EnvironmentCapability.UI_GENERATION,
            ],
            allow_network=False,
        )
    )

    # --------------------------------------------------------------
    # REMINDER
    # --------------------------------------------------------------

    registry.register(
        EnvironmentTemplate(
            name="reminder",
            environment_type=(
                EnvironmentType.REMINDER
            ),
            description=(
                "Workspace for reminders and scheduled tasks."
            ),
            capabilities=[
                EnvironmentCapability.TEXT_INPUT,
                EnvironmentCapability.VOICE_INPUT,
                EnvironmentCapability.REMINDER,
                EnvironmentCapability.UI_GENERATION,
            ],
            initial_data={
                "reminders": [],
            },
        )
    )

    return registry