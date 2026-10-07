from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Common models
# ============================================================================

class AIOSBaseModel(BaseModel):
    """
    Base Pydantic model used across the AIOS API.

    Extra fields are ignored by default so that frontend versions can evolve
    without immediately breaking the backend.
    """

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )


# ============================================================================
# Kernel
# ============================================================================

class CommandRequest(AIOSBaseModel):
    """
    Legacy / simplified command request.

    Used by:
        POST /api/command
    """

    text: str = Field(
        ...,
        min_length=1,
        description="Natural-language user command.",
    )

    confirm: bool = False


class KernelProcessRequest(AIOSBaseModel):
    """
    Request sent to the AIOS kernel.
    """

    input: str = Field(
        ...,
        min_length=1,
        description="Natural-language input.",
    )

    session_id: Optional[str] = None
    user_id: Optional[str] = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class KernelConfirmationRequest(AIOSBaseModel):
    """
    Confirmation/rejection of a pending kernel action.
    """

    confirmation_id: Optional[str] = None
    action_id: Optional[str] = None

    approved: bool

    session_id: Optional[str] = None
    reason: Optional[str] = None


# ============================================================================
# Task models
# ============================================================================

TaskStatus = Literal[
    "pending",
    "queued",
    "active",
    "running",
    "paused",
    "completed",
    "failed",
    "cancelled",
]

TaskPriority = Literal[
    "low",
    "medium",
    "high",
    "critical",
]


class TaskCreate(AIOSBaseModel):
    """
    Create a task in the AIOS task system.
    """

    title: str = Field(
        ...,
        min_length=1,
    )

    kind: str = "general"

    status: TaskStatus = "pending"

    state: dict[str, Any] = Field(
        default_factory=dict,
    )

    priority: TaskPriority = "medium"

    environment_id: Optional[str] = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class TaskUpdate(AIOSBaseModel):
    """
    Update task status/state.

    Kept compatible with the original API model while supporting the newer
    task lifecycle.
    """

    status: Optional[TaskStatus] = None

    title: Optional[str] = None

    state: Optional[dict[str, Any]] = None

    priority: Optional[TaskPriority] = None

    environment_id: Optional[str] = None

    metadata: Optional[dict[str, Any]] = None


class TaskActionRequest(AIOSBaseModel):
    """
    Generic request for task actions such as complete/cancel/pause/resume.
    """

    reason: Optional[str] = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================================
# Agent models
# ============================================================================

class AgentExecuteRequest(AIOSBaseModel):
    """
    Generic request for executing an AIOS agent.
    """

    input: str = Field(
        ...,
        min_length=1,
    )

    session_id: Optional[str] = None
    task_id: Optional[str] = None

    parameters: dict[str, Any] = Field(
        default_factory=dict,
    )

    confirm: bool = False


# ============================================================================
# Email
# ============================================================================

class EmailRequest(AIOSBaseModel):
    """
    Email action request.

    External sending remains confirmation/policy controlled.
    """

    to: str = Field(
        ...,
        min_length=1,
    )

    subject: str = ""

    body: str = ""

    cc: Optional[str] = None
    bcc: Optional[str] = None

    confirm: bool = False

    task_id: Optional[str] = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class EmailDraftRequest(AIOSBaseModel):
    """
    Create or update an email draft without sending it.
    """

    to: Optional[str] = None
    cc: Optional[str] = None
    bcc: Optional[str] = None

    subject: str = ""
    body: str = ""

    task_id: Optional[str] = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================================
# Reminder models
# ============================================================================

ReminderStatus = Literal[
    "pending",
    "scheduled",
    "active",
    "completed",
    "cancelled",
    "expired",
    "failed",
]


