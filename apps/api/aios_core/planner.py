"""
AIOS Planner

Transforms a detected user intent into an executable plan.

Pipeline:

    User Input
        ↓
    Intent
        ↓
    Planner
        ↓
    Execution Plan
        ↓
    Policy
        ↓
    Execution Engine

The planner does NOT execute actions.

Design goals:

    - deterministic planning by default
    - optional LLM-assisted planning
    - action registry validation
    - dependency ordering
    - confirmation detection
    - safe handling of missing information
    - compatibility with the AIOS Kernel
"""

from __future__ import annotations

import inspect
import json
import uuid

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .action_registry import ActionRegistry
from .intent import UserIntent


# ============================================================================
# Plan models
# ============================================================================


@dataclass
class PlanStep:
    """
    One executable step in an AIOS plan.
    """

    step_id: str
    action: str
    description: str

    parameters: Dict[str, Any] = field(
        default_factory=dict
    )

    depends_on: List[str] = field(
        default_factory=list
    )

    requires_confirmation: bool = False

    status: str = "pending"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionPlan:
    """
    Complete execution plan generated from a UserIntent.
    """

    plan_id: str
    intent_name: str
    goal: str

    steps: List[PlanStep] = field(
        default_factory=list
    )

    requires_confirmation: bool = False

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "intent_name": self.intent_name,
            "goal": self.goal,
            "steps": [
                step.to_dict()
                for step in self.steps
            ],
            "requires_confirmation": self.requires_confirmation,
            "metadata": self.metadata,
        }


# ============================================================================
# Planner
# ============================================================================


