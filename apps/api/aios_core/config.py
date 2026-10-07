from __future__ import annotations

import os
from pathlib import Path
from typing import Final


# ============================================================================
# Project paths
# ============================================================================

# apps/api/aios_core/config.py
#        │
#        └── parents[0] = aios_core
#            parents[1] = api
#            parents[2] = apps
#            parents[3] = project root
#
# Using parents[3] keeps the project root independent from the current
# working directory.
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[3]

API_ROOT: Final[Path] = PROJECT_ROOT / "apps" / "api"
WEB_ROOT: Final[Path] = PROJECT_ROOT / "apps" / "web"
TAURI_ROOT: Final[Path] = PROJECT_ROOT / "src-tauri"


# ============================================================================
# Environment helpers
# ============================================================================

def env_string(
    name: str,
    default: str,
) -> str:
    value = os.getenv(name)

    if value is None:
        return default

    value = value.strip()

    return value if value else default


def env_bool(
    name: str,
    default: bool,
) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }


def env_int(
    name: str,
    default: int,
) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    try:
        return int(value.strip())
    except (TypeError, ValueError):
        return default


# ============================================================================
# Data / database
# ============================================================================

DATA_DIR: Final[Path] = Path(
    env_string(
        "AIOS_DATA_DIR",
        str(API_ROOT / "data"),
    )
).expanduser()

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

DB_PATH: Final[Path] = DATA_DIR / "aios.db"

DATABASE_URL: Final[str] = env_string(
    "AIOS_DATABASE_URL",
    f"sqlite:///{DB_PATH.as_posix()}",
)


# ============================================================================
# Runtime
# ============================================================================

APP_NAME: Final[str] = env_string(
    "AIOS_APP_NAME",
    "AIOS Runtime",
)

APP_VERSION: Final[str] = env_string(
    "AIOS_APP_VERSION",
    "0.2.0",
)

ENVIRONMENT: Final[str] = env_string(
    "AIOS_ENVIRONMENT",
    "development",
).lower()

DEBUG: Final[bool] = env_bool(
    "AIOS_DEBUG",
    ENVIRONMENT != "production",
)

TIMEZONE: Final[str] = env_string(
    "AIOS_TIMEZONE",
    "Asia/Kolkata",
)

HOST: Final[str] = env_string(
    "AIOS_HOST",
    "127.0.0.1",
)

PORT: Final[int] = env_int(
    "AIOS_PORT",
    8000,
)


# ============================================================================
# API / CORS
# ============================================================================

DEFAULT_CORS_ORIGINS: Final[tuple[str, ...]] = (
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:1420",
    "http://127.0.0.1:1420",
)


def get_cors_origins() -> list[str]:
    """
    Returns configured CORS origins.

    Environment variable example:

        AIOS_CORS_ORIGINS=http://localhost:3000,http://localhost:1420
    """

    raw = os.getenv("AIOS_CORS_ORIGINS")

    if not raw:
        return list(DEFAULT_CORS_ORIGINS)

    origins = [
        origin.strip().rstrip("/")
        for origin in raw.split(",")
        if origin.strip()
    ]

    return origins or list(DEFAULT_CORS_ORIGINS)


CORS_ORIGINS: Final[list[str]] = get_cors_origins()


# ============================================================================
# AI / LLM
# ============================================================================

AIOS_USE_OLLAMA: Final[bool] = env_bool(
    "AIOS_USE_OLLAMA",
    True,
)

OLLAMA_BASE_URL: Final[str] = env_string(
    "OLLAMA_BASE_URL",
    "http://127.0.0.1:11434",
).rstrip("/")

OLLAMA_MODEL: Final[str] = env_string(
    "OLLAMA_MODEL",
    "gemma3:4b",
)

AIOS_LLM_TIMEOUT: Final[int] = env_int(
    "AIOS_LLM_TIMEOUT",
    120,
)


# ============================================================================
# AIOS behaviour
# ============================================================================

AIOS_AUTO_APPROVE_LOW_RISK: Final[bool] = env_bool(
    "AIOS_AUTO_APPROVE_LOW_RISK",
    False,
)

AIOS_REQUIRE_CONFIRMATION: Final[bool] = env_bool(
    "AIOS_REQUIRE_CONFIRMATION",
    True,
)

AIOS_MEMORY_ENABLED: Final[bool] = env_bool(
    "AIOS_MEMORY_ENABLED",
    True,
)

AIOS_VOICE_ENABLED: Final[bool] = env_bool(
    "AIOS_VOICE_ENABLED",
    True,
)

AIOS_VISION_ENABLED: Final[bool] = env_bool(
    "AIOS_VISION_ENABLED",
    True,
)


# ============================================================================
# Memory
# ============================================================================

MEMORY_SHORT_TERM_LIMIT: Final[int] = env_int(
    "AIOS_MEMORY_SHORT_TERM_LIMIT",
    100,
)

MEMORY_SEMANTIC_DIMENSION: Final[int] = env_int(
    "AIOS_MEMORY_SEMANTIC_DIMENSION",
    256,
)

MEMORY_SEARCH_LIMIT: Final[int] = env_int(
    "AIOS_MEMORY_SEARCH_LIMIT",
    20,
)


# ============================================================================
# Tasks / scheduler
# ============================================================================

SCHEDULER_ENABLED: Final[bool] = env_bool(
    "AIOS_SCHEDULER_ENABLED",
    True,
)

