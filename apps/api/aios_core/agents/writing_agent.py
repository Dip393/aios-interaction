"""
AIOS Writing Agent.

Handles document and text-generation workflows at the agent layer.

Actual LLM generation can later be connected through the AIOS model layer.
The current implementation provides deterministic fallback behavior so the
system remains runnable without paid APIs.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from .base import Agent, AgentContext, AgentResult


class WritingAgent(Agent):
    """Specialized agent for writing and document content."""

    name = "writing_agent"

    description = (
        "Creates, edits, rewrites and structures written content."
    )

    capabilities = [
        "write",
        "draft",
        "rewrite",
        "summarize",
        "expand",
        "document_content",
        "story_writing",
        "email_writing",
    ]

    def _fallback_generate(
        self,
        task: str,
        topic: str,
        style: str,
        language: str,
    ) -> str:
        """
        Generate a deterministic fallback response.

        This is intentionally not presented as a real LLM. It provides
        structured content until an LLM provider is connected.
        """

        if task == "rewrite":
            return (
                f"[AIOS writing draft]\n\n"
                f"Rewritten version of:\n{topic}"
            )

        if task == "summarize":
            return (
                f"[AIOS summary]\n\n"
                f"Summary requested for:\n{topic}"
            )

        if task == "expand":
            return (
                f"[AIOS expanded draft]\n\n"
                f"Topic: {topic}\n"
                f"Style: {style}\n"
                f"Language: {language}\n\n"
                f"This section is prepared as a structured writing "
                f"placeholder for the connected language model."
            )

        return (
            f"[AIOS generated draft]\n\n"
            f"Topic: {topic}\n"
            f"Style: {style}\n"
            f"Language: {language}\n\n"
            f"This draft is ready for the AIOS language-generation "
            f"provider to refine or replace."
        )

    async def run(
        self,
        context: AgentContext,
        params: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:

        params = params or {}

        task = str(
            params.get("task")
            or params.get("operation")
            or "write"
        ).lower()

        topic = str(
            params.get("topic")
            or params.get("content")
            or params.get("text")
            or context.input_text
            or ""
        ).strip()

        if not topic:
            return self.needs_input(
                context,
                "What would you like me to write?",
                ["topic"],
            )

        style = str(
            params.get("style", "natural")
        )

        language = str(
            params.get(
                "language",
                context.locale or "en-IN",
            )
        )

        content = params.get("generated_content")

        if not content:
            content = self._fallback_generate(
                task=task,
                topic=topic,
                style=style,
                language=language,
            )

        document_id = str(uuid.uuid4())

        document = {
            "id": document_id,
            "type": params.get(
                "document_type",
                "text",
            ),
            "title": params.get(
                "title",
                "AIOS Document",
            ),
            "content": content,
            "task": task,
            "style": style,
            "language": language,
            "status": "draft",
        }

        context.set(
            "current_document",
            document,
        )

        return self.success(
            context,
            "Writing draft prepared successfully.",
            {
                "document": document,
                "llm_provider": (
                    "external_provider_not_connected"
                    if not params.get("generated_content")
                    else "provided_content"
                ),
            },
            rollback_supported=True,
            rollback_token=document_id,
        )