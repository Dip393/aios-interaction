from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..aios_core.vision import VisionManager


router = APIRouter(
    prefix="/vision",
    tags=["Vision"],
)


_vision = VisionManager()


class VisionFrameRequest(BaseModel):
    session_id: str

    frame_id: str | None = None

    width: int = Field(
        default=0,
        ge=0,
    )

    height: int = Field(
        default=0,
        ge=0,
    )

    hands: list[dict[str, Any]] = Field(
        default_factory=list
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


@router.get("/status")
def status() -> dict[str, Any]:
    try:
        result = _vision.status()

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
            status_code=500,
            detail=str(exc),
        ) from exc


@router.post("/sessions/{session_id}/start")
def start_session(
    session_id: str,
) -> dict[str, Any]:
    try:
        result = _vision.start_session(
            session_id
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


@router.post("/sessions/{session_id}/stop")
def stop_session(
    session_id: str,
) -> dict[str, Any]:
    try:
        result = _vision.stop_session(
            session_id
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


@router.post("/process")
def process_frame(
    request: VisionFrameRequest,
) -> dict[str, Any]:
    try:
        result = _vision.process_frame(
            session_id=request.session_id,
            frame_id=request.frame_id,
            width=request.width,
            height=request.height,
            hands=request.hands,
            metadata=request.metadata,
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

    except TypeError:
        try:
            result = _vision.process_frame(
                request.session_id,
                request.hands,
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

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get("/sessions/{session_id}/last")
def last_result(
    session_id: str,
) -> dict[str, Any]:
    try:
        result = _vision.last_result(
            session_id
        )

        if result is None:
            return {
                "success": True,
                "data": None,
            }

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
            status_code=404,
            detail=str(exc),
        ) from exc