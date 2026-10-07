"""
AIOS File Agent.

Handles file-oriented reasoning and virtual file operations.

The agent does not directly execute arbitrary filesystem commands.
Actual filesystem access should happen through a controlled action/sandbox
layer with policy enforcement.
"""

from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List, Optional

from .base import Agent, AgentContext, AgentResult


class FileAgent(Agent):
    """Specialized agent for file and document operations."""

    name = "file_agent"

    description = (
        "Prepares safe file operations such as create, read, update, "
        "rename and organize."
    )

    capabilities = [
        "create_file",
        "read_file",
        "write_file",
        "rename_file",
        "delete_file",
        "list_files",
        "organize_files",
    ]

    def _normalize_path(self, path: str) -> str:
        """Normalize a virtual file path."""

        path = str(path or "").strip()

        if not path:
            return ""

        path = path.replace("\\", "/")

        while "//" in path:
            path = path.replace("//", "/")

        return path

    async def run(
        self,
        context: AgentContext,
        params: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:

        params = params or {}

        operation = str(
            params.get(
                "operation",
                "create",
            )
        ).lower()

        path = self._normalize_path(
            params.get(
                "path",
                "",
            )
        )

        if operation in {
            "create",
            "write",
            "update",
        } and not path:
            return self.needs_input(
                context,
                "Which file should be created or updated?",
                ["path"],
            )

        if operation == "create":
            file_id = str(uuid.uuid4())

            virtual_file = {
                "id": file_id,
                "path": path,
                "name": os.path.basename(path),
                "content": params.get(
                    "content",
                    "",
                ),
                "operation": "create",
                "status": "prepared",
                "storage": "virtual",
            }

            return self.success(
                context,
                f"File creation prepared for '{path}'.",
                {
                    "file": virtual_file,
                },
                rollback_supported=True,
                rollback_token=file_id,
            )

        if operation in {
            "write",
            "update",
        }:
            file_id = str(uuid.uuid4())

            virtual_file = {
                "id": file_id,
                "path": path,
                "content": params.get(
                    "content",
                    "",
                ),
                "operation": operation,
                "status": "prepared",
                "storage": "virtual",
            }

            return self.success(
                context,
                f"File update prepared for '{path}'.",
                {
                    "file": virtual_file,
                },
                rollback_supported=True,
                rollback_token=file_id,
            )

        if operation == "read":
            if not path:
                return self.needs_input(
                    context,
                    "Which file should be read?",
                    ["path"],
                )

            return self.success(
                context,
                f"File read request prepared for '{path}'.",
                {
                    "path": path,
                    "storage": "controlled_filesystem_required",
                },
            )

        if operation == "rename":
            old_path = self._normalize_path(
                params.get(
                    "old_path",
                    "",
                )
            )

            new_path = self._normalize_path(
                params.get(
                    "new_path",
                    "",
                )
            )

            if not old_path or not new_path:
                return self.needs_input(
                    context,
                    "Both the old and new file paths are required.",
                    [
                        "old_path",
                        "new_path",
                    ],
                )

            return self.success(
                context,
                "File rename operation prepared.",
                {
                    "old_path": old_path,
                    "new_path": new_path,
                    "status": "prepared",
                },
            )

        if operation == "delete":
            if not path:
                return self.needs_input(
                    context,
                    "Which file should be deleted?",
                    ["path"],
                )

            return self.needs_confirmation(
                context,
                f"File deletion prepared for '{path}'.",
                "Deleting a file is a destructive filesystem operation.",
                {
                    "path": path,
                    "operation": "delete",
                },
            )

        if operation in {
            "list",
            "list_files",
        }:
            directory = self._normalize_path(
                params.get(
                    "directory",
                    ".",
                )
            )

            return self.success(
                context,
                "File listing request prepared.",
                {
                    "directory": directory,
                    "storage": "controlled_filesystem_required",
                },
            )

        if operation in {
            "organize",
            "move",
        }:
            return self.success(
                context,
                "File organization operation prepared.",
                {
                    "source": self._normalize_path(
                        params.get(
                            "source",
                            "",
                        )
                    ),
                    "destination": self._normalize_path(
                        params.get(
                            "destination",
                            "",
                        )
                    ),
                    "status": "prepared",
                },
            )

        return self.failure(
            context,
            f"Unsupported file operation: {operation}",
            error="unsupported_operation",
        )