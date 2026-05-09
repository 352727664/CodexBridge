"""
Admin API endpoints for the CodexBridge WebUI.
Provides CRUD for providers, settings, and connection testing.
"""
import json
import os
import time
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

router = APIRouter(prefix="/api", tags=["admin"])

# Will be set by proxy.py after initialization
pm = None
CONFIG_PATH = ""


def init_admin(manager, config_path: str):
    global pm, CONFIG_PATH
    pm = manager
    CONFIG_PATH = config_path


def _sync_codex_config():
    """Write ~/.codex/config.toml and auth.json so Codex works immediately."""
    active_id = pm.config.get("active_provider", "")
    pcfg = pm.config.get("providers", {}).get(active_id, {})
    if not pcfg:
        return

    model = (pcfg.get("models") or ["unknown"])[0]
    port = pm.config.get("port", 8787)

    codex_dir = os.path.expanduser("~/.codex")
    os.makedirs(codex_dir, exist_ok=True)

    # auth.json
    auth_path = os.path.join(codex_dir, "auth.json")
    auth = {"OPENAI_API_KEY": "codexbridge-local"}
    with open(auth_path, "w") as f:
        json.dump(auth, f, indent=2)

    # config.toml — preserve existing non-CodexBridge sections
    config_path = os.path.join(codex_dir, "config.toml")
    existing = ""
    if os.path.exists(config_path):
        with open(config_path) as f:
            existing = f.read()

    # Build CodexBridge provider block
    cb_block = (
        f'[model_providers.codexbridge]\n'
        f'name = "{model}"\n'
        f'base_url = "http://127.0.0.1:{port}/v1"\n'
        f'wire_api = "responses"\n'
        f'requires_openai_auth = true\n'
        f'request_max_retries = 1\n'
    )

    # Parse existing config to preserve non-codexbridge sections
    lines = existing.split("\n")
    new_lines = []
    skip = False
    for line in lines:
        if line.strip().startswith("[model_providers.codexbridge]"):
            skip = True
            continue
        if skip and line.strip().startswith("["):
            skip = False
        if skip and not line.strip():
            continue
        if not skip:
            new_lines.append(line)

    # Insert global settings at top if not present
    content = "\n".join(new_lines).strip()
    has_provider = "model_provider" in content
    has_model = content.startswith('model =') or '\nmodel =' in content

    parts = []
    if not has_model:
        parts.append(f'model = "{model}"')
    if not has_provider:
        parts.append('model_provider = "codexbridge"')
    if parts:
        content = "\n".join(parts) + "\n\n" + content

    content = content.strip() + "\n\n" + cb_block

    with open(config_path, "w") as f:
        f.write(content)


# ------------------------------------------------------------------ #
#  Models
# ------------------------------------------------------------------ #

class ProviderCreate(BaseModel):
    name: str
    api_format: str = "openai"
    base_url: str = ""
    api_key: str = ""
    models: List[str] = []
    has_reasoning: bool = False
    note: str = ""
    website: str = ""


class ProviderUpdate(BaseModel):
    name: Optional[str] = None
    api_format: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    models: Optional[List[str]] = None
    has_reasoning: Optional[bool] = None
    note: Optional[str] = None
    website: Optional[str] = None


class TestRequest(BaseModel):
    base_url: str = ""
    api_key: str = ""
    api_format: str = "openai"
    model: str = ""


class SettingsUpdate(BaseModel):
    active_provider: Optional[str] = None
    port: Optional[int] = None


# ------------------------------------------------------------------ #
#  Provider CRUD
# ------------------------------------------------------------------ #

