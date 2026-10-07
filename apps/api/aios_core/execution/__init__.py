"""
AIOS Execution Layer.

The execution layer is responsible for:

- Representing executable actions
- Validating actions
- Running actions safely
- Providing sandbox boundaries
- Returning structured execution results
"""

from .action import (
    Action,
    ActionDefinition,
    ActionStatus,
)

from .result import (
    ExecutionResult,
    ExecutionStatus,
)

from .sandbox import (
    Sandbox,
    SandboxConfig,
    SandboxViolation,
)

from .validator import (
    ActionValidator,
    ValidationResult,
)

from .engine import (
    ExecutionEngine,
    ExecutionEngineConfig,
)


__all__ = [
    "Action",
    "ActionDefinition",
    "ActionStatus",
    "ExecutionResult",
    "ExecutionStatus",
    "Sandbox",
    "SandboxConfig",
    "SandboxViolation",
    "ActionValidator",
    "ValidationResult",
    "ExecutionEngine",
    "ExecutionEngineConfig",
]