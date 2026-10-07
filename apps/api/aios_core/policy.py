"""
AIOS Policy Engine

Controls what AIOS is allowed to execute automatically.

The policy engine classifies actions by risk.

Risk levels:

LOW
    Safe internal operations.

MEDIUM
    Operations that modify user-owned data.

HIGH
    External side effects.

CRITICAL
    Dangerous/destructive operations.

The policy engine does not execute actions.
It only decides whether an action:
- can run automatically
- needs confirmation
- must be blocked
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PolicyDecision(str, Enum):
    ALLOW = "allow"
    CONFIRM = "confirm"
    BLOCK = "block"


@dataclass
class PolicyResult:
    """Result returned by the policy engine."""

    decision: PolicyDecision

    risk_level: RiskLevel

    action: str

    reason: str

    requires_confirmation: bool = False

    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision.value,
            "risk_level": self.risk_level.value,
            "action": self.action,
            "reason": self.reason,
            "requires_confirmation": self.requires_confirmation,
            "metadata": self.metadata or {},
        }


class PolicyEngine:
    """
    Central authorization policy for AIOS actions.
    """

    def __init__(
        self,
        require_confirmation_for_high_risk: bool = True,
        allow_critical_actions: bool = False,
    ) -> None:
        self.require_confirmation_for_high_risk = (
            require_confirmation_for_high_risk
        )

        self.allow_critical_actions = allow_critical_actions

        self._risk_map: Dict[str, RiskLevel] = {
            # ----------------------------------------------------------
            # Low-risk actions
            # ----------------------------------------------------------
            "respond": RiskLevel.LOW,
            "read_memory": RiskLevel.LOW,
            "search_memory": RiskLevel.LOW,
            "search_web": RiskLevel.LOW,
            "read_file": RiskLevel.LOW,
            "list_files": RiskLevel.LOW,
            "open_environment": RiskLevel.LOW,
            "create_environment": RiskLevel.LOW,
            "pause_task": RiskLevel.LOW,
            "resume_task": RiskLevel.LOW,
            "create_reminder": RiskLevel.LOW,

            # ----------------------------------------------------------
            # Medium-risk actions
            # ----------------------------------------------------------
            "write_file": RiskLevel.MEDIUM,
            "create_file": RiskLevel.MEDIUM,
            "modify_file": RiskLevel.MEDIUM,
            "create_calendar_event": RiskLevel.MEDIUM,
            "create_workspace": RiskLevel.MEDIUM,
            "install_dependency": RiskLevel.MEDIUM,
            "run_code": RiskLevel.MEDIUM,

            # ----------------------------------------------------------
            # High-risk external actions
            # ----------------------------------------------------------
            "send_email": RiskLevel.HIGH,
            "send_message": RiskLevel.HIGH,
            "send_whatsapp_message": RiskLevel.HIGH,
            "publish_content": RiskLevel.HIGH,
            "submit_form": RiskLevel.HIGH,

            # ----------------------------------------------------------
            # Critical operations
            # ----------------------------------------------------------
            "delete_file": RiskLevel.CRITICAL,
            "delete_folder": RiskLevel.CRITICAL,
            "execute_shell": RiskLevel.CRITICAL,
            "system_command": RiskLevel.CRITICAL,
            "financial_transaction": RiskLevel.CRITICAL,
            "delete_account": RiskLevel.CRITICAL,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(
        self,
        action: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> PolicyResult:
        """
        Evaluate whether an action is permitted.

        Parameters are inspected for additional risk signals.
        """

        action = action.strip().lower()

        risk = self._risk_map.get(
            action,
            RiskLevel.MEDIUM,
        )

        parameters = parameters or {}

        # Critical actions are blocked by default.
        if risk == RiskLevel.CRITICAL:
            if not self.allow_critical_actions:
                return PolicyResult(
                    decision=PolicyDecision.BLOCK,
                    risk_level=risk,
                    action=action,
                    reason=(
                        "Critical system actions are disabled "
                        "by the default AIOS security policy."
                    ),
                    requires_confirmation=False,
                    metadata={
                        "parameters_present": bool(parameters),
                    },
                )

            return PolicyResult(
                decision=PolicyDecision.CONFIRM,
                risk_level=risk,
                action=action,
                reason=(
                    "Critical action requires explicit user "
                    "confirmation."
                ),
                requires_confirmation=True,
            )

        # High-risk actions require confirmation.
        if (
            risk == RiskLevel.HIGH
            and self.require_confirmation_for_high_risk
        ):
            return PolicyResult(
                decision=PolicyDecision.CONFIRM,
                risk_level=risk,
                action=action,
                reason=(
                    "This action creates an external side effect "
                    "and requires user confirmation."
                ),
                requires_confirmation=True,
            )

        # Medium risk actions are allowed by default.
        if risk == RiskLevel.MEDIUM:
            return PolicyResult(
                decision=PolicyDecision.ALLOW,
                risk_level=risk,
                action=action,
                reason=(
                    "Action modifies local/user-owned state "
                    "but is allowed by the current policy."
                ),
                requires_confirmation=False,
            )

        # Low risk actions are automatically allowed.
        return PolicyResult(
            decision=PolicyDecision.ALLOW,
            risk_level=risk,
            action=action,
            reason="Low-risk action is automatically allowed.",
            requires_confirmation=False,
        )

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------

    def requires_confirmation(
        self,
        action: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> bool:
        result = self.evaluate(
            action,
            parameters,
        )

        return result.requires_confirmation

    def is_allowed(
        self,
        action: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> bool:
        result = self.evaluate(
            action,
            parameters,
        )

        return result.decision == PolicyDecision.ALLOW

    def is_blocked(
        self,
        action: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> bool:
        result = self.evaluate(
            action,
            parameters,
        )

        return result.decision == PolicyDecision.BLOCK

    def get_risk_level(
        self,
        action: str,
    ) -> RiskLevel:
        return self._risk_map.get(
            action.strip().lower(),
            RiskLevel.MEDIUM,
        )