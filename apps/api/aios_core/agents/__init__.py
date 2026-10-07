"""
AIOS Agents Package

This package contains specialized agents used by the AIOS kernel.

Available agents:
- EmailAgent
- CalendarAgent
- WritingAgent
- CodeAgent
- FileAgent
- SearchAgent
- ReminderAgent
"""

from .base import (
    Agent,
    AgentContext,
    AgentResult,
    AgentStatus,
)

from .email_agent import EmailAgent
from .calendar_agent import CalendarAgent
from .writing_agent import WritingAgent
from .code_agent import CodeAgent
from .file_agent import FileAgent
from .search_agent import SearchAgent
from .reminder_agent import ReminderAgent


__all__ = [
    "Agent",
    "AgentContext",
    "AgentResult",
    "AgentStatus",
    "EmailAgent",
    "CalendarAgent",
    "WritingAgent",
    "CodeAgent",
    "FileAgent",
    "SearchAgent",
    "ReminderAgent",
]