class ReminderRequest(AIOSBaseModel):
    """
    Create a reminder.

    `due_at` is kept as a string because the existing database layer stores
    timestamps as ISO-8601 text.
    """

    title: str = Field(
        ...,
        min_length=1,
    )

    due_at: str

    description: Optional[str] = None

    event_id: Optional[int] = None

    priority: TaskPriority = "medium"

    recurring: bool = False

    recurrence: Optional[str] = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class ReminderUpdate(AIOSBaseModel):
    """
    Update reminder information.
    """

    title: Optional[str] = None

    description: Optional[str] = None

    due_at: Optional[str] = None

    status: Optional[ReminderStatus] = None

    priority: Optional[TaskPriority] = None

    recurring: Optional[bool] = None

    recurrence: Optional[str] = None

    metadata: Optional[dict[str, Any]] = None


# ============================================================================
# Contact models
# ============================================================================

class ContactCreate(AIOSBaseModel):
    """
    Create a contact.
    """

    name: str = Field(
        ...,
        min_length=1,
    )

    email: Optional[str] = None

    phone: Optional[str] = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class ContactUpdate(AIOSBaseModel):
    """
    Update an existing contact.
    """

    name: Optional[str] = None

    email: Optional[str] = None

    phone: Optional[str] = None

    metadata: Optional[dict[str, Any]] = None


# ============================================================================
# Workspace / Environment models
# ============================================================================

class WorkspaceRequest(AIOSBaseModel):
    """
    Legacy workspace request.

    AIOS environments supersede the old workspace concept, but this model
    remains for backward compatibility.
    """

    kind: str

    title: str

    state: dict[str, Any] = Field(
        default_factory=dict,
    )


