"""
CodexBridge — Local proxy that bridges Codex Desktop to various AI providers

Codex Desktop uses OpenAI's Responses API. This proxy translates between
Responses API and Chat Completions API, enabling non-OpenAI providers
(MiMo, DeepSeek, Qwen, Kimi, GLM, OpenRouter, etc.) to work with Codex.

    Codex (Responses API) → CodexBridge → AI Provider (Chat Completions API)

Usage:
    python proxy.py                      # Start with default config
    python proxy.py --port 9000          # Start on custom port
    python proxy.py print-config         # Print Codex config.toml + auth.json
    python proxy.py print-cc-switch      # Print cc-switch paste blocks
"""
import json as _json
import os
import shutil
import sys

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from provider_manager import ProviderManager
from admin_api import router as admin_router, init_admin

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "webui", "dist")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
EXAMPLE_PATH = os.path.join(BASE_DIR, "config.example.json")


# ------------------------------------------------------------------ #
#  Error envelope helper (matches OpenAI Responses API format)
# ------------------------------------------------------------------ #
def error_envelope(status: int, code: str, message: str):
    type_map = {401: "authentication_error", 429: "rate_limit_exceeded"}
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "type": type_map.get(status, "invalid_request_error") if status < 500 else "server_error",
                "code": code,
                "message": message,
                "status": status,
            }
        },
    )


# ------------------------------------------------------------------ #
#  Config snippet generators (borrowed from mimo2codex pattern)
# ------------------------------------------------------------------ #
def _config_snippet(host: str, port: int, active: str = "") -> str:
    """Print ~/.codex/auth.json + config.toml for all configured providers."""
    lines = []
    lines.append("# CodexBridge — Codex configuration snippets")
    lines.append("# Copy this into ~/.codex/config.toml and ~/.codex/auth.json")
    lines.append("")
    lines.append("# ─── ~/.codex/auth.json ───")
    lines.append(_json.dumps({"OPENAI_API_KEY": "codexbridge-local"}, indent=2))
    lines.append("")
    lines.append("# ─── ~/.codex/config.toml ───")

    active_pid = active or pm.config.get("active_provider", "")
    active_pcfg = pm.config.get("providers", {}).get(active_pid, {})
    model = (active_pcfg.get("models") or ["unknown"])[0]

    lines.append(f'model = "{model}"')
    lines.append(f'model_provider = "codexbridge"')
    lines.append("")
    lines.append("[model_providers.codexbridge]")
    lines.append(f'name = "{model}"')
    lines.append(f'base_url = "http://{host}:{port}/v1"')
    lines.append(f'wire_api = "responses"')
    lines.append(f'requires_openai_auth = true')
    lines.append(f'request_max_retries = 1')

    if active_pid:
        lines.append("")
        lines.append(f"# Active provider: {active_pid} ({active_pcfg.get('name', '')})")

    return "\n".join(lines)


def _cc_switch_snippet(host: str, port: int, active: str = "") -> str:
    """Print cc-switch paste blocks."""
    auth_json = _json.dumps({"OPENAI_API_KEY": "codexbridge-local"}, indent=2)
    active_pid = active or pm.config.get("active_provider", "")
    active_pcfg = pm.config.get("providers", {}).get(active_pid, {})
    model = (active_pcfg.get("models") or ["unknown"])[0]

    config_toml = (
        f'model_provider = "codexbridge"\n'
        f'model = "{model}"\n'
        f'\n'
        f'[model_providers.codexbridge]\n'
        f'name = "{model}"\n'
        f'base_url = "http://{host}:{port}/v1"\n'
        f'wire_api = "responses"\n'
        f'requires_openai_auth = true\n'
        f'request_max_retries = 1\n'
    )

    return (
        f"# cc-switch — Add Provider → Codex tab → Custom\n"
        f"\n"
        f"# ───────── auth.json ─────────\n"
        f"{auth_json}\n"
        f"\n"
        f"# ───────── config.toml ─────────\n"
        f"{config_toml}"
    )


# ------------------------------------------------------------------ #
#  Subcommand handling (before app init)
# ------------------------------------------------------------------ #
if len(sys.argv) > 1 and sys.argv[1] in ("print-config", "print-cc-switch"):
    # Load config
    if not os.path.exists(CONFIG_PATH) and os.path.exists(EXAMPLE_PATH):
        shutil.copy2(EXAMPLE_PATH, CONFIG_PATH)
    pm = ProviderManager(CONFIG_PATH)
    host = "127.0.0.1"
    port = pm.config.get("port", 8787)
    # Parse --host and --port from argv
    for i, arg in enumerate(sys.argv[2:], 2):
        if arg == "--host" and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
        elif arg == "--port" and i + 1 < len(sys.argv):
            try:
                port = int(sys.argv[i + 1])
            except ValueError:
                pass

    if sys.argv[1] == "print-config":
        print(_config_snippet(host, port))
    else:
        print(_cc_switch_snippet(host, port))
    sys.exit(0)