@router.get("/providers")
async def list_providers():
    providers = []
    for pid, p in pm.providers.items():
        pcfg = pm.config.get("providers", {}).get(pid, {})
        providers.append({
            "id": pid,
            "name": p.name,
            "api_format": getattr(p, "api_format", "openai"),
            "base_url": p.base_url,
            "api_key": p.api_key,
            "models": p.models,
            "has_reasoning": p.has_reasoning,
            "note": pcfg.get("note", ""),
            "website": pcfg.get("website", ""),
            "is_active": pid == pm.config.get("active_provider"),
        })
    return {"data": providers, "active_provider": pm.config.get("active_provider")}


@router.post("/providers")
async def create_provider(body: ProviderCreate):
    pid = body.name.lower().replace(" ", "-").replace("/", "-")
    pid = "".join(c for c in pid if c.isalnum() or c == "-")
    if not pid:
        pid = f"provider-{int(time.time())}"
    if pid in pm.providers:
        pid = f"{pid}-{int(time.time())}"

    pcfg = {
        "name": body.name,
        "api_format": body.api_format,
        "base_url": body.base_url,
        "api_key": body.api_key,
        "models": body.models,
        "has_reasoning": body.has_reasoning,
    }
    if body.note:
        pcfg["note"] = body.note
    if body.website:
        pcfg["website"] = body.website

    pm.config.setdefault("providers", {})[pid] = pcfg
    pm.config["active_provider"] = pid
    pm.save_config()

    from providers import PROVIDER_CLASSES
    cls = PROVIDER_CLASSES.get(body.api_format, PROVIDER_CLASSES["openai"])
    pm.providers[pid] = cls(pid, pcfg)

    _sync_codex_config()
    return {"status": "ok", "provider": {"id": pid, "name": body.name}}


@router.put("/providers/{provider_id}")
async def update_provider(provider_id: str, body: ProviderUpdate):
    if provider_id not in pm.providers:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")

    pcfg = pm.config.get("providers", {}).get(provider_id, {})
    updates = body.dict(exclude_none=True)

    for k, v in updates.items():
        if k in ("name", "api_format", "base_url", "api_key", "models", "has_reasoning", "note", "website"):
            pcfg[k] = v
    pm.config["providers"][provider_id] = pcfg
    pm.save_config()

    from providers import PROVIDER_CLASSES
    api_format = pcfg.get("api_format", "openai")
    cls = PROVIDER_CLASSES.get(api_format, PROVIDER_CLASSES["openai"])
    pm.providers[provider_id] = cls(provider_id, pcfg)

    _sync_codex_config()
    return {"status": "ok"}


@router.delete("/providers/{provider_id}")
async def delete_provider(provider_id: str):
    if provider_id not in pm.providers:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")

    del pm.providers[provider_id]
    pm.config.get("providers", {}).pop(provider_id, None)

    if pm.config.get("active_provider") == provider_id:
        remaining = list(pm.providers.keys())
        pm.config["active_provider"] = remaining[0] if remaining else ""

    pm.save_config()
    return {"status": "ok"}


@router.post("/providers/{provider_id}/enable")
async def enable_provider(provider_id: str):
    if provider_id not in pm.providers:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")

    pm.config["active_provider"] = provider_id
    pm.save_config()
    _sync_codex_config()
    return {"status": "ok", "active_provider": provider_id}


@router.post("/providers/{provider_id}/duplicate")
async def duplicate_provider(provider_id: str):
    if provider_id not in pm.providers:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_id}' not found")

    pcfg = pm.config.get("providers", {}).get(provider_id, {})
    new_pcfg = dict(pcfg)
    new_name = f"{pcfg.get('name', provider_id)} (Copy)"
    new_pcfg["name"] = new_name

    new_pid = f"{provider_id}-copy-{int(time.time())}"
    pm.config.setdefault("providers", {})[new_pid] = new_pcfg
    pm.save_config()

    from providers import PROVIDER_CLASSES
    cls = PROVIDER_CLASSES.get(new_pcfg.get("api_format", "openai"), PROVIDER_CLASSES["openai"])
    pm.providers[new_pid] = cls(new_pid, new_pcfg)

    return {"status": "ok", "provider": {"id": new_pid, "name": new_name}}


