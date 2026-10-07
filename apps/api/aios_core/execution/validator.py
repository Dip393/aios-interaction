"""
AIOS Action Validator.

Validates executable actions before they reach the execution engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .action import Action, ActionDefinition


@dataclass
class ValidationResult:
    """Result of action validation."""

    valid: bool

    action_name: str

    reasons: List[str] = field(
        default_factory=list
    )

    warnings: List[str] = field(
        default_factory=list
    )

    requires_confirmation: bool = False

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary."""

        return {
            "valid": self.valid,
            "action_name": self.action_name,
            "reasons": self.reasons,
            "warnings": self.warnings,
            "requires_confirmation": (
                self.requires_confirmation
            ),
            "metadata": self.metadata,
        }


class ActionValidator:
    """
    Validates actions against their definitions and basic safety rules.
    """

    def __init__(
        self,
        *,
        allow_unknown_actions: bool = False,
        max_arguments: int = 100,
    ) -> None:

        self.allow_unknown_actions = (
            allow_unknown_actions
        )

        self.max_arguments = (
            max_arguments
        )

    def validate(
        self,
        action: Action,
        definition: Optional[
            ActionDefinition
        ],
    ) -> ValidationResult:
        """Validate one action."""

        reasons: List[str] = []
        warnings: List[str] = []

        if definition is None:
            if self.allow_unknown_actions:
                warnings.append(
                    "Action is not registered."
                )

                return ValidationResult(
                    valid=True,
                    action_name=action.name,
                    warnings=warnings,
                )

            return ValidationResult(
                valid=False,
                action_name=action.name,
                reasons=[
                    f"Action '{action.name}' is not registered."
                ],
            )

        if not definition.has_handler():
            reasons.append(
                "Action has no executable handler."
            )

        argument_count = (
            len(action.args)
            + len(action.kwargs)
        )

        if argument_count > self.max_arguments:
            reasons.append(
                "Action contains too many arguments."
            )

        if definition.destructive:
            warnings.append(
                "This action is destructive."
            )

        if definition.external_side_effect:
            warnings.append(
                "This action creates an external side effect."
            )

        if definition.requires_confirmation:
            return ValidationResult(
                valid=len(reasons) == 0,
                action_name=action.name,
                reasons=reasons,
                warnings=warnings,
                requires_confirmation=True,
                metadata={
                    "risk_level": (
                        definition.risk_level
                    ),
                    "reversible": (
                        definition.reversible
                    ),
                    "external_side_effect": (
                        definition.external_side_effect
                    ),
                },
            )

        return ValidationResult(
            valid=len(reasons) == 0,
            action_name=action.name,
            reasons=reasons,
            warnings=warnings,
            requires_confirmation=False,
            metadata={
                "risk_level": (
                    definition.risk_level
                ),
                "reversible": (
                    definition.reversible
                ),
                "external_side_effect": (
                    definition.external_side_effect
                ),
            },
        )

    def validate_arguments(
        self,
        action: Action,
        required_arguments: Optional[
            List[str]
        ] = None,
    ) -> ValidationResult:
        """Validate required action arguments."""

        required_arguments = (
            required_arguments or []
        )

        missing = []

        for argument in required_arguments:
            if argument in action.args:
                value = action.args.get(
                    argument
                )
            else:
                value = action.kwargs.get(
                    argument
                )

            if value is None or value == "":
                missing.append(
                    argument
                )

        if missing:
            return ValidationResult(
                valid=False,
                action_name=action.name,
                reasons=[
                    "Missing required arguments: "
                    + ", ".join(missing)
                ],
            )

        return ValidationResult(
            valid=True,
            action_name=action.name,
        )