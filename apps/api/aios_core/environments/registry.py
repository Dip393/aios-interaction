"""
AIOS Environment Registry.

Maintains the collection of environments known to the AIOS runtime.
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from .schemas import (
    Environment,
    EnvironmentStatus,
    EnvironmentType,
)


class EnvironmentRegistry:
    """Thread-safe environment registry."""

    def __init__(self) -> None:

        self._environments: Dict[
            str,
            Environment,
        ] = {}

        self._lock = threading.RLock()

    def register(
        self,
        environment: Environment,
    ) -> Environment:
        """Register an environment."""

        if not isinstance(
            environment,
            Environment,
        ):
            raise TypeError(
                "environment must be an Environment."
            )

        with self._lock:
            self._environments[
                environment.id
            ] = environment

        return environment

    def unregister(
        self,
        environment_id: str,
    ) -> bool:
        """Remove an environment."""

        with self._lock:
            return (
                self._environments.pop(
                    environment_id,
                    None,
                )
                is not None
            )

    def get(
        self,
        environment_id: str,
    ) -> Optional[
        Environment
    ]:
        """Get an environment."""

        with self._lock:
            return self._environments.get(
                environment_id
            )

    def require(
        self,
        environment_id: str,
    ) -> Environment:
        """Get an environment or raise an error."""

        environment = self.get(
            environment_id
        )

        if environment is None:
            raise KeyError(
                f"Environment '{environment_id}' "
                "does not exist."
            )

        return environment

    def find_by_name(
        self,
        name: str,
    ) -> Optional[
        Environment
    ]:
        """Find environment by name."""

        normalized = name.strip().lower()

        with self._lock:

            for environment in (
                self._environments.values()
            ):
                if (
                    environment.name.lower()
                    == normalized
                ):
                    return environment

        return None

    def find_by_type(
        self,
        environment_type: EnvironmentType,
    ) -> List[
        Environment
    ]:
        """Find environments by type."""

        with self._lock:

            return [
                environment
                for environment
                in self._environments.values()
                if (
                    environment.environment_type
                    == environment_type
                )
            ]

    def find_by_session(
        self,
        session_id: str,
    ) -> List[
        Environment
    ]:
        """Find environments belonging to a session."""

        with self._lock:

            return [
                environment
                for environment
                in self._environments.values()
                if (
                    environment.session_id
                    == session_id
                )
            ]

    def find_active(
        self,
    ) -> List[
        Environment
    ]:
        """Return active environments."""

        return self.find_by_status(
            EnvironmentStatus.ACTIVE
        )

    def find_by_status(
        self,
        status: EnvironmentStatus,
    ) -> List[
        Environment
    ]:
        """Find environments by status."""

        with self._lock:

            return [
                environment
                for environment
                in self._environments.values()
                if environment.status == status
            ]

    def list(
        self,
    ) -> List[
        Environment
    ]:
        """List all environments."""

        with self._lock:
            return list(
                self._environments.values()
            )

    def count(self) -> int:
        """Return environment count."""

        with self._lock:
            return len(
                self._environments
            )

    def clear(self) -> None:
        """Clear registry."""

        with self._lock:
            self._environments.clear()

    def contains(
        self,
        environment_id: str,
    ) -> bool:
        """Check whether an environment exists."""

        with self._lock:
            return environment_id in (
                self._environments
            )