# ------------------------------------------------------------------ #
#  FastAPI app
# ------------------------------------------------------------------ #
if not os.path.exists(CONFIG_PATH) and os.path.exists(EXAMPLE_PATH):
    shutil.copy2(EXAMPLE_PATH, CONFIG_PATH)
    print("[CodexBridge] Created config.json from config.example.json")
    print("[CodexBridge] Please edit config.json to add your API keys.")

pm = ProviderManager(CONFIG_PATH)
init_admin(pm, CONFIG_PATH)

app = FastAPI(
    title="CodexBridge",
    description="Local proxy bridging Codex Desktop to any Chat Completions API provider.",
    version="2.0.0",
)

app.include_router(admin_router)


# ------------------------------------------------------------------ #
#  Proxy API Endpoints
# ------------------------------------------------------------------ #

def _probe_response(body: dict):
    """Synthetic response for connection-test probes (cc-switch etc)."""
    import time as _time
    resp_id = f"resp_probe_{int(_time.time())}"
    snapshot = {
        "id": resp_id, "object": "response",
        "created_at": int(_time.time()), "status": "completed",
        "model": body.get("model", "unknown"),
        "output": [], "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
        "parallel_tool_calls": True, "tool_choice": "auto",
        "text": {"format": {"type": "text"}},
        "reasoning": {"effort": None, "summary": None},
        "incomplete_details": None, "error": None, "metadata": None,
    }
    return snapshot


