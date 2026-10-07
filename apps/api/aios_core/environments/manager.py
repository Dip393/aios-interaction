"""
AIOS Environment Manager.

The EnvironmentManager coordinates:

- Environment creation
- Template selection
- Registry management
- State management
- Activation
- Pause
- Completion
- Destruction
- Environment switching
- Environment snapshots
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional

from .registry import EnvironmentRegistry
from .schemas import (
    Environment,
    EnvironmentCapability,
    EnvironmentConfig,
    EnvironmentStatus,
    EnvironmentType,
)
from .state import (
    EnvironmentState,
    EnvironmentStateStore,
)
from .templates import (
    EnvironmentTemplate,
    EnvironmentTemplateRegistry,
    create_default_template_registry,
)


class EnvironmentManager:
    """
    Main controller for AIOS environments.
    """

    def __init__(
        self,
        *,
        registry: Optional[
            EnvironmentRegistry
        ] = None,
        state_store: Optional[
            EnvironmentStateStore
        ] = None,
        template_registry: Optional[
            EnvironmentTemplateRegistry
        ] = None,
    ) -> None:

        self.registry = (
            registry
            or EnvironmentRegistry()
        )

        self.state_store = (
            state_store
            or EnvironmentStateStore()
        )

        self.templates = (
            template_registry
            or create_default_template_registry()
        )

        self._active_by_session: Dict[
            str,
            str,
        ] = {}

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    def create(
        self,
        *,
        name: Optional[str] = None,
        environment_type: EnvironmentType = (
            EnvironmentType.GENERAL
        ),
        template: Optional[str] = None,
        description: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        parent_environment_id: Optional[str] = None,
        capabilities: Optional[
            List[EnvironmentCapability]
        ] = None,
        config: Optional[
            EnvironmentConfig
        ] = None,
        metadata: Optional[
            Dict[str, Any]
        ] = None,
        initial_data: Optional[
            Dict[str, Any]
        ] = None,
    ) -> Environment:
        """
        Create a new environment.

        Template takes priority when supplied.
        """

        selected_template: Optional[
            EnvironmentTemplate
        ] = None

        if template:
            selected_template = (
                self.templates.get(
                    template
                )
            )

            if selected_template is None:
                raise KeyError(
                    f"Environment template "
                    f"'{template}' does not exist."
                )

            environment_type = (
                selected_template
                .environment_type
            )

        if config is None:

            if selected_template:

                config = (
                    selected_template
                    .create_config(
                        name=name
                    )
                )

            else:

                config = EnvironmentConfig(
                    name=(
                        name
                        or "AIOS Environment"
                    ),
                    environment_type=(
                        environment_type
                    ),
                    description=(
                        description
                        or ""
                    ),
                    capabilities=(
                        capabilities
                        or []
                    ),
                )

        final_name = (
            name
            or config.name
            or "AIOS Environment"
        )

        final_description = (
            description
            if description is not None
            else config.description
        )

        final_capabilities = (
            capabilities
            if capabilities is not None
            else list(
                config.capabilities
            )
        )

        environment = Environment(
            name=final_name,
            environment_type=(
                environment_type
            ),
            description=(
                final_description
            ),
            capabilities=(
                final_capabilities
            ),
            session_id=session_id,
            user_id=user_id,
            parent_environment_id=(
                parent_environment_id
            ),
            config=config,
            metadata=(
                metadata
                or {}
            ),
        )

        # Apply template initial data.
        if selected_template:

            environment.data.update(
                copy.deepcopy(
                    selected_template.initial_data
                )
            )

        if initial_data:

            environment.data.update(
                copy.deepcopy(
                    initial_data
                )
            )

        self.registry.register(
            environment
        )

        self.state_store.create(
            environment.id
        )

        environment.status = (
            EnvironmentStatus.ACTIVE
        )

        environment.touch()

        if session_id:
            self._active_by_session[
                session_id
            ] = environment.id

        return environment

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------

    def get(
        self,
        environment_id: str,
    ) -> Optional[
        Environment
    ]:
        """Get environment."""

        return self.registry.get(
            environment_id
        )

    def require(
        self,
        environment_id: str,
    ) -> Environment:
        """Get environment or raise KeyError."""

        return self.registry.require(
            environment_id
        )

    # ------------------------------------------------------------------
    # ACTIVE ENVIRONMENT
    # ------------------------------------------------------------------

    def get_active(
        self,
        session_id: str,
    ) -> Optional[
        Environment
    ]:
        """Get active environment for a session."""

        environment_id = (
            self._active_by_session.get(
                session_id
            )
        )

        if not environment_id:
            return None

        environment = self.get(
            environment_id
        )

        if environment is None:
            self._active_by_session.pop(
                session_id,
                None,
            )

            return None

        return environment

    def switch(
        self,
        environment_id: str,
        *,
        session_id: Optional[str] = None,
    ) -> Environment:
        """Switch the active environment."""

        environment = self.require(
            environment_id
        )

        if environment.status in {
            EnvironmentStatus.DESTROYED,
            EnvironmentStatus.ERROR,
        }:
            raise ValueError(
                "Cannot activate a destroyed or errored environment."
            )

        if session_id is None:
            session_id = (
                environment.session_id
            )

        if session_id:

            current = self.get_active(
                session_id
            )

            if (
                current
                and current.id
                != environment.id
            ):
                current.pause()

            self._active_by_session[
                session_id
            ] = environment.id

        environment.activate()

        return environment

    # ------------------------------------------------------------------
    # STATE
    # ------------------------------------------------------------------

    def get_state(
        self,
        environment_id: str,
    ) -> EnvironmentState:
        """Get runtime state."""

        self.require(
            environment_id
        )

        return self.state_store.require(
            environment_id
        )

    def set_state(
        self,
        environment_id: str,
        key: str,
        value: Any,
    ) -> EnvironmentState:
        """Set environment runtime state."""

        state = self.get_state(
            environment_id
        )

        state.set(
            key,
            value,
        )

        return state

    def get_state_value(
        self,
        environment_id: str,
        key: str,
        default: Any = None,
    ) -> Any:
        """Get one state value."""

        state = self.get_state(
            environment_id
        )

        return state.get(
            key,
            default,
        )

    # ------------------------------------------------------------------
    # LIFECYCLE
    # ------------------------------------------------------------------

    def pause(
        self,
        environment_id: str,
    ) -> Environment:
        """Pause an environment."""

        environment = self.require(
            environment_id
        )

        environment.pause()

        if (
            environment.session_id
            and self._active_by_session.get(
                environment.session_id
            )
            == environment.id
        ):
            self._active_by_session.pop(
                environment.session_id,
                None,
            )

        return environment

    def complete(
        self,
        environment_id: str,
    ) -> Environment:
        """Complete an environment."""

        environment = self.require(
            environment_id
        )

        environment.complete()

        if (
            environment.session_id
            and self._active_by_session.get(
                environment.session_id
            )
            == environment.id
        ):
            self._active_by_session.pop(
                environment.session_id,
                None,
            )

        return environment

    def destroy(
        self,
        environment_id: str,
    ) -> bool:
        """
        Destroy an environment.

        The registry entry and runtime state are removed after marking the
        environment destroyed.
        """

        environment = self.get(
            environment_id
        )

        if environment is None:
            return False

        environment.destroy()

        if (
            environment.session_id
            and self._active_by_session.get(
                environment.session_id
            )
            == environment.id
        ):
            self._active_by_session.pop(
                environment.session_id,
                None,
            )

        self.state_store.delete(
            environment_id
        )

        return self.registry.unregister(
            environment_id
        )

    # ------------------------------------------------------------------
    # DATA
    # ------------------------------------------------------------------

    def set_data(
        self,
        environment_id: str,
        key: str,
        value: Any,
    ) -> Environment:
        """Set persistent environment data."""

        environment = self.require(
            environment_id
        )

        environment.set_data(
            key,
            value,
        )

        return environment

    def get_data(
        self,
        environment_id: str,
        key: str,
        default: Any = None,
    ) -> Any:
        """Get persistent environment data."""

        environment = self.require(
            environment_id
        )

        return environment.get_data(
            key,
            default,
        )

    # ------------------------------------------------------------------
    # SNAPSHOT / RESTORE
    # ------------------------------------------------------------------

    def snapshot(
        self,
        environment_id: str,
    ) -> Dict[str, Any]:
        """Create a complete environment snapshot."""

        environment = self.require(
            environment_id
        )

        state = self.get_state(
            environment_id
        )

        return {
            "environment": copy.deepcopy(
                environment.to_dict()
            ),
            "state": state.snapshot(),
        }

    def restore_state(
        self,
        environment_id: str,
        snapshot: Dict[str, Any],
    ) -> EnvironmentState:
        """Restore runtime state from snapshot."""

        return self.state_store.restore(
            environment_id,
            snapshot.get(
                "state",
                {},
            ),
        )

    # ------------------------------------------------------------------
    # FIND
    # ------------------------------------------------------------------

    def find_by_type(
        self,
        environment_type: EnvironmentType,
    ) -> List[
        Environment
    ]:
        """Find environments by type."""

        return self.registry.find_by_type(
            environment_type
        )

    def find_by_session(
        self,
        session_id: str,
    ) -> List[
        Environment
    ]:
        """Find environments for session."""

        return self.registry.find_by_session(
            session_id
        )

    def list(
        self,
    ) -> List[
        Environment
    ]:
        """List all environments."""

        return self.registry.list()

    # ------------------------------------------------------------------
    # TEMPLATE
    # ------------------------------------------------------------------

    def list_templates(self) -> List[
        EnvironmentTemplate
    ]:
        """List available environment templates."""

        return self.templates.list()

    # ------------------------------------------------------------------
    # INFORMATION
    # ------------------------------------------------------------------

    def info(self) -> Dict[str, Any]:
        """Return manager status."""

        environments = self.list()

        return {
            "total_environments": len(
                environments
            ),
            "active_environments": len(
                [
                    environment
                    for environment
                    in environments
                    if (
                        environment.status
                        == EnvironmentStatus.ACTIVE
                    )
                ]
            ),
            "templates": len(
                self.templates.list()
            ),
            "active_sessions": len(
                self._active_by_session
            ),
        }