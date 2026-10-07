from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..aios_core.connectors import (
    BaseConnector,
    CalendarConnector,
    ConnectorRegistry,
    FilesystemConnector,
    GmailConnector,
    MessagingConnector,
    BrowserConnector,
)


router = APIRouter(
    prefix="/connectors",
    tags=["Connectors"],
)


_registry = ConnectorRegistry()

_registry.register(
    GmailConnector()
)

_registry.register(
    CalendarConnector()
)

_registry.register(
    BrowserConnector()
)

_registry.register(
    FilesystemConnector()
)

_registry.register(
    MessagingConnector()
)


class ConnectorExecuteRequest(BaseModel):
    operation: str = Field(
        ...,
        min_length=1,
    )

    parameters: dict[str, Any] = Field(
        default_factory=dict
    )


def _serialize(
    value: Any,
) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()

    if isinstance(value, list):
        return [
            _serialize(item)
            for item in value
        ]

    if isinstance(value, dict):
        return {
            key: _serialize(item)
            for key, item in value.items()
        }

    return value


@router.get("")
def list_connectors() -> dict[str, Any]:
    return {
        "success": True,
        "data": [
            info.to_dict()
            for info in _registry.infos()
        ],
    }


@router.get("/{connector_name}")
def get_connector(
    connector_name: str,
) -> dict[str, Any]:
    connector = _registry.get(
        connector_name
    )

    if connector is None:
        raise HTTPException(
            status_code=404,
            detail="Connector not found.",
        )

    return {
        "success": True,
        "data": connector.info().to_dict(),
    }


@router.post(
    "/{connector_name}/connect"
)
def connect_connector(
    connector_name: str,
) -> dict[str, Any]:
    connector = _registry.get(
        connector_name
    )

    if connector is None:
        raise HTTPException(
            status_code=404,
            detail="Connector not found.",
        )

    try:
        result = connector.connect()

        return {
            "success": result.success,
            "data": result.to_dict(),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.post(
    "/{connector_name}/disconnect"
)
def disconnect_connector(
    connector_name: str,
) -> dict[str, Any]:
    connector = _registry.get(
        connector_name
    )

    if connector is None:
        raise HTTPException(
            status_code=404,
            detail="Connector not found.",
        )

    try:
        result = connector.disconnect()

        return {
            "success": result.success,
            "data": result.to_dict(),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get(
    "/{connector_name}/health"
)
def health_check(
    connector_name: str,
) -> dict[str, Any]:
    connector = _registry.get(
        connector_name
    )

    if connector is None:
        raise HTTPException(
            status_code=404,
            detail="Connector not found.",
        )

    result = connector.health_check()

    return {
        "success": result.success,
        "data": result.to_dict(),
    }


@router.post(
    "/{connector_name}/execute"
)
def execute_connector(
    connector_name: str,
    request: ConnectorExecuteRequest,
) -> dict[str, Any]:
    connector: BaseConnector | None = (
        _registry.get(
            connector_name
        )
    )

    if connector is None:
        raise HTTPException(
            status_code=404,
            detail="Connector not found.",
        )

    try:
        result = connector.execute(
            request.operation,
            **request.parameters,
        )

        return {
            "success": result.success,
            "data": _serialize(result),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc