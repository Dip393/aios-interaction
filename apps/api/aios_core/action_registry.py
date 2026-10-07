"""
AIOS Action Registry

Central registry for all actions/tools available to AIOS.

Examples:

    send_email
    create_reminder
    search_web
    create_environment
    run_code

The registry only describes and resolves actions.
Execution is handled later by the Execution Engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional


ActionHandler = Callable[..., Any]


@dataclass
class ActionDefinition:
    """Definition of one AIOS action."""

    name: str

    description: str

    category: str

    handler: Optional[ActionHandler] = None

    parameters: Dict[str, Any] = field(
        default_factory=dict
    )

    requires_confirmation: bool = False

    enabled: bool = True

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": self.parameters,
            "requires_confirmation": (
                self.requires_confirmation
            ),
            "enabled": self.enabled,
            "metadata": self.metadata,
            "has_handler": self.handler is not None,
        }


class ActionRegistry:
    """
    Registry containing all available AIOS actions.
    """

    def __init__(self) -> None:
        self._actions: Dict[
            str,
            ActionDefinition,
        ] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        action: ActionDefinition,
        *,
        overwrite: bool = False,
    ) -> ActionDefinition:
        """Register an action."""

        name = action.name.strip()

        if not name:
            raise ValueError(
                "Action name cannot be empty."
            )

        if (
            name in self._actions
            and not overwrite
        ):
            raise ValueError(
                f"Action '{name}' is already registered."
            )

        action.name = name

        self._actions[name] = action

        return action

    def register_many(
        self,
        actions: Iterable[ActionDefinition],
        *,
        overwrite: bool = False,
    ) -> None:
        """Register multiple actions."""

        for action in actions:
            self.register(
                action,
                overwrite=overwrite,
            )

    # ------------------------------------------------------------------
    # Removal
    # ------------------------------------------------------------------

    def unregister(
        self,
        name: str,
    ) -> bool:
        """Remove an action from the registry."""

        return self._actions.pop(
            name,
            None,
        ) is not None

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(
        self,
        name: str,
    ) -> Optional[ActionDefinition]:
        """Return an action definition."""

        return self._actions.get(
            name.strip()
        )

    def require(
        self,
        name: str,
    ) -> ActionDefinition:
        """Return an action or raise KeyError."""

        action = self.get(name)

        if action is None:
            raise KeyError(
                f"Action '{name}' is not registered."
            )

        return action

    def exists(
        self,
        name: str,
    ) -> bool:
        return name.strip() in self._actions

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def enable(
        self,
        name: str,
    ) -> None:
        action = self.require(name)

        action.enabled = True

    def disable(
        self,
        name: str,
    ) -> None:
        action = self.require(name)

        action.enabled = False

    # ------------------------------------------------------------------
    # Handler
    # ------------------------------------------------------------------

    def attach_handler(
        self,
        name: str,
        handler: ActionHandler,
    ) -> None:
        """Attach an executable handler to an action."""

        action = self.require(name)

        if not callable(handler):
            raise TypeError(
                "Action handler must be callable."
            )

        action.handler = handler

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    def list(
        self,
        *,
        category: Optional[str] = None,
        enabled_only: bool = False,
    ) -> List[ActionDefinition]:
        """List registered actions."""

        actions = list(
            self._actions.values()
        )

        if category:
            actions = [
                action
                for action in actions
                if action.category == category
            ]

        if enabled_only:
            actions = [
                action
                for action in actions
                if action.enabled
            ]

        return sorted(
            actions,
            key=lambda action: action.name,
        )

    def describe(
        self,
        *,
        enabled_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """Return serializable action descriptions."""

        return [
            action.to_dict()
            for action in self.list(
                enabled_only=enabled_only
            )
        ]

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_parameters(
        self,
        name: str,
        parameters: Dict[str, Any],
    ) -> None:
        """
        Basic parameter validation.

        Detailed JSON schema validation can be introduced later.
        """

        action = self.require(name)

        schema = action.parameters or {}

        required = schema.get(
            "required",
            [],
        )

        for field_name in required:
            if field_name not in parameters:
                raise ValueError(
                    f"Missing required parameter "
                    f"'{field_name}' for action '{name}'."
                )

    # ------------------------------------------------------------------
    # Execution preparation
    # ------------------------------------------------------------------

    def prepare(
        self,
        name: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validate and prepare an action for the execution engine.

        This method does not execute anything.
        """

        action = self.require(name)

        if not action.enabled:
            raise RuntimeError(
                f"Action '{name}' is disabled."
            )

        parameters = parameters or {}

        self.validate_parameters(
            name,
            parameters,
        )

        return {
            "action": action.name,
            "category": action.category,
            "description": action.description,
            "parameters": parameters,
            "requires_confirmation": (
                action.requires_confirmation
            ),
            "handler_available": (
                action.handler is not None
            ),
        }

    # ------------------------------------------------------------------
    # Size / iteration
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._actions)

    def __contains__(
        self,
        name: str,
    ) -> bool:
        return self.exists(name)

    def __iter__(self):
        return iter(
            self._actions.values()
        )


