import json
import httpx
from .config import AIOS_USE_OLLAMA, OLLAMA_BASE_URL, OLLAMA_MODEL

SYSTEM = """You are the planner for a local-first AI operating environment. Return ONLY valid JSON.\nSchema: {intent:string, title:string, environment:string, entities:object, actions:[{tool:string,args:object,risk:string}], memory_candidates:[{category:string,content:string,importance:int}], event_candidates:[{title:string,event_type:string,event_time:string|null}], response:string}.\nNever claim an external action happened unless the tool reports success. Prefer confirmation for external side effects."""

async def ollama_plan(text: str):
    if not AIOS_USE_OLLAMA:
        return None
    payload = {"model": OLLAMA_MODEL, "system": SYSTEM, "prompt": text, "stream": False, "format": "json"}
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
            r.raise_for_status()
            data = r.json()
            return json.loads(data.get("response", "{}"))
    except Exception:
        return None
