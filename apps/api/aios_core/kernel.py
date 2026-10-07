"""
AIOS Kernel

The central orchestration layer of AIOS.

The kernel coordinates:

    User Input
        ↓
    Context
        ↓
    Intent Detection
        ↓
    Planning
        ↓
    Policy Evaluation
        ↓
    Execution Plan
        ↓
    User-facing result

IMPORTANT:
The kernel does NOT directly perform dangerous/external actions.

Actual execution is delegated to the Execution Engine and Agents.

This separation is intentional.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .action_registry import (
    ActionRegistry,
    create_default_registry,
)
from .context import AIOSContext
from .intent import IntentEngine, UserIntent
from .planner import (
    ExecutionPlan,
    Planner,
)
from .policy import (
    PolicyDecision,
    PolicyEngine,
    PolicyResult,
)


@dataclass
class KernelStepEvaluation:
    """Policy evaluation for one planned step."""

    step_id: str

    action: str

    policy: PolicyResult

    parameters: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "action": self.action,
            "parameters": self.parameters,
            "policy": self.policy.to_dict(),
        }


@dataclass
class KernelResponse:
    """Complete response returned by the AIOS kernel."""

    success: bool

    message: str

    intent: UserIntent

    plan: ExecutionPlan

    evaluations: List[
        KernelStepEvaluation
    ] = field(
        default_factory=list
    )

    requires_confirmation: bool = False

    confirmation_ids: List[str] = field(
        default_factory=list
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "intent": self.intent.to_dict(),
            "plan": self.plan.to_dict(),
            "evaluations": [
                evaluation.to_dict()
                for evaluation in self.evaluations
            ],
            "requires_confirmation": (
                self.requires_confirmation
            ),
            "confirmation_ids": (
                self.confirmation_ids
            ),
            "metadata": self.metadata,
        }


class AIOSKernel:
    """
    Main AIOS orchestration kernel.
    """

    def __init__(
        self,
        *,
        context: Optional[AIOSContext] = None,
        intent_engine: Optional[IntentEngine] = None,
        registry: Optional[ActionRegistry] = None,
        policy_engine: Optional[PolicyEngine] = None,
        planner: Optional[Planner] = None,
        llm: Optional[Any] = None,
    ) -> None:
        self.context = (
            context
            or AIOSContext()
        )

        self.intent_engine = (
            intent_engine
            or IntentEngine()
        )

        self.registry = (
            registry
            or create_default_registry()
        )

        self.policy_engine = (
            policy_engine
            or PolicyEngine()
        )

        self.planner = (
            planner
            or Planner(
                registry=self.registry,
                llm=llm,
            )
        )

    # ------------------------------------------------------------------
    # Main command processing
    # ------------------------------------------------------------------

    async def process(
        self,
        user_input: str,
        *,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> KernelResponse:
        """
        Process one user command.

        This method performs:
        1. Input validation
        2. Context update
        3. Intent detection
        4. Planning
        5. Policy evaluation
        6. Confirmation creation
        7. Response preparation

        It does NOT execute the actions.
        """

        if not user_input or not user_input.strip():
            raise ValueError(
                "AIOS command cannot be empty."
            )

        user_input = user_input.strip()

        if metadata:
            self.context.metadata.update(
                metadata
            )

        # --------------------------------------------------------------
        # 1. Add user message
        # --------------------------------------------------------------

        self.context.add_message(
            role="user",
            content=user_input,
        )

        # --------------------------------------------------------------
        # 2. Detect intent
        # --------------------------------------------------------------

        intent = self.intent_engine.detect(
            user_input
        )

        # --------------------------------------------------------------
        # 3. Start/update task
        # --------------------------------------------------------------

        self._update_task_from_intent(
            intent
        )

        # --------------------------------------------------------------
        # 4. Add relevant intent information to context
        # --------------------------------------------------------------

        self.context.metadata[
            "last_intent"
        ] = intent.to_dict()

        # --------------------------------------------------------------
        # 5. Generate plan
        # --------------------------------------------------------------

        plan = await self.planner.plan(
            intent,
            self.context,
        )

        # --------------------------------------------------------------
        # 6. Evaluate every action through policy
        # --------------------------------------------------------------

        evaluations: List[
            KernelStepEvaluation
        ] = []

        confirmation_ids: List[str] = []

        blocked = False

        for step in plan.steps:
            policy_result = (
                self.policy_engine.evaluate(
                    step.action,
                    step.parameters,
                )
            )

            evaluation = KernelStepEvaluation(
                step_id=step.step_id,
                action=step.action,
                policy=policy_result,
                parameters=step.parameters,
            )

            evaluations.append(
                evaluation
            )

            if (
                policy_result.decision
                == PolicyDecision.BLOCK
            ):
                blocked = True

            if (
                policy_result.decision
                == PolicyDecision.CONFIRM
            ):
                confirmation = (
                    self.context.add_confirmation(
                        action_type=step.action,
                        description=step.description,
                        risk_level=(
                            policy_result
                            .risk_level
                            .value
                        ),
                        payload={
                            "plan_id": plan.plan_id,
                            "step_id": step.step_id,
                            "parameters": (
                                step.parameters
                            ),
                        },
                    )
                )

                confirmation_ids.append(
                    confirmation.confirmation_id
                )

        # --------------------------------------------------------------
        # 7. Determine response
        # --------------------------------------------------------------

        if blocked:
            message = (
                "I understood the request, but "
                "one or more requested actions are "
                "blocked by the AIOS security policy."
            )

            success = False

        elif confirmation_ids:
            message = self._confirmation_message(
                intent,
                evaluations,
            )

            success = True

        else:
            message = self._plan_message(
                intent,
                plan,
            )

            success = True

        # --------------------------------------------------------------
        # 8. Record kernel action
        # --------------------------------------------------------------

        self.context.record_action(
            {
                "type": "kernel_process",
                "intent": intent.name,
                "plan_id": plan.plan_id,
                "success": success,
                "requires_confirmation": bool(
                    confirmation_ids
                ),
            }
        )

        return KernelResponse(
            success=success,
            message=message,
            intent=intent,
            plan=plan,
            evaluations=evaluations,
            requires_confirmation=bool(
                confirmation_ids
            ),
            confirmation_ids=confirmation_ids,
            metadata={
                "kernel_version": "0.2.0",
                "execution_started": False,
                "note": (
                    "Actions are planned and policy-checked. "
                    "Execution is handled separately."
                ),
            },
        )

    # ------------------------------------------------------------------
    # Task handling
    # ------------------------------------------------------------------

    def _update_task_from_intent(
        self,
        intent: UserIntent,
    ) -> None:
        """
        Update the working task based on the detected intent.

        The task manager itself will later become persistent.
        For now the runtime context handles the working state.
        """

        if intent.name in {
            "general_chat",
            "unknown",
        }:
            return

        title = self._task_title(
            intent
        )

        self.context.start_task(
            task_type=intent.name,
            title=title,
            metadata={
                "domain": intent.domain,
                "confidence": intent.confidence,
            },
        )

    @staticmethod
    def _task_title(
        intent: UserIntent,
    ) -> str:
        mapping = {
            "send_email": "Send email",
            "write_email": "Write email",
            "create_reminder": "Create reminder",
            "schedule_event": "Schedule event",
            "write_content": "Writing task",
            "create_code": "Coding task",
            "search_web": "Research task",
            "create_file": "File creation task",
        }

        return mapping.get(
            intent.name,
            "AIOS Task",
        )

    # ------------------------------------------------------------------
    # Response generation
    # ------------------------------------------------------------------

    @staticmethod
    def _confirmation_message(
        intent: UserIntent,
        evaluations: List[
            KernelStepEvaluation
        ],
    ) -> str:
        confirmed_actions = [
            evaluation.action
            for evaluation in evaluations
            if evaluation.policy.decision
            == PolicyDecision.CONFIRM
        ]

        if (
            "send_email"
            in confirmed_actions
        ):
            recipient = (
                intent.entities.get(
                    "recipient"
                )
                or intent.entities.get(
                    "email"
                )
                or "the recipient"
            )

            return (
                f"I prepared the email for "
                f"{recipient}. "
                "Sending it will create an external "
                "side effect. Please confirm before I send it."
            )

        if "send_message" in confirmed_actions:
            return (
                "The message is ready. "
                "Please confirm before sending it."
            )

        return (
            "The requested action is ready, "
            "but it requires your confirmation "
            "before execution."
        )

    @staticmethod
    def _plan_message(
        intent: UserIntent,
        plan: ExecutionPlan,
    ) -> str:
        if intent.name == "write_content":
            return (
                "I understood this as a writing task "
                "and prepared a writing environment."
            )

        if intent.name == "create_code":
            return (
                "I understood this as a coding task "
                "and prepared a coding environment."
            )

        if intent.name == "create_reminder":
            return (
                "I understood this as a reminder task "
                "and prepared the reminder action."
            )

        if intent.name == "search_web":
            return (
                "I understood this as a research request "
                "and prepared a search plan."
            )

        return (
            f"I understood your request as "
            f"'{intent.name}' and prepared "
            f"{len(plan.steps)} action(s)."
        )

    # ------------------------------------------------------------------
    # Context helpers
    # ------------------------------------------------------------------

    def get_context(
        self,
    ) -> Dict[str, Any]:
        """Return current AIOS runtime context."""

        return self.context.to_dict()

    def get_available_actions(
        self,
    ) -> List[Dict[str, Any]]:
        """Return all currently available actions."""

        return self.registry.describe(
            enabled_only=True
        )

    def reset_context(self) -> None:
        """Reset the current AIOS session."""

        self.context.clear_session()