def create_default_registry() -> ActionRegistry:
    """
    Create the default AIOS action registry.

    These are action definitions only.
    Actual handlers are attached by the agent/execution layer.
    """

    registry = ActionRegistry()

    registry.register_many(
        [
            ActionDefinition(
                name="respond",
                description=(
                    "Generate a normal conversational response."
                ),
                category="core",
            ),
            ActionDefinition(
                name="resolve_contact",
                description=(
                    "Resolve a person's identity/contact information."
                ),
                category="communication",
                parameters={
                    "required": ["name"],
                },
            ),
            ActionDefinition(
                name="compose_email",
                description=(
                    "Create an email draft."
                ),
                category="communication",
                parameters={
                    "required": ["recipient"],
                },
            ),
            ActionDefinition(
                name="send_email",
                description=(
                    "Send an email to an external recipient."
                ),
                category="communication",
                requires_confirmation=True,
                parameters={
                    "required": [
                        "recipient",
                        "subject",
                        "body",
                    ],
                },
            ),
            ActionDefinition(
                name="send_message",
                description=(
                    "Send an external message."
                ),
                category="communication",
                requires_confirmation=True,
                parameters={
                    "required": [
                        "recipient",
                        "message",
                    ],
                },
            ),
            ActionDefinition(
                name="create_reminder",
                description=(
                    "Create a local reminder."
                ),
                category="productivity",
                parameters={
                    "required": [
                        "title",
                        "scheduled_at",
                    ],
                },
            ),
            ActionDefinition(
                name="create_calendar_event",
                description=(
                    "Create a calendar event."
                ),
                category="calendar",
                parameters={
                    "required": [
                        "title",
                        "start",
                    ],
                },
            ),
            ActionDefinition(
                name="create_environment",
                description=(
                    "Create a dynamic AIOS workspace."
                ),
                category="environment",
                parameters={
                    "required": ["environment_type"],
                },
            ),
            ActionDefinition(
                name="open_environment",
                description=(
                    "Open an existing AIOS workspace."
                ),
                category="environment",
                parameters={
                    "required": ["environment_id"],
                },
            ),
            ActionDefinition(
                name="pause_task",
                description=(
                    "Pause the current AIOS task."
                ),
                category="task",
            ),
            ActionDefinition(
                name="resume_task",
                description=(
                    "Resume a paused AIOS task."
                ),
                category="task",
                parameters={
                    "required": ["task_id"],
                },
            ),
            ActionDefinition(
                name="search_web",
                description=(
                    "Search the web for information."
                ),
                category="research",
                parameters={
                    "required": ["query"],
                },
            ),
            ActionDefinition(
                name="read_file",
                description=(
                    "Read a local user file."
                ),
                category="filesystem",
                parameters={
                    "required": ["path"],
                },
            ),
            ActionDefinition(
                name="create_file",
                description=(
                    "Create a new local file."
                ),
                category="filesystem",
                parameters={
                    "required": [
                        "path",
                        "content",
                    ],
                },
            ),
            ActionDefinition(
                name="write_file",
                description=(
                    "Modify an existing local file."
                ),
                category="filesystem",
                parameters={
                    "required": [
                        "path",
                        "content",
                    ],
                },
            ),
            ActionDefinition(
                name="run_code",
                description=(
                    "Run code inside a controlled environment."
                ),
                category="development",
                parameters={
                    "required": [
                        "language",
                        "code",
                    ],
                },
            ),
            ActionDefinition(
                name="search_memory",
                description=(
                    "Search the user's stored AIOS memory."
                ),
                category="memory",
                parameters={
                    "required": ["query"],
                },
            ),
            ActionDefinition(
                name="store_memory",
                description=(
                    "Store a useful piece of long-term memory."
                ),
                category="memory",
                parameters={
                    "required": ["content"],
                },
            ),
        ]
    )

    return registry