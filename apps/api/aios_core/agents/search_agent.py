"""
AIOS Search Agent.

Provides a provider-independent search abstraction.

No external search API is required for the base implementation.
A real search provider can later be injected through params["provider"].
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from .base import Agent, AgentContext, AgentResult


class SearchAgent(Agent):
    """Specialized agent for information retrieval."""

    name = "search_agent"

    description = (
        "Prepares web and knowledge searches and normalizes search requests."
    )

    capabilities = [
        "web_search",
        "knowledge_search",
        "search_query",
        "research",
        "source_collection",
    ]

    async def run(
        self,
        context: AgentContext,
        params: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:

        params = params or {}

        query = str(
            params.get(
                "query"
            )
            or params.get(
                "text"
            )
            or context.input_text
            or ""
        ).strip()

        if not query:
            return self.needs_input(
                context,
                "What would you like me to search for?",
                ["query"],
            )

        provider = params.get(
            "provider",
            "default",
        )

        search_id = str(uuid.uuid4())

        search_request = {
            "id": search_id,
            "query": query,
            "provider": provider,
            "limit": int(
                params.get(
                    "limit",
                    10,
                )
            ),
            "language": params.get(
                "language",
                context.locale,
            ),
            "safe_search": params.get(
                "safe_search",
                True,
            ),
            "status": "prepared",
        }

        # If a provider callback is supplied, use it.
        provider_callable = params.get(
            "provider_callable"
        )

        if provider_callable is not None:
            try:
                result = provider_callable(
                    search_request
                )

                if hasattr(
                    result,
                    "__await__",
                ):
                    result = await result

                return self.success(
                    context,
                    "Search completed successfully.",
                    {
                        "request": search_request,
                        "results": result,
                    },
                )

            except Exception as exc:
                return self.failure(
                    context,
                    "The configured search provider failed.",
                    error=str(exc),
                )

        return self.success(
            context,
            "Search request prepared.",
            {
                "request": search_request,
                "results": [],
                "provider_status": "provider_not_connected",
            },
        )