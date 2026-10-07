"""
AIOS Intent Engine

Converts natural-language user requests into structured intents.

The intent layer does NOT execute actions.

Its responsibility is to answer:

    What does the user want?

Examples:

"Email Rahul tomorrow's meeting details."

becomes:

{
    "name": "send_email",
    "domain": "communication",
    "entities": {
        "recipient": "Rahul",
        "message": "...",
        "event": "meeting"
    }
}

This module contains deterministic intent detection as a fallback.
The LLM planner can later enrich or replace parts of this process.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class IntentEntity:
    """A detected entity inside a user request."""

    name: str
    value: Any
    confidence: float = 1.0
    source: str = "rule"


@dataclass
class UserIntent:
    """Structured representation of a user request."""

    name: str
    domain: str

    confidence: float = 0.0

    entities: Dict[str, Any] = field(default_factory=dict)

    parameters: Dict[str, Any] = field(default_factory=dict)

    requested_actions: List[str] = field(default_factory=list)

    requires_confirmation: bool = False

    raw_text: str = ""

    created_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return data


class IntentEngine:
    """Detects the primary intent of a natural-language command."""

    def __init__(self) -> None:
        self._patterns = [
            (
                "send_email",
                "communication",
                [
                    r"\b(send|email|mail)\b",
                ],
            ),
            (
                "write_email",
                "communication",
                [
                    r"\b(write|draft|compose)\b.*\b(email|mail)\b",
                ],
            ),
            (
                "create_reminder",
                "productivity",
                [
                    r"\b(remind|reminder|remember me)\b",
                    r"\balarm\b",
                ],
            ),
            (
                "schedule_event",
                "calendar",
                [
                    r"\b(schedule|book|create)\b.*\b(meeting|event|appointment)\b",
                ],
            ),
            (
                "write_content",
                "writing",
                [
                    r"\b(write|draft|create)\b.*\b(story|article|essay|poem|document)\b",
                ],
            ),
            (
                "create_code",
                "development",
                [
                    r"\b(create|write|build|make)\b.*\b(code|app|application|website|project)\b",
                    r"\bpython\b",
                    r"\bjavascript\b",
                    r"\btypescript\b",
                    r"\breact\b",
                ],
            ),
            (
                "search_web",
                "research",
                [
                    r"\b(search|find|look up|research)\b",
                ],
            ),
            (
                "create_file",
                "files",
                [
                    r"\b(create|make|generate)\b.*\b(file|folder|document)\b",
                ],
            ),
        ]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(
        self,
        text: str,
    ) -> UserIntent:
        """
        Detect the user's primary intent.

        This method is deterministic and works without an LLM.
        """

        normalized = self._normalize(text)

        if not normalized:
            return UserIntent(
                name="unknown",
                domain="general",
                confidence=0.0,
                raw_text=text,
            )

        detected = self._detect_intent(normalized)

        entities = self._extract_entities(
            normalized
        )

        requested_actions = self._infer_actions(
            detected[0]
        )

        requires_confirmation = (
            detected[0]
            in {
                "send_email",
                "schedule_event",
                "create_file",
            }
        )

        return UserIntent(
            name=detected[0],
            domain=detected[1],
            confidence=detected[2],
            entities=entities,
            requested_actions=requested_actions,
            requires_confirmation=requires_confirmation,
            raw_text=text,
        )

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(
            r"\s+",
            " ",
            text.strip().lower(),
        )

    # ------------------------------------------------------------------
    # Intent detection
    # ------------------------------------------------------------------

    def _detect_intent(
        self,
        text: str,
    ) -> tuple[str, str, float]:
        best_name = "general_chat"
        best_domain = "general"
        best_score = 0.1

        for name, domain, patterns in self._patterns:
            score = 0.0

            for pattern in patterns:
                if re.search(pattern, text):
                    score += 0.5

            score = min(score, 1.0)

            if score > best_score:
                best_name = name
                best_domain = domain
                best_score = score

        return best_name, best_domain, best_score

    # ------------------------------------------------------------------
    # Entity extraction
    # ------------------------------------------------------------------

    def _extract_entities(
        self,
        text: str,
    ) -> Dict[str, Any]:
        entities: Dict[str, Any] = {}

        recipient = self._extract_recipient(text)

        if recipient:
            entities["recipient"] = recipient

        email = self._extract_email(text)

        if email:
            entities["email"] = email

        date_info = self._extract_date(text)

        if date_info:
            entities["date"] = date_info

        time_info = self._extract_time(text)

        if time_info:
            entities["time"] = time_info

        event = self._extract_event(text)

        if event:
            entities["event"] = event

        return entities

    @staticmethod
    def _extract_recipient(
        text: str,
    ) -> Optional[str]:
        patterns = [
            r"\bto\s+([a-z][a-z .'-]{1,50}?)(?:\s+(?:a|an|the|about|for|regarding)\b|[,.!?]|$)",
            r"\b([a-z][a-z .'-]{1,50}?)\s+কে\b",
            r"\bemail\s+([a-z][a-z .'-]{1,50}?)(?:\s|$)",
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if match:
                value = match.group(1).strip()

                value = re.sub(
                    r"\s+",
                    " ",
                    value,
                )

                if value:
                    return value

        return None

    @staticmethod
    def _extract_email(
        text: str,
    ) -> Optional[str]:
        match = re.search(
            r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
            text,
            re.IGNORECASE,
        )

        return match.group(0) if match else None

    @staticmethod
    def _extract_date(
        text: str,
    ) -> Optional[Dict[str, Any]]:
        today = datetime.now(timezone.utc).date()

        if "tomorrow" in text or "আগামীকাল" in text:
            target = today + timedelta(days=1)

            return {
                "label": "tomorrow",
                "date": target.isoformat(),
            }

        if "today" in text or "আজ" in text:
            return {
                "label": "today",
                "date": today.isoformat(),
            }

        if "day after tomorrow" in text:
            target = today + timedelta(days=2)

            return {
                "label": "day_after_tomorrow",
                "date": target.isoformat(),
            }

        return None

    @staticmethod
    def _extract_time(
        text: str,
    ) -> Optional[Dict[str, Any]]:
        match = re.search(
            r"\b(?:at|@)\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b",
            text,
            re.IGNORECASE,
        )

        if not match:
            return None

        hour = int(match.group(1))
        minute = int(match.group(2) or 0)

        meridiem = match.group(3)

        if meridiem:
            meridiem = meridiem.lower()

            if meridiem == "pm" and hour < 12:
                hour += 12

            if meridiem == "am" and hour == 12:
                hour = 0

        if hour > 23 or minute > 59:
            return None

        return {
            "hour": hour,
            "minute": minute,
            "formatted": f"{hour:02d}:{minute:02d}",
        }

    @staticmethod
    def _extract_event(
        text: str,
    ) -> Optional[str]:
        event_keywords = [
            "meeting",
            "appointment",
            "interview",
            "class",
            "exam",
            "deadline",
            "call",
            "মিটিং",
        ]

        for keyword in event_keywords:
            if keyword in text:
                return keyword

        return None

    # ------------------------------------------------------------------
    # Action inference
    # ------------------------------------------------------------------

    @staticmethod
    def _infer_actions(
        intent_name: str,
    ) -> List[str]:
        mapping = {
            "send_email": [
                "resolve_contact",
                "compose_email",
                "request_confirmation",
                "send_email",
                "extract_events",
                "store_memory",
            ],
            "write_email": [
                "compose_email",
            ],
            "create_reminder": [
                "create_reminder",
                "store_memory",
            ],
            "schedule_event": [
                "create_calendar_event",
                "create_reminder",
                "store_memory",
            ],
            "write_content": [
                "create_writing_environment",
                "generate_writing_assistance",
            ],
            "create_code": [
                "create_coding_environment",
                "generate_code",
                "run_tests",
                "verify_result",
            ],
            "search_web": [
                "search_web",
                "summarize_results",
            ],
            "create_file": [
                "create_file",
                "verify_file",
            ],
            "general_chat": [
                "respond",
            ],
            "unknown": [
                "request_clarification",
            ],
        }

        return list(
            mapping.get(
                intent_name,
                ["respond"],
            )
        )