class Planner:
    """
    Converts UserIntent into an ExecutionPlan.

    The planner is deliberately side-effect free.

    It decides:
        - which actions should run
        - their parameters
        - their dependencies
        - whether confirmation is required

    It does NOT:
        - send email
        - modify files
        - call external services
        - execute code
        - mutate memory
    """

    CONFIRMATION_ACTIONS = {
        "send_email",
        "send_message",
        "send_whatsapp_message",
        "publish_content",
        "delete_file",
        "delete_directory",
        "execute_code",
        "external_api_call",
    }

    def __init__(
        self,
        registry: ActionRegistry,
        llm: Optional[Any] = None,
    ) -> None:
        self.registry = registry
        self.llm = llm

    # ========================================================================
    # Public API
    # ========================================================================

    async def plan(
        self,
        intent: UserIntent,
        context: Optional[Any] = None,
    ) -> ExecutionPlan:
        """
        Generate an execution plan.

        If an LLM planner is configured, it is attempted first.
        Any LLM failure falls back to deterministic planning.
        """

        if self.llm is not None:
            try:
                llm_plan = await self._plan_with_llm(
                    intent,
                    context,
                )

                if llm_plan is not None:
                    return llm_plan

            except Exception:
                # The LLM must never become a single point of failure.
                pass

        return self._plan_deterministically(intent)

    # ========================================================================
    # Deterministic planner
    # ========================================================================

    def _plan_deterministically(
        self,
        intent: UserIntent,
    ) -> ExecutionPlan:

        steps: List[PlanStep] = []

        actions = list(
            intent.requested_actions or []
        )

        # No action means the system should simply respond.
        if not actions:
            actions = ["respond"]

        previous_step_id: Optional[str] = None

        for index, action in enumerate(
            actions,
            start=1,
        ):
            action = str(action).strip()

            if not action:
                continue

            step_id = f"step_{index}"

            parameters = self._parameters_for_action(
                action,
                intent,
            )

            requires_confirmation = (
                self._requires_confirmation(
                    action=action,
                    intent=intent,
                )
            )

            step = PlanStep(
                step_id=step_id,
                action=action,
                description=self._describe_action(
                    action,
                    intent,
                ),
                parameters=parameters,
                depends_on=(
                    [previous_step_id]
                    if previous_step_id
                    else []
                ),
                requires_confirmation=requires_confirmation,
            )

            steps.append(step)

            previous_step_id = step_id

        if not steps:
            steps.append(
                PlanStep(
                    step_id="step_1",
                    action="respond",
                    description="Respond to the user.",
                    parameters={
                        "raw_text": intent.raw_text,
                    },
                )
            )

        return ExecutionPlan(
            plan_id=self._generate_plan_id(),
            intent_name=intent.name,
            goal=intent.raw_text,
            steps=steps,
            requires_confirmation=any(
                step.requires_confirmation
                for step in steps
            ),
            metadata={
                "planner": "deterministic",
                "intent_confidence": intent.confidence,
                "step_count": len(steps),
            },
        )

    # ========================================================================
    # Confirmation
    # ========================================================================

    def _requires_confirmation(
        self,
        action: str,
        intent: UserIntent,
    ) -> bool:

        if action in self.CONFIRMATION_ACTIONS:
            return True

        if intent.requires_confirmation:
            return True

        if not self.registry.exists(action):
            return False

        definition = self.registry.get(action)

        if definition is None:
            return False

        return bool(
            getattr(
                definition,
                "requires_confirmation",
                False,
            )
        )

    # ========================================================================
    # Parameter generation
    # ========================================================================

    def _parameters_for_action(
        self,
        action: str,
        intent: UserIntent,
    ) -> Dict[str, Any]:

        entities = dict(
            intent.entities or {}
        )

        if action == "resolve_contact":
            return {
                "name": (
                    entities.get("recipient")
                    or entities.get("recipient_name")
                    or ""
                ),
            }

        if action == "compose_email":
            return {
                "recipient": entities.get(
                    "recipient",
                    "",
                ),
                "email": entities.get(
                    "email"
                ) or entities.get(
                    "recipient_email"
                ),
                "subject": self._generate_subject(
                    intent
                ),
                "context": intent.raw_text,
            }

        if action == "send_email":
            return {
                "recipient": entities.get(
                    "recipient",
                    "",
                ),
                "email": entities.get(
                    "email"
                ) or entities.get(
                    "recipient_email"
                ),
                "subject": self._generate_subject(
                    intent
                ),
                "body": self._generate_email_body(
                    intent
                ),
            }

        if action == "create_reminder":
            return {
                "title": self._generate_reminder_title(
                    intent
                ),
                "scheduled_at": self._generate_reminder_time(
                    intent
                ),
                "source": "aios",
            }

        if action == "create_calendar_event":
            return {
                "title": self._generate_event_title(
                    intent
                ),
                "date": self._extract_value(
                    entities.get("date")
                ),
                "time": self._extract_time_value(
                    entities.get("time")
                ),
            }

        if action == "create_environment":
            return {
                "environment_type": (
                    entities.get(
                        "environment_type"
                    )
                    or intent.domain
                    or "generic"
                ),
                "name": entities.get(
                    "environment_name"
                ),
                "data": entities.get(
                    "environment_data",
                    {},
                ),
            }

        if action == "create_writing_environment":
            return {
                "environment_type": "writing",
                "name": entities.get(
                    "environment_name"
                ),
            }

        if action == "create_coding_environment":
            return {
                "environment_type": "coding",
                "name": entities.get(
                    "environment_name"
                ),
            }

        if action == "search_web":
            return {
                "query": (
                    entities.get("query")
                    or intent.raw_text
                ),
            }

        if action == "store_memory":
            return {
                "content": self._memory_candidate(
                    intent
                ),
                "category": (
                    entities.get(
                        "memory_category"
                    )
                    or "context"
                ),
                "source": "user_request",
            }

        if action == "create_file":
            return {
                "filename": (
                    entities.get("filename")
                    or entities.get("file_name")
                ),
                "content": entities.get(
                    "content",
                    "",
                ),
                "path": entities.get(
                    "path"
                ),
            }

        if action == "generate_code":
            return {
                "request": intent.raw_text,
                "language": entities.get(
                    "language"
                ),
            }

        if action == "generate_writing_assistance":
            return {
                "request": intent.raw_text,
                "style": entities.get(
                    "style"
                ),
            }

        if action == "request_clarification":
            return {
                "raw_text": intent.raw_text,
                "missing": entities.get(
                    "missing",
                    [],
                ),
            }

        if action == "respond":
            return {
                "raw_text": intent.raw_text,
            }

        return {
            "raw_text": intent.raw_text,
            "entities": entities,
        }

    # ========================================================================
    # Action descriptions
    # ========================================================================

    @staticmethod
    def _describe_action(
        action: str,
        intent: UserIntent,
    ) -> str:

        descriptions = {
            "resolve_contact": (
                "Resolve the requested contact."
            ),
            "compose_email": (
                "Prepare an email draft."
            ),
            "send_email": (
                "Send the email after confirmation."
            ),
            "extract_events": (
                "Extract useful events from the request."
            ),
            "store_memory": (
                "Store useful long-term context."
            ),
            "create_reminder": (
                "Create a reminder."
            ),
            "create_calendar_event": (
                "Create a calendar event."
            ),
            "create_environment": (
                "Create the requested AIOS environment."
            ),
            "create_writing_environment": (
                "Open a writing workspace."
            ),
            "create_coding_environment": (
                "Open a coding workspace."
            ),
            "generate_writing_assistance": (
                "Provide writing assistance."
            ),
            "generate_code": (
                "Generate the requested code."
            ),
            "run_tests": (
                "Run validation/tests."
            ),
            "verify_result": (
                "Verify the result."
            ),
            "search_web": (
                "Search for relevant information."
            ),
            "summarize_results": (
                "Summarize search results."
            ),
            "create_file": (
                "Create the requested file."
            ),
            "verify_file": (
                "Verify the created file."
            ),
            "send_message": (
                "Send the requested message."
            ),
            "publish_content": (
                "Publish the requested content."
            ),
            "respond": (
                "Respond to the user."
            ),
            "request_clarification": (
                "Ask the user for clarification."
            ),
        }

        return descriptions.get(
            action,
            f"Execute action: {action}",
        )

    # ========================================================================
    # Email helpers
    # ========================================================================

    @staticmethod
    def _generate_subject(
        intent: UserIntent,
    ) -> str:

        event = intent.entities.get(
            "event"
        )

        if isinstance(event, dict):
            event = (
                event.get("title")
                or event.get("name")
            )

        if event:
            return f"Regarding our {event}"

        return "Regarding our discussion"

    @staticmethod
    def _generate_email_body(
        intent: UserIntent,
    ) -> str:

        raw = (
            intent.raw_text or ""
        ).strip()

        event = intent.entities.get(
            "event"
        )

        if isinstance(event, dict):
            event = (
                event.get("title")
                or event.get("name")
            )

        date = intent.entities.get(
            "date"
        )

        date_label = Planner._extract_value(
            date
        )

        if event and date_label:
            return (
                "Hi,\n\n"
                f"Just a reminder regarding "
                f"our {event} on {date_label}.\n\n"
                "Best regards"
            )

        return (
            "Hi,\n\n"
            f"{raw}\n\n"
            "Best regards"
        )

    # ========================================================================
    # Reminder / calendar helpers
    # ========================================================================

    @staticmethod
    def _generate_reminder_title(
        intent: UserIntent,
    ) -> str:

        event = intent.entities.get(
            "event"
        )

        recipient = intent.entities.get(
            "recipient"
        )

        event_title = Planner._extract_value(
            event
        )

        if event_title and recipient:
            return (
                f"{event_title.title()} "
                f"with {recipient}"
            )

        if event_title:
            return event_title.title()

        return "AIOS Reminder"

    @staticmethod
    def _generate_event_title(
        intent: UserIntent,
    ) -> str:

        event = intent.entities.get(
            "event"
        )

        recipient = intent.entities.get(
            "recipient"
        )

        event_title = Planner._extract_value(
            event
        )

        if event_title and recipient:
            return (
                f"{event_title.title()} "
                f"with {recipient}"
            )

        if event_title:
            return event_title.title()

        return "AIOS Event"

    @staticmethod
    def _generate_reminder_time(
        intent: UserIntent,
    ) -> Optional[str]:
        """
        Return the explicitly requested date/time.

        The planner deliberately does not invent an exact time.
        """

        date_info = intent.entities.get(
            "date"
        )

        time_info = intent.entities.get(
            "time"
        )

        if not date_info:
            return None

        date_value = Planner._extract_value(
            date_info
        )

        if not date_value:
            return None

        time_value = Planner._extract_time_value(
            time_info
        )

        if time_value:
            return (
                f"{date_value}T"
                f"{time_value}:00"
            )

        return str(date_value)

    # ========================================================================
    # Memory
    # ========================================================================

    @staticmethod
    def _memory_candidate(
        intent: UserIntent,
    ) -> str:

        return (
            "User requested: "
            f"{(intent.raw_text or '').strip()}"
        )

    # ========================================================================
    # Generic value helpers
    # ========================================================================

    @staticmethod
    def _extract_value(
        value: Any,
    ) -> Optional[str]:

        if value is None:
            return None

        if isinstance(value, str):
            return value

        if isinstance(value, dict):
            for key in (
                "value",
                "label",
                "date",
                "name",
                "title",
                "text",
            ):
                candidate = value.get(key)

                if candidate is not None:
                    return str(candidate)

            return None

        return str(value)

    @staticmethod
    def _extract_time_value(
        value: Any,
    ) -> Optional[str]:

        if value is None:
            return None

        if isinstance(value, str):
            return value

        if isinstance(value, dict):
            for key in (
                "formatted",
                "time",
                "value",
            ):
                candidate = value.get(key)

                if candidate:
                    return str(candidate)

        return str(value)

    # ========================================================================
    # LLM planning
    # ========================================================================

    async def _plan_with_llm(
        self,
        intent: UserIntent,
        context: Optional[Any],
    ) -> Optional[ExecutionPlan]:

        if self.llm is None:
            return None

        available_actions = (
            self._describe_available_actions()
        )

        context_data: Dict[str, Any] = {}

        if context is not None:
            if hasattr(context, "to_dict"):
                try:
                    context_data = context.to_dict()
                except Exception:
                    context_data = {}

            elif isinstance(context, dict):
                context_data = context

        prompt = self._build_llm_prompt(
            intent,
            available_actions,
            context_data,
        )

        response = await self._call_llm(
            prompt
        )

        if not response:
            return None

        parsed = self._parse_json_response(
            response
        )

        if not parsed:
            return None

        return self._validate_llm_plan(
            parsed,
            intent,
        )

    def _describe_available_actions(
        self,
    ) -> List[Dict[str, Any]]:

        try:
            result = self.registry.describe(
                enabled_only=True
            )

            if isinstance(result, list):
                return result

            return list(result)

        except Exception:
            return []

    def _build_llm_prompt(
        self,
        intent: UserIntent,
        available_actions: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> str:

        return f"""
You are the planning engine of AIOS.

Your job is to convert the user's intent into a safe,
machine-readable execution plan.

DO NOT execute anything.

Return JSON only.

User intent:

{json.dumps(
    intent.to_dict(),
    ensure_ascii=False,
    indent=2,
)}

Available actions:

{json.dumps(
    available_actions,
    ensure_ascii=False,
    indent=2,
)}

Current context:

{json.dumps(
    context,
    ensure_ascii=False,
    indent=2,
)}

Required JSON format:

{{
  "steps": [
    {{
      "action": "action_name",
      "description": "what this step does",
      "parameters": {{}},
      "depends_on": [],
      "requires_confirmation": false
    }}
  ]
}}

Rules:

1. Use only available actions.
2. Never invent action names.
3. External side effects require confirmation.
4. Do not fabricate contact information.
5. Do not invent exact dates or times.
6. Prefer the minimum number of steps.
7. Use clarification when required information is missing.
8. Do not execute tools.
9. Do not include markdown.
10. Do not include explanations outside the JSON.
""".strip()

    async def _call_llm(
        self,
        prompt: str,
    ) -> Optional[str]:

        if self.llm is None:
            return None

        result: Any

        if hasattr(
            self.llm,
            "generate",
        ):
            result = self.llm.generate(
                prompt
            )

        elif hasattr(
            self.llm,
            "complete",
        ):
            result = self.llm.complete(
                prompt
            )

        else:
            raise TypeError(
                "Configured LLM must expose "
                "'generate' or 'complete'."
            )

        if inspect.isawaitable(result):
            result = await result

        if result is None:
            return None

        # Support adapters returning:
        #   str
        #   {"text": "..."}
        #   {"response": "..."}
        #   {"content": "..."}
        #   {"output": "..."}
        if isinstance(result, dict):
            for key in (
                "text",
                "response",
                "content",
                "output",
            ):
                if key in result:
                    return str(
                        result[key]
                    )

        return str(result)

    # ========================================================================
    # JSON parsing
    # ========================================================================

    @staticmethod
    def _parse_json_response(
        response: str,
    ) -> Optional[Dict[str, Any]]:

        response = (
            response or ""
        ).strip()

        if not response:
            return None

        # Direct JSON.
        try:
            parsed = json.loads(
                response
            )

            return (
                parsed
                if isinstance(parsed, dict)
                else None
            )

        except json.JSONDecodeError:
            pass

        # Markdown JSON fence.
        candidates = []

        if "```json" in response:
            candidates.append(
                response.split(
                    "```json",
                    1,
                )[1].split(
                    "```",
                    1,
                )[0].strip()
            )

        if "```" in response:
            parts = response.split(
                "```"
            )

            if len(parts) >= 3:
                candidates.append(
                    parts[1].strip()
                )

        for candidate in candidates:
            try:
                parsed = json.loads(
                    candidate
                )

                if isinstance(parsed, dict):
                    return parsed

            except json.JSONDecodeError:
                continue

        # Last-resort extraction of the outermost JSON object.
        start = response.find("{")
        end = response.rfind("}")

        if start >= 0 and end > start:
            try:
                parsed = json.loads(
                    response[
                        start:end + 1
                    ]
                )

                if isinstance(parsed, dict):
                    return parsed

            except json.JSONDecodeError:
                pass

        return None

    # ========================================================================
    # LLM plan validation
    # ========================================================================

    def _validate_llm_plan(
        self,
        data: Dict[str, Any],
        intent: UserIntent,
    ) -> Optional[ExecutionPlan]:

        raw_steps = data.get(
            "steps"
        )

        if not isinstance(
            raw_steps,
            list,
        ):
            return None

        steps: List[PlanStep] = []

        for index, raw_step in enumerate(
            raw_steps,
            start=1,
        ):
            if not isinstance(
                raw_step,
                dict,
            ):
                return None

            action = str(
                raw_step.get(
                    "action",
                    "",
                )
            ).strip()

            if not action:
                return None

            # LLM is never allowed to invent actions.
            if not self.registry.exists(
                action
            ):
                return None

            definition = self.registry.get(
                action
            )

            if definition is None:
                return None

            parameters = raw_step.get(
                "parameters",
                {},
            )

            if not isinstance(
                parameters,
                dict,
            ):
                return None

            dependencies = raw_step.get(
                "depends_on",
                [],
            )

            if not isinstance(
                dependencies,
                list,
            ):
                return None

            step_id = f"step_{index}"

            # Validate dependencies.
            valid_step_ids = {
                f"step_{i}"
                for i in range(1, index)
            }

            dependencies = [
                str(dep)
                for dep in dependencies
                if str(dep) in valid_step_ids
            ]

            registry_confirmation = bool(
                getattr(
                    definition,
                    "requires_confirmation",
                    False,
                )
            )

            requested_confirmation = bool(
                raw_step.get(
                    "requires_confirmation",
                    False,
                )
            )

            safety_confirmation = (
                action in self.CONFIRMATION_ACTIONS
            )

            requires_confirmation = (
                registry_confirmation
                or requested_confirmation
                or safety_confirmation
            )

            description = str(
                raw_step.get(
                    "description",
                    getattr(
                        definition,
                        "description",
                        self._describe_action(
                            action,
                            intent,
                        ),
                    ),
                )
            )

            step = PlanStep(
                step_id=step_id,
                action=action,
                description=description,
                parameters=parameters,
                depends_on=dependencies,
                requires_confirmation=(
                    requires_confirmation
                ),
            )

            steps.append(step)

        if not steps:
            return None

        return ExecutionPlan(
            plan_id=self._generate_plan_id(),
            intent_name=intent.name,
            goal=intent.raw_text,
            steps=steps,
            requires_confirmation=any(
                step.requires_confirmation
                for step in steps
            ),
            metadata={
                "planner": "llm",
                "validated": True,
                "step_count": len(steps),
            },
        )

    # ========================================================================
    # Utility
    # ========================================================================

    @staticmethod
    def _generate_plan_id() -> str:
        return (
            f"plan_{uuid.uuid4().hex[:12]}"
        )


# ============================================================================
# Compatibility helper
# ============================================================================


async def build_plan(
    intent: UserIntent,
    registry: ActionRegistry,
    context: Optional[Any] = None,
    llm: Optional[Any] = None,
) -> ExecutionPlan:
    """
    Convenience wrapper around Planner.

    Useful for code that does not need to retain a Planner instance.
    """

    planner = Planner(
        registry=registry,
        llm=llm,
    )

    return await planner.plan(
        intent=intent,
        context=context,
    )


# ============================================================================
# Module-level plan helper
# ============================================================================


async def plan(
    intent: UserIntent,
    registry: Optional[ActionRegistry] = None,
    context: Optional[Any] = None,
    llm: Optional[Any] = None,
) -> ExecutionPlan:
    """
    Module-level planner entry point.

    This keeps compatibility with code such as:

        from .aios_core.planner import plan

    If an ActionRegistry is supplied, it is used directly.
    Otherwise a default registry is created.

    The planner itself remains side-effect free.
    """

    if registry is None:
        registry = ActionRegistry()

    planner = Planner(
        registry=registry,
        llm=llm,
    )

    return await planner.plan(
        intent=intent,
        context=context,
    )