SCHEDULER_INTERVAL_SECONDS: Final[int] = env_int(
    "AIOS_SCHEDULER_INTERVAL_SECONDS",
    30,
)


# ============================================================================
# File / execution security
# ============================================================================

AIOS_ALLOW_FILE_WRITE: Final[bool] = env_bool(
    "AIOS_ALLOW_FILE_WRITE",
    True,
)

AIOS_ALLOW_FILE_DELETE: Final[bool] = env_bool(
    "AIOS_ALLOW_FILE_DELETE",
    False,
)

AIOS_ALLOW_EXTERNAL_ACTIONS: Final[bool] = env_bool(
    "AIOS_ALLOW_EXTERNAL_ACTIONS",
    False,
)

AIOS_SANDBOX_ENABLED: Final[bool] = env_bool(
    "AIOS_SANDBOX_ENABLED",
    True,
)


# ============================================================================
# Connector configuration
# ============================================================================

GMAIL_ENABLED: Final[bool] = env_bool(
    "AIOS_GMAIL_ENABLED",
    False,
)

CALENDAR_ENABLED: Final[bool] = env_bool(
    "AIOS_CALENDAR_ENABLED",
    False,
)

BROWSER_ENABLED: Final[bool] = env_bool(
    "AIOS_BROWSER_ENABLED",
    False,
)

FILESYSTEM_ENABLED: Final[bool] = env_bool(
    "AIOS_FILESYSTEM_ENABLED",
    True,
)

MESSAGING_ENABLED: Final[bool] = env_bool(
    "AIOS_MESSAGING_ENABLED",
    False,
)


# ============================================================================
# Development helpers
# ============================================================================

def is_production() -> bool:
    return ENVIRONMENT == "production"


def is_development() -> bool:
    return ENVIRONMENT == "development"


def config_summary() -> dict[str, object]:
    """
    Returns safe configuration information.

    Secrets are intentionally not included.
    """

    return {
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "environment": ENVIRONMENT,
        "debug": DEBUG,
        "timezone": TIMEZONE,
        "host": HOST,
        "port": PORT,
        "data_dir": str(DATA_DIR),
        "db_path": str(DB_PATH),
        "database_url": _safe_database_url(DATABASE_URL),
        "ollama": {
            "enabled": AIOS_USE_OLLAMA,
            "base_url": OLLAMA_BASE_URL,
            "model": OLLAMA_MODEL,
        },
        "features": {
            "memory": AIOS_MEMORY_ENABLED,
            "voice": AIOS_VOICE_ENABLED,
            "vision": AIOS_VISION_ENABLED,
            "scheduler": SCHEDULER_ENABLED,
        },
        "security": {
            "require_confirmation": AIOS_REQUIRE_CONFIRMATION,
            "auto_approve_low_risk": AIOS_AUTO_APPROVE_LOW_RISK,
            "allow_file_write": AIOS_ALLOW_FILE_WRITE,
            "allow_file_delete": AIOS_ALLOW_FILE_DELETE,
            "allow_external_actions": AIOS_ALLOW_EXTERNAL_ACTIONS,
            "sandbox_enabled": AIOS_SANDBOX_ENABLED,
        },
    }


def _safe_database_url(url: str) -> str:
    """
    Prevent accidental exposure of database credentials in diagnostics.

    SQLite URLs are returned unchanged.
    """

    if url.startswith("sqlite:"):
        return url

    if "@" not in url:
        return url

    scheme, _, remainder = url.partition("://")

    if "@" not in remainder:
        return url

    credentials, _, host = remainder.partition("@")

    if ":" in credentials:
        username = credentials.split(":", 1)[0]
        credentials = f"{username}:***"

    return f"{scheme}://{credentials}@{host}"


# ============================================================================
# Public exports
# ============================================================================

__all__ = [
    "PROJECT_ROOT",
    "API_ROOT",
    "WEB_ROOT",
    "TAURI_ROOT",
    "DATA_DIR",
    "DB_PATH",
    "DATABASE_URL",
    "APP_NAME",
    "APP_VERSION",
    "ENVIRONMENT",
    "DEBUG",
    "TIMEZONE",
    "HOST",
    "PORT",
    "CORS_ORIGINS",
    "AIOS_USE_OLLAMA",
    "OLLAMA_BASE_URL",
    "OLLAMA_MODEL",
    "AIOS_LLM_TIMEOUT",
    "AIOS_AUTO_APPROVE_LOW_RISK",
    "AIOS_REQUIRE_CONFIRMATION",
    "AIOS_MEMORY_ENABLED",
    "AIOS_VOICE_ENABLED",
    "AIOS_VISION_ENABLED",
    "MEMORY_SHORT_TERM_LIMIT",
    "MEMORY_SEMANTIC_DIMENSION",
    "MEMORY_SEARCH_LIMIT",
    "SCHEDULER_ENABLED",
    "SCHEDULER_INTERVAL_SECONDS",
    "AIOS_ALLOW_FILE_WRITE",
    "AIOS_ALLOW_FILE_DELETE",
    "AIOS_ALLOW_EXTERNAL_ACTIONS",
    "AIOS_SANDBOX_ENABLED",
    "GMAIL_ENABLED",
    "CALENDAR_ENABLED",
    "BROWSER_ENABLED",
    "FILESYSTEM_ENABLED",
    "MESSAGING_ENABLED",
    "get_cors_origins",
    "is_production",
    "is_development",
    "config_summary",
]