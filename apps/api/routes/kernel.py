from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..aios_core.kernel import AIOSKernel


router = APIRouter(
    prefix="/kernel",
    tags=["Kernel"],
)


_kernel = AIOSKernel()


class KernelRequest(BaseModel):
    input: str = Field(
        ...,
        min_length=1,
        description="Natural-language instruction for AIOS.",
    )

    session_id: str | None = None
    user_id: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )


class ConfirmationRequest(BaseModel):
    approved: bool


class KernelResponse(BaseModel):
    success: bool
    data: Any = None
    message: str | None = None


@router.get("/health")
def health() -> dict[str, Any]:
    return {
        "success": True,
        "service": "aios-kernel",
        "status": "running",
    }


@router.post(
    "/process",
    response_model=KernelResponse,
)
def process(
    request: KernelRequest,
) -> KernelResponse:
    """
    Send a natural-language command to the AIOS kernel.

    The kernel handles:
        input -> context -> intent -> plan -> policy -> execution
    """

    try:
        result = _kernel.process(
            request.input,
            session_id=request.session_id,
            user_id=request.user_id,
            metadata=request.metadata,
        )

        if hasattr(result, "to_dict"):
            data = result.to_dict()
        else:
            data = result

        return KernelResponse(
            success=True,
            data=data,
        )

    except TypeError:
        # Compatibility fallback for kernels whose process()
        # signature only accepts the input text.
        try:
            result = _kernel.process(
                request.input
            )

            data = (
                result.to_dict()
                if hasattr(result, "to_dict")
                else result
            )

            return KernelResponse(
                success=True,
                data=data,
            )

        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=str(exc),
            ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


@router.post("/confirm")
def confirm(
    request: ConfirmationRequest,
) -> dict[str, Any]:
    """
    Confirmation endpoint for future side-effect workflows.

    The actual continuation logic will be connected when the
    kernel confirmation/checkpoint API is wired into the API app.
    """

    return {
        "success": True,
        "approved": request.approved,
        "message": (
            "Confirmation received."
            if request.approved
            else "Action rejected."
        ),
    }


@router.get("/status")
def status() -> dict[str, Any]:
    status_method = getattr(
        _kernel,
        "status",
        None,
    )

    if callable(status_method):
        try:
            result = status_method()

            return {
                "success": True,
                "data": (
                    result.to_dict()
                    if hasattr(result, "to_dict")
                    else result
                ),
            }
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=str(exc),
            ) from exc

    return {
        "success": True,
        "data": {
            "status": "ready",
        },
    }