class EnvironmentCreateRequest(AIOSBaseModel):
    """
    Create a dynamic AIOS environment.
    """

    type: str = Field(
        ...,
        min_length=1,
    )

    name: Optional[str] = None

    description: Optional[str] = None

    config: dict[str, Any] = Field(
        default_factory=dict,
    )

    data: dict[str, Any] = Field(
        default_factory=dict,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class EnvironmentDataRequest(AIOSBaseModel):
    """
    Update environment data.
    """

    data: dict[str, Any] = Field(
        default_factory=dict,
    )


class EnvironmentStateRequest(AIOSBaseModel):
    """
    Replace/update environment state.
    """

    state: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================================
# Memory models
# ============================================================================

MemoryCategory = Literal[
    "context",
    "preference",
    "fact",
    "communication",
    "event",
    "reminder",
    "task",
    "project",
    "user",
    "system",
    "general",
]


class RememberRequest(AIOSBaseModel):
    """
    Store information in long-term memory.
    """

    content: str = Field(
        ...,
        min_length=1,
    )

    category: str = "general"

    importance: int = Field(
        default=1,
        ge=0,
        le=10,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class RecentMemoryRequest(AIOSBaseModel):
    """
    Add information to short-term memory.
    """

    content: str = Field(
        ...,
        min_length=1,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class SemanticRequest(AIOSBaseModel):
    """
    Store a semantic memory.
    """

    content: str = Field(
        ...,
        min_length=1,
    )

    category: Optional[str] = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class SemanticSearchRequest(AIOSBaseModel):
    """
    Search semantic memory.
    """

    query: str = Field(
        ...,
        min_length=1,
    )

    limit: int = Field(
        default=10,
        ge=1,
        le=100,
    )


class TaskMemoryRequest(AIOSBaseModel):
    """
    Create working memory for a task.
    """

    task_id: str = Field(
        ...,
        min_length=1,
    )

    initial_data: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================================
# Voice models
# ============================================================================

class VoiceSessionRequest(AIOSBaseModel):
    """
    Start/stop a voice session.
    """

    session_id: str = Field(
        ...,
        min_length=1,
    )


class VoiceTranscriptionRequest(AIOSBaseModel):
    """
    Text/audio transcription metadata.

    Actual binary audio uploads are handled separately by the FastAPI route.
    """

    session_id: Optional[str] = None

    language: Optional[str] = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class VoiceSpeakRequest(AIOSBaseModel):
    """
    Text-to-speech request.
    """

    text: str = Field(
        ...,
        min_length=1,
    )

    session_id: Optional[str] = None

    voice: Optional[str] = None

    language: Optional[str] = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class VoiceProcessRequest(AIOSBaseModel):
    """
    Complete voice → AIOS processing request.
    """

    text: str = Field(
        ...,
        min_length=1,
    )

    session_id: Optional[str] = None

    user_id: Optional[str] = None

    speak_response: bool = False

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================================
# Vision models
# ============================================================================

class VisionLandmark(BaseModel):
    """
    A normalized 3D hand landmark.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    x: float
    y: float
    z: float = 0.0


class VisionHand(BaseModel):
    """
    Hand data sent from frontend/browser vision processing.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    id: str = "hand"

    handedness: Optional[str] = None

    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
    )

    landmarks: list[VisionLandmark] = Field(
        default_factory=list,
    )


class VisionFrameRequest(AIOSBaseModel):
    """
    Vision frame processing request.
    """

    session_id: str = Field(
        ...,
        min_length=1,
    )

    hands: list[VisionHand] = Field(
        default_factory=list,
    )

    timestamp: Optional[float] = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================================
# Rollback models
# ============================================================================

class SnapshotRequest(AIOSBaseModel):
    """
    Create a rollback/checkpoint snapshot.
    """

    task_id: Optional[str] = None

    name: Optional[str] = None

    snapshot_type: str = "checkpoint"

    state: dict[str, Any] = Field(
        default_factory=dict,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class RestoreRequest(AIOSBaseModel):
    """
    Restore a snapshot.
    """

    snapshot_id: str = Field(
        ...,
        min_length=1,
    )

    target_task_id: Optional[str] = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================================
# Connector models
# ============================================================================

class ConnectorExecuteRequest(AIOSBaseModel):
    """
    Generic connector execution request.
    """

    action: str = Field(
        ...,
        min_length=1,
    )

    parameters: dict[str, Any] = Field(
        default_factory=dict,
    )

    confirm: bool = False

    task_id: Optional[str] = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class ConnectorConfigRequest(AIOSBaseModel):
    """
    Connector configuration request.

    Secrets should normally be supplied through environment variables or
    secure credential storage rather than persisted directly here.
    """

    config: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================================
# API session models
# ============================================================================

class SessionRequest(AIOSBaseModel):
    """
    Create/update an AIOS API session.
    """

    session_id: Optional[str] = None

    user_id: Optional[str] = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Common
    "AIOSBaseModel",

    # Kernel
    "CommandRequest",
    "KernelProcessRequest",
    "KernelConfirmationRequest",

    # Tasks
    "TaskStatus",
    "TaskPriority",
    "TaskCreate",
    "TaskUpdate",
    "TaskActionRequest",

    # Agents
    "AgentExecuteRequest",

    # Email
    "EmailRequest",
    "EmailDraftRequest",

    # Reminders
    "ReminderStatus",
    "ReminderRequest",
    "ReminderUpdate",

    # Contacts
    "ContactCreate",
    "ContactUpdate",

    # Environment
    "WorkspaceRequest",
    "EnvironmentCreateRequest",
    "EnvironmentDataRequest",
    "EnvironmentStateRequest",

    # Memory
    "MemoryCategory",
    "RememberRequest",
    "RecentMemoryRequest",
    "SemanticRequest",
    "SemanticSearchRequest",
    "TaskMemoryRequest",

    # Voice
    "VoiceSessionRequest",
    "VoiceTranscriptionRequest",
    "VoiceSpeakRequest",
    "VoiceProcessRequest",

    # Vision
    "VisionLandmark",
    "VisionHand",
    "VisionFrameRequest",

    # Rollback
    "SnapshotRequest",
    "RestoreRequest",

    # Connectors
    "ConnectorExecuteRequest",
    "ConnectorConfigRequest",

    # Sessions
    "SessionRequest",
]