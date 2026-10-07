from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..aios_core.voice import VoiceManager


router = APIRouter(
    prefix="/voice",
    tags=["Voice"],
)


_voice = VoiceManager()


class VoiceInputRequest(BaseModel):
    session_id: str

    text: str = Field(
        ...,
        min_length=1,
    )


class SpeakRequest(BaseModel):
    session_id: str

    text: str = Field(
        ...,
        min_length=1,
    )


@router.get("/status")
def status() -> dict[str, Any]:
    try:
        result = _voice.status()

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
        result = _voice.start_session(
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
        result = _voice.stop_session(
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


@router.post("/transcribe")
def transcribe(
    request: VoiceInputRequest,
) -> dict[str, Any]:
    try:
        result = _voice.transcribe(
            request.session_id,
            request.text,
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


@router.post("/speak")
def speak(
    request: SpeakRequest,
) -> dict[str, Any]:
    try:
        result = _voice.speak(
            request.session_id,
            request.text,
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
def process(
    request: VoiceInputRequest,
) -> dict[str, Any]:
    """
    Development voice pipeline endpoint.

    Real audio -> STT -> Kernel -> TTS will be connected
    through provider adapters later.
    """

    try:
        result = _voice.process_input(
            request.session_id,
            request.text,
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