@app.post("/v1/responses")
async def create_response(request: Request):
    """Handle Responses API requests — dispatch to the right provider format."""
    try:
        body = await request.json()
    except Exception:
        return error_envelope(400, "invalid_json", "Failed to parse request body")

    # --- Request logging ---
    import sys
    input_count = len(body.get("input", [])) if isinstance(body.get("input"), list) else 0
    tool_count = len(body.get("tools", []))
    is_stream = body.get("stream", False)
    print(f"  → {body.get('model', '?')} | input:{input_count} tools:{tool_count} stream:{is_stream}", file=sys.stderr, flush=True)

    if not body.get("model"):
        return error_envelope(400, "missing_fields", "Request must include 'model'")

    # Probe detection: cc-switch "test connection" sends {model, stream} with
    # no input/instructions. Return synthetic 200 without hitting upstream.
    has_input = isinstance(body.get("input"), list) and len(body["input"]) > 0
    has_instructions = isinstance(body.get("instructions"), str) and len(body["instructions"]) > 0
    if not has_input and not has_instructions:
        return _probe_response(body)

    provider_id = body.get("provider") or pm.config.get("active_provider")
    provider = pm.get_provider(provider_id)
    if not provider:
        return error_envelope(404, "provider_not_found", f"Provider '{provider_id}' not found")
    if not provider.api_key:
        return error_envelope(400, "missing_api_key",
            f"API key not configured for '{provider_id}'. Set it in config.json.")

    is_stream = body.get("stream", False)
    api_format = getattr(provider, "api_format", "openai")

    # ---- OpenAI format ----
    if api_format == "openai":
        chat_req = provider.to_chat_completions(body)
        if is_stream:
            return StreamingResponse(
                provider.stream(chat_req, request_body=body),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )
        try:
            async with httpx.AsyncClient(timeout=300, proxy=None) as client:
                resp = await client.post(
                    f"{provider.base_url}/chat/completions",
                    json=chat_req, headers=provider.get_headers(),
                )
                if resp.status_code != 200:
                    return error_envelope(resp.status_code, "upstream_error",
                        f"HTTP {resp.status_code}: {resp.text[:300]}")
                return provider.to_responses(resp.json(), request_body=body)
        except httpx.TimeoutException:
            return error_envelope(504, "timeout", "Upstream request timed out (300s)")
        except Exception as e:
            return error_envelope(500, "internal_error", str(e))

    # ---- Anthropic format ----
    elif api_format == "anthropic":
        anthropic_req = provider.to_anthropic_request(body)
        if is_stream:
            return StreamingResponse(
                provider.stream(anthropic_req, request_body=body),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )
        try:
            async with httpx.AsyncClient(timeout=300, proxy=None) as client:
                resp = await client.post(
                    f"{provider.base_url}/v1/messages",
                    json=anthropic_req, headers=provider.get_headers(),
                )
                if resp.status_code != 200:
                    return error_envelope(resp.status_code, "upstream_error",
                        f"HTTP {resp.status_code}: {resp.text[:300]}")
                return provider.to_responses(resp.json(), request_body=body)
        except httpx.TimeoutException:
            return error_envelope(504, "timeout", "Upstream request timed out (300s)")
        except Exception as e:
            return error_envelope(500, "internal_error", str(e))

    else:
        return error_envelope(500, "unknown_format", f"Unknown API format: {api_format}")


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """Passthrough for Chat Completions API — forwards directly to the active provider."""
    try:
        body = await request.json()
    except Exception:
        return error_envelope(400, "invalid_json", "Failed to parse request body")

    provider_id = body.get("provider") or pm.config.get("active_provider")
    provider = pm.get_provider(provider_id)
    if not provider:
        return error_envelope(404, "provider_not_found", f"Provider '{provider_id}' not found")
    if not provider.api_key:
        return error_envelope(400, "missing_api_key",
            f"API key not configured for '{provider_id}'.")

    # Probe: empty messages → synthetic 200
    messages = body.get("messages", [])
    if not messages:
        return {"id": "chatcmpl_probe", "object": "chat.completion",
                "created": 0, "model": body.get("model", "unknown"),
                "choices": [{"index": 0, "message": {"role": "assistant", "content": ""}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}

    is_stream = body.get("stream", False)
    url = f"{provider.base_url}/chat/completions"
    headers = provider.get_headers()

    if is_stream:
        async def _forward_stream():
            async with httpx.AsyncClient(timeout=300, proxy=None) as client:
                async with client.stream("POST", url, json=body, headers=headers) as resp:
                    async for line in resp.aiter_lines():
                        yield line + "\n"
                        if line.strip() == "data: [DONE]":
                            break
        return StreamingResponse(_forward_stream(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    async with httpx.AsyncClient(timeout=300, proxy=None) as client:
        resp = await client.post(url, json=body, headers=headers)
        return JSONResponse(status_code=resp.status_code, content=resp.json())


@app.get("/v1/models")
async def list_models():
    return {"data": pm.get_models()}


@app.get("/v1/providers")
async def list_providers():
    return {"data": pm.list_providers()}


@app.post("/v1/providers/active")
async def set_active_provider(request: Request):
    try:
        body = await request.json()
    except Exception:
        return error_envelope(400, "invalid_json", "Invalid JSON body")
    provider_id = body.get("provider")
    if not provider_id:
        return error_envelope(400, "missing_field", "Provider ID required")
    if not pm.set_active_provider(provider_id):
        return error_envelope(404, "provider_not_found", f"Provider '{provider_id}' not found")
    return {"status": "ok", "active_provider": provider_id}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "active_provider": pm.config.get("active_provider"),
        "providers": list(pm.providers.keys()),
    }


@app.get("/healthz")
async def healthz():
    return {"ok": True, "name": "codexbridge", "version": "2.0.0"}


# ------------------------------------------------------------------ #
#  Static Files & SPA Fallback
# ------------------------------------------------------------------ #

if os.path.isdir(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve SPA: try static file first, fallback to index.html."""
        file_path = os.path.join(STATIC_DIR, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
else:
    @app.get("/")
    async def root():
        return {
            "message": "CodexBridge is running. Build the WebUI with: cd webui && npm run build",
            "docs": "/docs",
        }


if __name__ == "__main__":
    port = pm.config.get("port", 8787)
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        if idx + 1 < len(sys.argv):
            try:
                port = int(sys.argv[idx + 1])
            except ValueError:
                print(f"Error: Invalid port '{sys.argv[idx + 1]}'")
                sys.exit(1)

    active = pm.config.get("active_provider", "none")
    providers = list(pm.providers.keys())
    active_pcfg = pm.config.get("providers", {}).get(active, {})
    active_model = (active_pcfg.get("models") or ["unknown"])[0]
    active_name = active_pcfg.get("name", active)

    print()
    print("  \033[32m●\033[0m CodexBridge v2.0")
    print()
    print(f"  \033[1m服务地址\033[0m    http://localhost:{port}")
    print(f"  \033[1mWebUI\033[0m       http://localhost:{port}")
    print(f"  \033[1m当前模型\033[0m    {active_name} ({active_model})")
    print(f"  \033[1m已配置\033[0m      {len(providers)} 个提供商, {len(pm.get_models())} 个模型")
    print()

    missing = [pid for pid, p in pm.providers.items() if not p.api_key]
    if missing:
        print(f"  \033[33m⚠\033[0m 未配置 API Key: {', '.join(missing)}")
        print()

    print(f"  \033[1mCodex 配置\033[0m  python proxy.py print-config")
    print(f"  \033[1mAPI 文档\033[0m    http://localhost:{port}/docs")
    print()
    print("  \033[2m等待 Codex 连接...\033[0m")
    print()

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