# ------------------------------------------------------------------ #
#  Connection Testing
# ------------------------------------------------------------------ #

@router.post("/test")
async def test_connection(body: TestRequest):
    """Test an API connection by sending a minimal chat completion request."""
    base_url = body.base_url.rstrip("/")
    api_key = body.api_key
    model = body.model
    api_format = body.api_format

    start = time.time()

    try:
        if api_format == "anthropic":
            # Anthropic: base_url could be https://api.anthropic.com or https://api.anthropic.com/v1
            test_url = base_url
            if not test_url.endswith("/v1"):
                test_url = f"{test_url}/v1"
            url = f"{test_url}/messages"
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            payload = {
                "model": model or "claude-sonnet-4-20250514",
                "max_tokens": 32,
                "messages": [{"role": "user", "content": "Hi, reply with just 'OK'."}],
            }
        else:
            # OpenAI-compatible: ensure base_url ends with /v1 before appending /chat/completions
            test_url = base_url
            if not test_url.endswith("/v1"):
                test_url = f"{test_url}/v1"
            url = f"{test_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": model or "deepseek-chat",
                "max_tokens": 32,
                "messages": [{"role": "user", "content": "Hi, reply with just 'OK'."}],
            }

        async with httpx.AsyncClient(timeout=30, follow_redirects=True, proxy=None) as client:
            resp = await client.post(url, json=payload, headers=headers)
            elapsed = int((time.time() - start) * 1000)

            if resp.status_code == 200:
                return {"status": "ok", "latency_ms": elapsed, "message": "连接成功"}
            else:
                detail = resp.text[:300]
                return {"status": "error", "latency_ms": elapsed, "message": f"HTTP {resp.status_code}: {detail}"}

    except httpx.TimeoutException:
        elapsed = int((time.time() - start) * 1000)
        return {"status": "error", "latency_ms": elapsed, "message": "连接超时（30秒）"}
    except httpx.ConnectError as e:
        elapsed = int((time.time() - start) * 1000)
        return {"status": "error", "latency_ms": elapsed, "message": f"无法连接到服务器: {e}"}
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        return {"status": "error", "latency_ms": elapsed, "message": str(e)}


@router.post("/fetch-models")
async def fetch_models(body: TestRequest):
    """Fetch available models from an API endpoint."""
    base_url = body.base_url.rstrip("/")
    api_key = body.api_key
    api_format = body.api_format

    try:
        if api_format == "anthropic":
            return {"status": "ok", "models": ["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-3-5-haiku-20241022"]}

        # Ensure base_url ends with /v1 before appending /models
        test_url = base_url
        if not test_url.endswith("/v1"):
            test_url = f"{test_url}/v1"
        url = f"{test_url}/models"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=15, follow_redirects=True, proxy=None) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                models = [m.get("id", "") for m in data.get("data", [])]
                if not models:
                    return {"status": "error", "message": "模型列表为空", "models": []}
                return {"status": "ok", "models": models}
            else:
                return {"status": "error", "message": f"HTTP {resp.status_code}: {resp.text[:200]}", "models": []}

    except Exception as e:
        return {"status": "error", "message": str(e), "models": []}


# ------------------------------------------------------------------ #
#  Settings
# ------------------------------------------------------------------ #

@router.get("/settings")
async def get_settings():
    return {
        "active_provider": pm.config.get("active_provider", ""),
        "port": pm.config.get("port", 8787),
    }


@router.put("/settings")
async def update_settings(body: SettingsUpdate):
    if body.active_provider is not None:
        pm.config["active_provider"] = body.active_provider
    if body.port is not None:
        pm.config["port"] = body.port
    pm.save_config()
    return {"status": "ok"}


@router.get("/config/raw")
async def get_raw_config():
    """Return the raw config.json for preview."""
    return {"config": pm.config}
