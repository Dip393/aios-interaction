"""
AIOS Execution Engine.

The ExecutionEngine is responsible for:

1. Receiving an Action
2. Looking up its ActionDefinition
3. Validating the action
4. Applying confirmation requirements
5. Applying sandbox restrictions
6. Executing the handler
7. Producing an ExecutionResult
8. Supporting rollback when possible

The engine does not decide what the user wants.
Intent and planning belong to the upper AIOS layers.
"""

from __future__ import annotations

import asyncio
import inspect
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .action import (
    Action,
    ActionDefinition,
    ActionStatus,
    invoke_handler,
)
from .result import (
    ExecutionResult,
    ExecutionStatus,
)
from .sandbox import (
    Sandbox,
    SandboxConfig,
    SandboxViolation,
)
from .validator import (
    ActionValidator,
)


@dataclass
class ExecutionEngineConfig:
    """Configuration for the execution engine."""

    default_timeout_seconds: float = 60.0

    auto_validate: bool = True

    require_confirmation_for_external_actions: bool = True

    require_confirmation_for_destructive_actions: bool = True

    auto_rollback_on_failure: bool = False

    enable_sandbox: bool = True

    sandbox_config: SandboxConfig = field(
        default_factory=SandboxConfig
    )


class ExecutionEngine:
    """
    Central execution engine for AIOS.

    Example:

        engine = ExecutionEngine()

        engine.register(
            ActionDefinition(
                name="hello",
                handler=my_handler,
            )
        )

        result = await engine.execute(
            Action(
                name="hello"
            )
        )
    """

    def __init__(
        self,
        config: Optional[
            ExecutionEngineConfig
        ] = None,
        validator: Optional[
            ActionValidator
        ] = None,
        sandbox: Optional[
            Sandbox
        ] = None,
    ) -> None:

        self.config = (
            config
            or ExecutionEngineConfig()
        )

        self.validator = (
            validator
            or ActionValidator()
        )

        self.sandbox = (
            sandbox
            or Sandbox(
                self.config.sandbox_config
            )
        )

        self._definitions: Dict[
            str,
            ActionDefinition,
        ] = {}

        self._rollback_handlers: Dict[
            str,
            ActionDefinition,
        ] = {}

        self._execution_history: list[
            ExecutionResult
        ] = []

    # ------------------------------------------------------------------
    # REGISTRATION
    # ------------------------------------------------------------------

    def register(
        self,
        definition: ActionDefinition,
    ) -> ActionDefinition:
        """Register an action definition."""

        if not isinstance(
            definition,
            ActionDefinition,
        ):
            raise TypeError(
                "definition must be an ActionDefinition."
            )

        if not definition.name.strip():
            raise ValueError(
                "Action name cannot be empty."
            )

        self._definitions[
            definition.name
        ] = definition

        return definition

    def unregister(
        self,
        name: str,
    ) -> bool:
        """Unregister an action."""

        return (
            self._definitions.pop(
                name,
                None,
            )
            is not None
        )

    def get_definition(
        self,
        name: str,
    ) -> Optional[
        ActionDefinition
    ]:
        """Get an action definition."""

        return self._definitions.get(
            name
        )

    def list_actions(self) -> list[
        Dict[str, Any]
    ]:
        """Return all registered actions."""

        return [
            {
                "name": definition.name,
                "description": definition.description,
                "risk_level": definition.risk_level,
                "reversible": definition.reversible,
                "requires_confirmation": (
                    definition.requires_confirmation
                ),
                "external_side_effect": (
                    definition.external_side_effect
                ),
                "destructive": (
                    definition.destructive
                ),
                "allowed_in_sandbox": (
                    definition.allowed_in_sandbox
                ),
            }
            for definition
            in self._definitions.values()
        ]

    # ------------------------------------------------------------------
    # CONFIRMATION
    # ------------------------------------------------------------------

    def _needs_confirmation(
        self,
        definition: ActionDefinition,
        confirmed: bool,
    ) -> bool:
        """Determine whether an action needs confirmation."""

        if confirmed:
            return False

        if (
            definition.requires_confirmation
        ):
            return True

        if (
            self.config
            .require_confirmation_for_external_actions
            and definition.external_side_effect
        ):
            return True

        if (
            self.config
            .require_confirmation_for_destructive_actions
            and definition.destructive
        ):
            return True

        return False

    # ------------------------------------------------------------------
    # EXECUTION
    # ------------------------------------------------------------------

    async def execute(
        self,
        action: Action,
        *,
        context: Any = None,
        confirmed: bool = False,
    ) -> ExecutionResult:
        """
        Execute one action.

        This is the main execution entry point.
        """

        if not isinstance(
            action,
            Action,
        ):
            raise TypeError(
                "action must be an Action instance."
            )

        started = time.perf_counter()

        definition = (
            self.get_definition(
                action.name
            )
        )

        # --------------------------------------------------------------
        # VALIDATION
        # --------------------------------------------------------------

        if self.config.auto_validate:

            validation = (
                self.validator.validate(
                    action,
                    definition,
                )
            )

            if not validation.valid:

                result = ExecutionResult(
                    success=False,
                    status=(
                        ExecutionStatus
                        .VALIDATION_FAILED
                    ),
                    action_name=action.name,
                    action_id=action.action_id,
                    request_id=action.request_id,
                    message=(
                        "Action validation failed."
                    ),
                    error="; ".join(
                        validation.reasons
                    ),
                    metadata={
                        "validation": (
                            validation.to_dict()
                        )
                    },
                )

                result.duration_ms = (
                    (
                        time.perf_counter()
                        - started
                    )
                    * 1000
                )

                self._execution_history.append(
                    result
                )

                action.mark_failed()

                return result

        # --------------------------------------------------------------
        # UNKNOWN ACTION
        # --------------------------------------------------------------

        if definition is None:

            result = ExecutionResult(
                success=False,
                status=ExecutionStatus.FAILED,
                action_name=action.name,
                action_id=action.action_id,
                request_id=action.request_id,
                message=(
                    f"Action '{action.name}' "
                    "is not registered."
                ),
                error="action_not_registered",
            )

            result.duration_ms = (
                (
                    time.perf_counter()
                    - started
                )
                * 1000
            )

            self._execution_history.append(
                result
            )

            action.mark_failed()

            return result

        # --------------------------------------------------------------
        # SANDBOX CHECK
        # --------------------------------------------------------------

        if (
            self.config.enable_sandbox
            and not definition.allowed_in_sandbox
        ):

            result = ExecutionResult(
                success=False,
                status=(
                    ExecutionStatus
                    .SANDBOX_VIOLATION
                ),
                action_name=action.name,
                action_id=action.action_id,
                request_id=action.request_id,
                message=(
                    "Action is not allowed "
                    "inside the AIOS sandbox."
                ),
                error="sandbox_policy_denied",
            )

            result.duration_ms = (
                (
                    time.perf_counter()
                    - started
                )
                * 1000
            )

            self._execution_history.append(
                result
            )

            action.mark_failed()

            return result

        # --------------------------------------------------------------
        # CONFIRMATION CHECK
        # --------------------------------------------------------------

        if self._needs_confirmation(
            definition,
            confirmed,
        ):

            result = (
                ExecutionResult.confirmation_required(
                    action_name=action.name,
                    action_id=action.action_id,
                    request_id=action.request_id,
                    reason=(
                        "This action creates an "
                        "external or destructive side effect."
                    ),
                    data={
                        "action": action.to_dict(),
                        "risk_level": (
                            definition.risk_level
                        ),
                    },
                )
            )

            result.duration_ms = (
                (
                    time.perf_counter()
                    - started
                )
                * 1000
            )

            self._execution_history.append(
                result
            )

            action.status = (
                ActionStatus
                .WAITING_CONFIRMATION
            )

            return result

        # --------------------------------------------------------------
        # HANDLER CHECK
        # --------------------------------------------------------------

        if not definition.has_handler():

            result = ExecutionResult(
                success=False,
                status=ExecutionStatus.FAILED,
                action_name=action.name,
                action_id=action.action_id,
                request_id=action.request_id,
                message=(
                    "Action has no executable handler."
                ),
                error="missing_handler",
            )

            result.duration_ms = (
                (
                    time.perf_counter()
                    - started
                )
                * 1000
            )

            self._execution_history.append(
                result
            )

            action.mark_failed()

            return result

        # --------------------------------------------------------------
        # EXECUTE
        # --------------------------------------------------------------

        action.mark_running()

        try:

            timeout = (
                definition.timeout_seconds
                or self.config
                .default_timeout_seconds
            )

            coroutine = invoke_handler(
                definition.handler,
                action,
                context,
            )

            if timeout and timeout > 0:
                data = await asyncio.wait_for(
                    coroutine,
                    timeout=timeout,
                )
            else:
                data = await coroutine

            action.mark_success()

            rollback_token = None

            if (
                definition.reversible
                and definition.has_rollback()
            ):
                rollback_token = (
                    str(uuid.uuid4())
                )

                self._rollback_handlers[
                    rollback_token
                ] = definition

            result = ExecutionResult(
                success=True,
                status=ExecutionStatus.SUCCESS,
                action_name=action.name,
                action_id=action.action_id,
                request_id=action.request_id,
                message=(
                    definition.description
                    or "Action executed successfully."
                ),
                data=data,
                rollback_available=(
                    definition.reversible
                    and definition.has_rollback()
                ),
                rollback_token=rollback_token,
            )

            result.duration_ms = (
                (
                    time.perf_counter()
                    - started
                )
                * 1000
            )

            result.add_log(
                f"Action '{action.name}' completed."
            )

            self._execution_history.append(
                result
            )

            return result

        # --------------------------------------------------------------
        # TIMEOUT
        # --------------------------------------------------------------

        except asyncio.TimeoutError:

            action.mark_failed()

            result = ExecutionResult(
                success=False,
                status=ExecutionStatus.TIMEOUT,
                action_name=action.name,
                action_id=action.action_id,
                request_id=action.request_id,
                message=(
                    "Action execution timed out."
                ),
                error="execution_timeout",
            )

            result.duration_ms = (
                (
                    time.perf_counter()
                    - started
                )
                * 1000
            )

            self._execution_history.append(
                result
            )

            return result

        # --------------------------------------------------------------
        # SANDBOX VIOLATION
        # --------------------------------------------------------------

        except SandboxViolation as exc:

            action.mark_failed()

            result = ExecutionResult(
                success=False,
                status=(
                    ExecutionStatus
                    .SANDBOX_VIOLATION
                ),
                action_name=action.name,
                action_id=action.action_id,
                request_id=action.request_id,
                message=(
                    "Action was blocked by the sandbox."
                ),
                error=str(exc),
            )

            result.duration_ms = (
                (
                    time.perf_counter()
                    - started
                )
                * 1000
            )

            self._execution_history.append(
                result
            )

            return result

        # --------------------------------------------------------------
        # GENERAL ERROR
        # --------------------------------------------------------------

        except Exception as exc:

            action.mark_failed()

            result = ExecutionResult(
                success=False,
                status=ExecutionStatus.FAILED,
                action_name=action.name,
                action_id=action.action_id,
                request_id=action.request_id,
                message=(
                    "Action execution failed."
                ),
                error=str(exc),
            )

            result.duration_ms = (
                (
                    time.perf_counter()
                    - started
                )
                * 1000
            )

            result.add_log(
                f"Execution error: {exc}"
            )

            self._execution_history.append(
                result
            )

            return result

    # ------------------------------------------------------------------
    # ROLLBACK
    # ------------------------------------------------------------------

    async def rollback(
        self,
        rollback_token: str,
        action: Optional[
            Action
        ] = None,
        context: Any = None,
    ) -> ExecutionResult:
        """
        Roll back an action using its rollback token.
        """

        definition = (
            self._rollback_handlers.get(
                rollback_token
            )
        )

        action_name = (
            action.name
            if action
            else "unknown"
        )

        if definition is None:

            return ExecutionResult(
                success=False,
                status=ExecutionStatus.FAILED,
                action_name=action_name,
                action_id=(
                    action.action_id
                    if action
                    else None
                ),
                request_id=(
                    action.request_id
                    if action
                    else None
                ),
                message=(
                    "Rollback token is invalid "
                    "or no rollback handler exists."
                ),
                error="rollback_not_available",
            )

        if not definition.has_rollback():

            return ExecutionResult(
                success=False,
                status=ExecutionStatus.FAILED,
                action_name=action_name,
                message=(
                    "This action cannot be rolled back."
                ),
                error="rollback_handler_missing",
            )

        if action is None:
            action = Action(
                name=action_name
            )

        try:

            result = await invoke_handler(
                definition.rollback_handler,
                action,
                context,
            )

            action.mark_rolled_back()

            self._rollback_handlers.pop(
                rollback_token,
                None,
            )

            return ExecutionResult(
                success=True,
                status=(
                    ExecutionStatus
                    .ROLLED_BACK
                ),
                action_name=action.name,
                action_id=action.action_id,
                request_id=action.request_id,
                message=(
                    "Action rolled back successfully."
                ),
                data=result,
                metadata={
                    "rollback_token": (
                        rollback_token
                    )
                },
            )

        except Exception as exc:

            return ExecutionResult(
                success=False,
                status=ExecutionStatus.FAILED,
                action_name=action.name,
                action_id=action.action_id,
                request_id=action.request_id,
                message=(
                    "Rollback failed."
                ),
                error=str(exc),
            )

    # ------------------------------------------------------------------
    # HISTORY
    # ------------------------------------------------------------------

    def history(
        self,
        limit: Optional[int] = None,
    ) -> list[Dict[str, Any]]:
        """Return execution history."""

        history = [
            result.to_dict()
            for result
            in self._execution_history
        ]

        if limit is not None:
            return history[-limit:]

        return history

    def clear_history(self) -> None:
        """Clear execution history."""
        self._execution_history.clear()

    # ------------------------------------------------------------------
    # STATUS
    # ------------------------------------------------------------------

    def info(self) -> Dict[str, Any]:
        """Return engine information."""

        return {
            "registered_actions": len(
                self._definitions
            ),
            "rollback_tokens": len(
                self._rollback_handlers
            ),
            "history_entries": len(
                self._execution_history
            ),
            "sandbox": self.sandbox.info(),
            "config": {
                "default_timeout_seconds": (
                    self.config
                    .default_timeout_seconds
                ),
                "auto_validate": (
                    self.config.auto_validate
                ),
                "require_confirmation_for_external_actions": (
                    self.config
                    .require_confirmation_for_external_actions
                ),
                "require_confirmation_for_destructive_actions": (
                    self.config
                    .require_confirmation_for_destructive_actions
                ),
                "auto_rollback_on_failure": (
                    self.config
                    .auto_rollback_on_failure
                ),
            },
        }