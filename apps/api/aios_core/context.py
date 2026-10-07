"""
AIOS Context Engine

Maintains the runtime context of the current AIOS session.

The context contains:
- Current user information
- Current conversation
- Active task
- Paused tasks
- Current environment
- Relevant memories
- Recent actions
- Pending confirmations

This module deliberately does not execute tools.
It only manages context/state.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


@dataclass
class ConversationMessage:
    """A single conversation message."""

    role: str
    content: str
    timestamp: datetime = field(default_factory=utc_now)
    message_id: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class ActiveTaskContext:
    """Information about the task currently being worked on."""

    task_id: str
    task_type: str
    title: str
    status: str = "active"

    environment_id: Optional[str] = None

    metadata: Dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        return data


@dataclass
class PendingConfirmation:
    """Represents an action waiting for user approval."""

    confirmation_id: str
    action_type: str
    description: str
    risk_level: str

    payload: Dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return data


class AIOSContext:
    """
    Central runtime context for AIOS.

    One context instance represents one active AIOS session.
    """

    def __init__(
        self,
        user_id: str = "local-user",
        session_id: Optional[str] = None,
    ) -> None:
        self.user_id = user_id
        self.session_id = session_id or str(uuid4())

        self.created_at = utc_now()
        self.updated_at = utc_now()

        self.conversation: List[ConversationMessage] = []

        self.active_task: Optional[ActiveTaskContext] = None

        self.paused_tasks: Dict[str, ActiveTaskContext] = {}

        self.current_environment_id: Optional[str] = None

        self.relevant_memories: List[Dict[str, Any]] = []

        self.recent_actions: List[Dict[str, Any]] = []

        self.pending_confirmations: Dict[str, PendingConfirmation] = {}

        self.metadata: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # General context
    # ------------------------------------------------------------------

    def touch(self) -> None:
        """Update context timestamp."""
        self.updated_at = utc_now()

    # ------------------------------------------------------------------
    # Conversation
    # ------------------------------------------------------------------

    def add_message(
        self,
        role: str,
        content: str,
    ) -> ConversationMessage:
        """
        Add a conversation message.

        Supported roles:
        - user
        - assistant
        - system
        - tool
        """

        if not role:
            raise ValueError("Message role cannot be empty.")

        if not content or not content.strip():
            raise ValueError("Message content cannot be empty.")

        message = ConversationMessage(
            role=role,
            content=content.strip(),
        )

        self.conversation.append(message)

        self.touch()

        return message

    def get_recent_messages(
        self,
        limit: int = 20,
    ) -> List[ConversationMessage]:
        """Return the most recent conversation messages."""

        if limit <= 0:
            return []

        return self.conversation[-limit:]

    def get_conversation_text(
        self,
        limit: int = 20,
    ) -> str:
        """Return recent conversation as plain text."""

        messages = self.get_recent_messages(limit)

        return "\n".join(
            f"{message.role}: {message.content}"
            for message in messages
        )

    # ------------------------------------------------------------------
    # Task management
    # ------------------------------------------------------------------

    def start_task(
        self,
        task_type: str,
        title: str,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ActiveTaskContext:
        """
        Start a new task.

        Existing active task is automatically paused.
        """

        if not task_type:
            raise ValueError("task_type cannot be empty.")

        if not title:
            raise ValueError("Task title cannot be empty.")

        if self.active_task is not None:
            self.pause_active_task()

        task = ActiveTaskContext(
            task_id=task_id or str(uuid4()),
            task_type=task_type,
            title=title,
            metadata=metadata or {},
        )

        self.active_task = task

        self.touch()

        return task

    def pause_active_task(self) -> Optional[ActiveTaskContext]:
        """Pause the currently active task."""

        if self.active_task is None:
            return None

        self.active_task.status = "paused"
        self.active_task.touch()

        self.paused_tasks[
            self.active_task.task_id
        ] = self.active_task

        paused = self.active_task

        self.active_task = None

        self.touch()

        return paused

    def resume_task(
        self,
        task_id: str,
    ) -> ActiveTaskContext:
        """Resume a previously paused task."""

        if task_id not in self.paused_tasks:
            raise KeyError(
                f"Paused task '{task_id}' was not found."
            )

        if self.active_task is not None:
            self.pause_active_task()

        task = self.paused_tasks.pop(task_id)

        task.status = "active"
        task.touch()

        self.active_task = task

        self.touch()

        return task

    def complete_active_task(self) -> Optional[ActiveTaskContext]:
        """Mark the active task as completed."""

        if self.active_task is None:
            return None

        self.active_task.status = "completed"
        self.active_task.touch()

        completed = self.active_task

        self.active_task = None

        self.touch()

        return completed

    # ------------------------------------------------------------------
    # Environment
    # ------------------------------------------------------------------

    def set_environment(
        self,
        environment_id: Optional[str],
    ) -> None:
        """Set the currently active environment."""

        self.current_environment_id = environment_id

        if self.active_task is not None:
            self.active_task.environment_id = environment_id
            self.active_task.touch()

        self.touch()

    # ------------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------------

    def set_relevant_memories(
        self,
        memories: List[Dict[str, Any]],
    ) -> None:
        """Replace the memories relevant to the current task."""

        self.relevant_memories = list(memories)

        self.touch()

    def add_memory(
        self,
        memory: Dict[str, Any],
    ) -> None:
        """Add one relevant memory."""

        if not isinstance(memory, dict):
            raise TypeError("Memory must be a dictionary.")

        self.relevant_memories.append(memory)

        self.touch()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def record_action(
        self,
        action: Dict[str, Any],
    ) -> None:
        """Record an action performed during this session."""

        if not isinstance(action, dict):
            raise TypeError("Action must be a dictionary.")

        action_record = dict(action)

        action_record.setdefault(
            "timestamp",
            utc_now().isoformat(),
        )

        self.recent_actions.append(action_record)

        # Keep context memory bounded.
        if len(self.recent_actions) > 100:
            self.recent_actions = self.recent_actions[-100:]

        self.touch()

    # ------------------------------------------------------------------
    # Confirmation
    # ------------------------------------------------------------------

    def add_confirmation(
        self,
        action_type: str,
        description: str,
        risk_level: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> PendingConfirmation:
        """Create a pending user confirmation."""

        confirmation = PendingConfirmation(
            confirmation_id=str(uuid4()),
            action_type=action_type,
            description=description,
            risk_level=risk_level,
            payload=payload or {},
        )

        self.pending_confirmations[
            confirmation.confirmation_id
        ] = confirmation

        self.touch()

        return confirmation

    def consume_confirmation(
        self,
        confirmation_id: str,
    ) -> PendingConfirmation:
        """Remove and return a pending confirmation."""

        if confirmation_id not in self.pending_confirmations:
            raise KeyError(
                f"Confirmation '{confirmation_id}' was not found."
            )

        confirmation = self.pending_confirmations.pop(
            confirmation_id
        )

        self.touch()

        return confirmation

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the complete context."""

        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "conversation": [
                message.to_dict()
                for message in self.conversation
            ],
            "active_task": (
                self.active_task.to_dict()
                if self.active_task
                else None
            ),
            "paused_tasks": {
                task_id: task.to_dict()
                for task_id, task in self.paused_tasks.items()
            },
            "current_environment_id": self.current_environment_id,
            "relevant_memories": self.relevant_memories,
            "recent_actions": self.recent_actions,
            "pending_confirmations": {
                confirmation_id: confirmation.to_dict()
                for confirmation_id, confirmation
                in self.pending_confirmations.items()
            },
            "metadata": self.metadata,
        }

    def clear_session(self) -> None:
        """Clear transient session information."""

        self.conversation.clear()
        self.active_task = None
        self.paused_tasks.clear()
        self.current_environment_id = None
        self.relevant_memories.clear()
        self.recent_actions.clear()
        self.pending_confirmations.clear()

        self.touch()