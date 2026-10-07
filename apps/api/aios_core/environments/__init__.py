"""
AIOS Environment Layer.

Environments represent dynamic workspaces created by AIOS for different
user tasks.

Examples:
- writing environment
- email environment
- coding environment
- file management environment
- research environment
- calendar environment
"""

from .schemas import (
    Environment,
    EnvironmentConfig,
    EnvironmentType,
    EnvironmentStatus,
    EnvironmentCapability,
)

from .state import (
    EnvironmentState,
    EnvironmentStateStore,
)

from .registry import (
    EnvironmentRegistry,
)

from .templates import (
    EnvironmentTemplate,
    EnvironmentTemplateRegistry,
    create_default_template_registry,
)

from .manager import (
    EnvironmentManager,
)


__all__ = [
    "Environment",
    "EnvironmentConfig",
    "EnvironmentType",
    "EnvironmentStatus",
    "EnvironmentCapability",
    "EnvironmentState",
    "EnvironmentStateStore",
    "EnvironmentRegistry",
    "EnvironmentTemplate",
    "EnvironmentTemplateRegistry",
    "create_default_template_registry",
    "EnvironmentManager",
]