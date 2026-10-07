from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..aios_core.agents import (
    CalendarAgent,
    CodeAgent,
    EmailAgent,
    FileAgent,
    ReminderAgent,
    SearchAgent,
    WritingAgent,
)


router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
)


_AGENT_CLASSES = {
    "email": EmailAgent,
    "calendar": CalendarAgent,
    "writing": WritingAgent,
    "code": CodeAgent,
    "file": FileAgent,
    "search": SearchAgent,
    "reminder": ReminderAgent,
}


class AgentExecuteRequest(BaseModel):
    input: str = Field(
        ...,
        min_length=1,
    )

    context: dict[str, Any] = Field(
        default_factory=dict
    )


def _create_agent(
    name: str,
):
    agent_class = _AGENT_CLASSES.get(
        name.lower()
    )

    if agent_class is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown agent: {name}",
        )

    try:
        return agent_class()
    except TypeError:
        return agent_class


@router.get("")
def list_agents() -> dict[str, Any]:
    return {
        "success": True,
        "agents": [
            {
                "name": name,
                "available": True,
            }
            for name in _AGENT_CLASSES
        ],
    }


@router.get("/{agent_name}")
def get_agent(
    agent_name: str,
) -> dict[str, Any]:
    if agent_name.lower() not in _AGENT_CLASSES:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown agent: {agent_name}",
        )

    agent = _create_agent(
        agent_name
    )

    data: dict[str, Any] = {
        "name": agent_name.lower(),
        "available": True,
    }

    if hasattr(agent, "info"):
        try:
            info = agent.info()

            data["info"] = (
                info.to_dict()
                if hasattr(info, "to_dict")
                else info
            )

        except Exception:
            pass

    return {
        "success": True,
        "data": data,
    }


@router.post("/{agent_name}/execute")
def execute_agent(
    agent_name: str,
    request: AgentExecuteRequest,
) -> dict[str, Any]:
    agent = _create_agent(
        agent_name
    )

    methods = [
        "execute",
        "run",
        "process",
    ]

    for method_name in methods:
        method = getattr(
            agent,
            method_name,
            None,
        )

        if not callable(method):
            continue

        try:
            try:
                result = method(
                    request.input,
                    context=request.context,
                )

            except TypeError:
                result = method(
                    request.input
                )

            return {
                "success": True,
                "agent": agent_name.lower(),
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

    raise HTTPException(
        status_code=500,
        detail=(
            f"Agent '{agent_name}' does not "
            "provide an executable interface."
        ),
    )