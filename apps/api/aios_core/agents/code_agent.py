"""
AIOS Code Agent.

Handles software-development tasks such as:
- project planning
- code generation requests
- file structures
- test planning
- code modification requests

No shell command is executed by this agent.
Actual execution belongs to a controlled action/sandbox layer.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from .base import Agent, AgentContext, AgentResult


class CodeAgent(Agent):
    """Specialized agent for coding and software development tasks."""

    name = "code_agent"

    description = (
        "Plans software projects, generates code structures and prepares "
        "development operations."
    )

    capabilities = [
        "generate_code",
        "create_project",
        "project_structure",
        "modify_code",
        "test_planning",
        "code_review",
    ]

    def _default_structure(
        self,
        project_type: str,
    ) -> List[str]:
        """Return a minimal project structure."""

        normalized = project_type.lower()

        if normalized in {"python", "python_app"}:
            return [
                "app/",
                "app/__init__.py",
                "app/main.py",
                "tests/",
                "tests/test_main.py",
                "requirements.txt",
                "README.md",
                ".gitignore",
            ]

        if normalized in {
            "react",
            "react_app",
            "frontend",
        }:
            return [
                "src/",
                "src/main.jsx",
                "src/App.jsx",
                "src/components/",
                "public/",
                "package.json",
                "vite.config.js",
                "index.html",
                "README.md",
            ]

        if normalized in {
            "node",
            "node_api",
            "express",
        }:
            return [
                "src/",
                "src/server.js",
                "src/routes/",
                "src/controllers/",
                "src/services/",
                "package.json",
                ".env.example",
                "README.md",
            ]

        return [
            "src/",
            "tests/",
            "README.md",
            ".gitignore",
        ]

    async def run(
        self,
        context: AgentContext,
        params: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:

        params = params or {}

        operation = str(
            params.get(
                "operation",
                "generate",
            )
        ).lower()

        project_name = str(
            params.get(
                "project_name",
                "aios-project",
            )
        )

        project_type = str(
            params.get(
                "project_type",
                "generic",
            )
        )

        description = str(
            params.get(
                "description"
            )
            or params.get(
                "prompt"
            )
            or context.input_text
            or ""
        ).strip()

        if not description:
            return self.needs_input(
                context,
                "Please describe what you want the code or project to do.",
                ["description"],
            )

        if operation == "create_project":
            project_id = str(uuid.uuid4())

            structure = params.get(
                "structure"
            ) or self._default_structure(
                project_type
            )

            project = {
                "id": project_id,
                "name": project_name,
                "type": project_type,
                "description": description,
                "structure": structure,
                "status": "planned",
            }

            context.set(
                "current_project",
                project,
            )

            return self.success(
                context,
                "Project structure prepared successfully.",
                {
                    "project": project,
                },
                rollback_supported=True,
                rollback_token=project_id,
            )

        if operation in {
            "generate",
            "generate_code",
            "write_code",
        }:
            code_id = str(uuid.uuid4())

            files = params.get("files", [])

            if not files:
                files = [
                    {
                        "path": "src/main.py",
                        "content": (
                            "# AIOS generated code placeholder\n"
                            f"# Project: {project_name}\n"
                            f"# Task: {description}\n"
                        ),
                    }
                ]

            result = {
                "id": code_id,
                "project_name": project_name,
                "description": description,
                "language": params.get(
                    "language",
                    "auto",
                ),
                "files": files,
                "status": "generated",
                "execution_required": False,
            }

            context.set(
                "current_code_generation",
                result,
            )

            return self.success(
                context,
                "Code generation result prepared.",
                {
                    "code": result,
                    "llm_provider": (
                        "external_code_model_not_connected"
                        if not params.get("files")
                        else "provided_code"
                    ),
                },
                rollback_supported=True,
                rollback_token=code_id,
            )

        if operation in {
            "review",
            "code_review",
        }:
            return self.success(
                context,
                "Code review request prepared.",
                {
                    "review_target": params.get(
                        "code"
                    ) or description,
                    "checks": [
                        "correctness",
                        "security",
                        "performance",
                        "maintainability",
                        "style",
                    ],
                },
            )

        if operation in {
            "test",
            "test_plan",
        }:
            return self.success(
                context,
                "Test plan prepared.",
                {
                    "test_plan": [
                        "unit tests",
                        "integration tests",
                        "edge cases",
                        "error handling",
                    ],
                },
            )

        return self.failure(
            context,
            f"Unsupported code operation: {operation}",
            error="unsupported_operation",
        )