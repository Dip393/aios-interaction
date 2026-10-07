from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..aios_core.environments import (
    EnvironmentManager,
)


router = APIRouter(
    prefix="/environments",
    tags=["Environments"],
)


_manager = EnvironmentManager()


class CreateEnvironmentRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
    )

    environment_type: str = "general"

    session_id: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class DataRequest(BaseModel):
    key: str
    value: Any


@router.get("")
def list_environments(
    session_id: str | None = None,
) -> dict[str, Any]:
    try:
        environments = _manager.list(
            session_id=session_id
        )

        return {
            "success": True,
            "data": [
                item.to_dict()
                if hasattr(item, "to_dict")
                else item
                for item in environments
            ],
        }

    except TypeError:
        environments = _manager.list()

        return {
            "success": True,
            "data": [
                item.to_dict()
                if hasattr(item, "to_dict")
                else item
                for item in environments
            ],
        }


@router.post("")
def create_environment(
    request: CreateEnvironmentRequest,
) -> dict[str, Any]:
    try:
        environment = _manager.create(
            name=request.name,
            environment_type=request.environment_type,
            session_id=request.session_id,
            metadata=request.metadata,
        )

        return {
            "success": True,
            "data": (
                environment.to_dict()
                if hasattr(environment, "to_dict")
                else environment
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get("/{environment_id}")
def get_environment(
    environment_id: str,
) -> dict[str, Any]:
    environment = _manager.get(
        environment_id
    )

    if environment is None:
        raise HTTPException(
            status_code=404,
            detail="Environment not found.",
        )

    return {
        "success": True,
        "data": (
            environment.to_dict()
            if hasattr(environment, "to_dict")
            else environment
        ),
    }


@router.post("/{environment_id}/activate")
def activate_environment(
    environment_id: str,
) -> dict[str, Any]:
    try:
        environment = _manager.activate(
            environment_id
        )

        return {
            "success": True,
            "data": (
                environment.to_dict()
                if hasattr(environment, "to_dict")
                else environment
            ),
        }

    except AttributeError:
        try:
            environment = _manager.switch(
                environment_id
            )

            return {
                "success": True,
                "data": (
                    environment.to_dict()
                    if hasattr(
                        environment,
                        "to_dict",
                    )
                    else environment
                ),
            }

        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get("/{environment_id}/state")
def get_state(
    environment_id: str,
) -> dict[str, Any]:
    try:
        state = _manager.get_state(
            environment_id
        )

        return {
            "success": True,
            "data": (
                state.to_dict()
                if hasattr(
                    state,
                    "to_dict",
                )
                else state
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.post("/{environment_id}/data")
def set_data(
    environment_id: str,
    request: DataRequest,
) -> dict[str, Any]:
    try:
        result = _manager.set_data(
            environment_id,
            request.key,
            request.value,
        )

        return {
            "success": True,
            "data": (
                result.to_dict()
                if hasattr(
                    result,
                    "to_dict",
                )
                else result
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.post("/{environment_id}/pause")
def pause_environment(
    environment_id: str,
) -> dict[str, Any]:
    try:
        result = _manager.pause(
            environment_id
        )

        return {
            "success": True,
            "data": (
                result.to_dict()
                if hasattr(
                    result,
                    "to_dict",
                )
                else result
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.post("/{environment_id}/complete")
def complete_environment(
    environment_id: str,
) -> dict[str, Any]:
    try:
        result = _manager.complete(
            environment_id
        )

        return {
            "success": True,
            "data": (
                result.to_dict()
                if hasattr(
                    result,
                    "to_dict",
                )
                else result
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc