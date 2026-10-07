"""
AIOS Email Agent.

This agent handles email-related reasoning and preparation.

External email delivery is intentionally abstracted. By default this agent
creates a structured email operation rather than sending a real email.
A future Gmail/SMTP connector can consume the returned payload.
"""

from __future__ import annotations

import re
import uuid
from typing import Any, Dict, Optional

from .base import Agent, AgentContext, AgentResult, AgentStatus


EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)


class EmailAgent(Agent):
    """Specialized agent for email operations."""

    name = "email_agent"

    description = (
        "Creates, drafts, previews and prepares email operations "
        "for external delivery."
    )

    capabilities = [
        "draft_email",
        "compose_email",
        "extract_email_address",
        "prepare_email",
        "preview_email",
        "send_email_request",
    ]

    def _extract_email(self, text: str) -> Optional[str]:
        """Extract the first email address from text."""
        if not text:
            return None

        match = EMAIL_REGEX.search(text)
        return match.group(0) if match else None

    def _extract_subject(self, text: str) -> str:
        """
        Extract a simple subject from text.

        Supported patterns:
        - subject: Meeting
        - subject Meeting
        - বিষয়: Meeting
        """

        if not text:
            return ""

        patterns = [
            r"(?:subject|বিষয়|বিষয়)\s*[:\-]\s*(.+?)(?:\n|$)",
            r"(?:subject|বিষয়|বিষয়)\s+(.+?)(?:\n|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return ""

    def _extract_body(self, text: str) -> str:
        """Extract an explicitly provided email body."""

        if not text:
            return ""

        body_match = re.search(
            r"(?:body|message|content|বার্তা|মেসেজ)\s*[:\-]\s*(.+)",
            text,
            re.IGNORECASE | re.DOTALL,
        )

        if body_match:
            return body_match.group(1).strip()

        return ""

    async def run(
        self,
        context: AgentContext,
        params: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:

        params = params or {}

        operation = str(
            params.get("operation", "draft")
        ).strip().lower()

        raw_text = str(
            params.get("text")
            or context.input_text
            or ""
        ).strip()

        recipient = (
            params.get("recipient")
            or params.get("to")
            or self._extract_email(raw_text)
        )

        subject = (
            params.get("subject")
            or self._extract_subject(raw_text)
            or "AIOS Email"
        )

        body = (
            params.get("body")
            or self._extract_body(raw_text)
        )

        if operation in {"draft", "compose", "prepare", "preview"}:
            if not recipient:
                return self.needs_input(
                    context,
                    "Who should receive the email?",
                    ["recipient"],
                )

            draft_id = str(uuid.uuid4())

            email = {
                "id": draft_id,
                "to": recipient,
                "subject": subject,
                "body": body,
                "status": "draft",
                "created_by": self.name,
            }

            context.set("current_email_draft", email)

            return self.success(
                context,
                "Email draft prepared successfully.",
                {
                    "operation": "draft",
                    "email": email,
                    "ready_for_review": True,
                },
                rollback_supported=True,
                rollback_token=draft_id,
            )

        if operation == "send":
            if not recipient:
                return self.needs_input(
                    context,
                    "An email recipient is required before sending.",
                    ["recipient"],
                )

            if not body:
                return self.needs_input(
                    context,
                    "Email body is required before sending.",
                    ["body"],
                )

            email = {
                "id": str(uuid.uuid4()),
                "to": recipient,
                "subject": subject,
                "body": body,
                "status": "ready_for_delivery",
                "delivery_mode": "external_connector_required",
            }

            return self.needs_confirmation(
                context,
                "The email is ready to be sent.",
                "Sending an email creates an external side effect.",
                {
                    "operation": "send",
                    "email": email,
                    "external_delivery_required": True,
                },
            )

        return self.failure(
            context,
            f"Unsupported email operation: {operation}",
            error="unsupported_operation",
        )