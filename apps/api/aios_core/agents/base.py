"""
Base agent architecture for AIOS.

Every specialized AIOS agent should inherit from the Agent class.

The base layer intentionally contains no external service dependency.
Agents communicate through structured AgentContext and AgentResult objects.
"""

from __future__ import annotations

import inspect
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional


def utc_now() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


class AgentStatus(str, Enum):
    """Possible execution states of an agent."""

    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    NEEDS_INPUT = "needs_input"
    NEEDS_CONFIRMATION = "needs_confirmation"
    NOT_IMPLEMENTED = "not_implemented"


@dataclass
class AgentContext:
    """
    Context passed to an agent.

    The object is deliberately generic so that the same architecture can
    support text, voice, image, files, scheduled tasks and future modalities.
    """

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = "default"
    user_id: str = "local-user"

    input_text: str = ""
    input_source: str = "text"

    locale: str = "en-IN"
    timezone: str = "Asia/Kolkata"

    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    memories: List[Dict[str, Any]] = field(default_factory=list)

    previous_results: List[Dict[str, Any]] = field(default_factory=list)

    def get(self, key: str, default: Any = None) -> Any:
        """Read a variable from the agent context."""
        return self.variables.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Store a variable in the agent context."""
        self.variables[key] = value

    def add_result(self, result: Dict[str, Any]) -> None:
        """Append a previous agent/action result."""
        self.previous_results.append(result)

    def remember(self, memory: Dict[str, Any]) -> None:
        """Add a lightweight memory entry."""
        self.memories.append(memory)


@dataclass
class AgentResult:
    """
    Standard result returned by every AIOS agent.
    """

    status: AgentStatus

    agent: str

    message: str = ""

    data: Dict[str, Any] = field(default_factory=dict)

    error: Optional[str] = None

    requires_confirmation: bool = False

    confirmation_reason: Optional[str] = None

    rollback_supported: bool = False

    rollback_token: Optional[str] = None

    request_id: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    created_at: str = field(default_factory=utc_now)

    @property
    def success(self) -> bool:
        """Return True when the agent completed successfully."""
        return self.status == AgentStatus.SUCCESS

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a JSON-friendly dictionary."""
        return {
            "status": self.status.value,
            "agent": self.agent,
            "message": self.message,
            "data": self.data,
            "error": self.error,
            "requires_confirmation": self.requires_confirmation,
            "confirmation_reason": self.confirmation_reason,
            "rollback_supported": self.rollback_supported,
            "rollback_token": self.rollback_token,
            "request_id": self.request_id,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


class Agent(ABC):
    """
    Base class for every AIOS specialized agent.

    Example:

        class MyAgent(Agent):
            name = "my_agent"

            async def run(self, context, params):
                ...
    """

    name: str = "base_agent"
    description: str = "Base AIOS agent"

    capabilities: List[str] = []

    def __init__(
        self,
        *,
        enabled: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.enabled = enabled
        self.metadata = metadata or {}

    @abstractmethod
    async def run(
        self,
        context: AgentContext,
        params: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:
        """
        Execute the agent.

        Subclasses must implement this method.
        """
        raise NotImplementedError

    async def execute(
        self,
        context: AgentContext,
        params: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:
        """
        Safe public execution wrapper.

        This method handles:
        - disabled agents
        - missing parameters
        - unexpected exceptions
        - standardized AgentResult
        """

        if not self.enabled:
            return AgentResult(
                status=AgentStatus.FAILED,
                agent=self.name,
                message=f"Agent '{self.name}' is disabled.",
                error="agent_disabled",
                request_id=context.request_id,
            )

        try:
            result = self.run(context, params or {})

            if inspect.isawaitable(result):
                result = await result

            if not isinstance(result, AgentResult):
                return AgentResult(
                    status=AgentStatus.FAILED,
                    agent=self.name,
                    message="Agent returned an invalid result.",
                    error="invalid_agent_result",
                    request_id=context.request_id,
                )

            if result.request_id is None:
                result.request_id = context.request_id

            return result

        except Exception as exc:
            return AgentResult(
                status=AgentStatus.FAILED,
                agent=self.name,
                message=f"Agent '{self.name}' failed.",
                error=str(exc),
                request_id=context.request_id,
            )

    def info(self) -> Dict[str, Any]:
        """Return metadata describing this agent."""

        return {
            "name": self.name,
            "description": self.description,
            "capabilities": list(self.capabilities),
            "enabled": self.enabled,
            "metadata": dict(self.metadata),
        }

    def success(
        self,
        context: AgentContext,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AgentResult:
        """Convenience method for successful results."""

        return AgentResult(
            status=AgentStatus.SUCCESS,
            agent=self.name,
            message=message,
            data=data or {},
            request_id=context.request_id,
            **kwargs,
        )

    def failure(
        self,
        context: AgentContext,
        message: str,
        error: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AgentResult:
        """Convenience method for failed results."""

        return AgentResult(
            status=AgentStatus.FAILED,
            agent=self.name,
            message=message,
            error=error,
            data=data or {},
            request_id=context.request_id,
            **kwargs,
        )

    def needs_input(
        self,
        context: AgentContext,
        message: str,
        missing_fields: Optional[List[str]] = None,
    ) -> AgentResult:
        """Return a result requesting additional user information."""

        return AgentResult(
            status=AgentStatus.NEEDS_INPUT,
            agent=self.name,
            message=message,
            data={
                "missing_fields": missing_fields or [],
            },
            request_id=context.request_id,
        )

    def needs_confirmation(
        self,
        context: AgentContext,
        message: str,
        reason: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:
        """Return a result requesting explicit confirmation."""

        return AgentResult(
            status=AgentStatus.NEEDS_CONFIRMATION,
            agent=self.name,
            message=message,
            data=data or {},
            requires_confirmation=True,
            confirmation_reason=reason,
            request_id=context.request_id,
        )


class AgentRegistry:
    """
    Lightweight registry for specialized agents.

    This registry is intentionally independent from the action registry.
    The ActionRegistry handles executable actions, while this registry handles
    higher-level AI agents.
    """

    def __init__(self) -> None:
        self._agents: Dict[str, Agent] = {}

    def register(self, agent: Agent) -> Agent:
        """Register an agent."""
        if not isinstance(agent, Agent):
            raise TypeError("Only Agent instances can be registered.")

        self._agents[agent.name] = agent
        return agent

    def unregister(self, name: str) -> bool:
        """Remove an agent from the registry."""
        return self._agents.pop(name, None) is not None

    def get(self, name: str) -> Optional[Agent]:
        """Get an agent by name."""
        return self._agents.get(name)

    def require(self, name: str) -> Agent:
        """Get an agent or raise KeyError."""
        agent = self.get(name)

        if agent is None:
            raise KeyError(f"Agent '{name}' is not registered.")

        return agent

    def list_agents(self) -> List[Dict[str, Any]]:
        """Return information about all registered agents."""
        return [agent.info() for agent in self._agents.values()]

    async def execute(
        self,
        name: str,
        context: AgentContext,
        params: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:
        """Execute a registered agent."""

        agent = self.get(name)

        if agent is None:
            return AgentResult(
                status=AgentStatus.FAILED,
                agent=name,
                message=f"Agent '{name}' is not registered.",
                error="agent_not_found",
                request_id=context.request_id,
            )

        return await agent.execute(context, params or {})


def create_default_agent_registry() -> AgentRegistry:
    """
    Create and register all standard AIOS agents.

    Imports are local to avoid circular imports during package loading.
    """

    from .email_agent import EmailAgent
    from .calendar_agent import CalendarAgent
    from .writing_agent import WritingAgent
    from .code_agent import CodeAgent
    from .file_agent import FileAgent
    from .search_agent import SearchAgent
    from .reminder_agent import ReminderAgent

    registry = AgentRegistry()

    registry.register(EmailAgent())
    registry.register(CalendarAgent())
    registry.register(WritingAgent())
    registry.register(CodeAgent())
    registry.register(FileAgent())
    registry.register(SearchAgent())
    registry.register(ReminderAgent())

    return registry