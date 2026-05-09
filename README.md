# CodexBridge — Use Any AI Model with Codex Desktop

> **Codex Custom Model** | **Codex Third-Party API** | **Codex Alternative Models** | **OpenAI Codex Proxy**

[中文文档](README_zh.md)

OpenAI Codex Desktop only supports Responses API and cannot directly use third-party models. CodexBridge is a local proxy that translates Codex's Responses API to Chat Completions format, letting you use **DeepSeek**, **MiMo**, **Qwen**, **Kimi**, **GLM**, **Baichuan**, **Doubao**, **Claude** and more in Codex.

```
Codex (Responses API) → CodexBridge → AI Provider (Chat Completions API)
```

## Supported Models

| Provider | Models | Reasoning |
|----------|--------|-----------|
| **DeepSeek** | deepseek-chat, deepseek-reasoner, DeepSeek-V3, DeepSeek-R1 | ✅ |
| **Qwen** | qwen-max, qwen-plus, qwen3-235b-a22b, qwen3-coder-plus | ✅ |
| **Kimi** | moonshot-v1-8k/32k/128k, kimi-k2 | - |
| **GLM** | glm-4-plus, glm-4-flash, glm-z2-airx | - |
| **MiMo** | mimo-v2.5-pro, mimo-v2-flash | ✅ |
| **MiniMax** | MiniMax-Text-01, abab6.5-chat | - |
| **Baichuan** | Baichuan4, Baichuan3-Turbo | - |
| **Yi** | yi-lightning, yi-large, yi-spark | - |
| **Doubao** | doubao-1.5-pro-256k, doubao-1.5-lite-32k | ✅ |
| **StepFun** | step-2-16k/32k, step-1-flash | - |
| **SiliconFlow** | DeepSeek-V3, Qwen3-235B, DeepSeek-R1 | ✅ |
| **Anthropic (Claude)** | claude-sonnet-4, claude-opus-4 | ✅ |
| **OpenAI Compatible** | Any OpenAI-compatible API | ✅ |

## Get Started in 3 Steps

```bash
# 1. Install and start
git clone https://github.com/352727664/CodexBridge.git
cd CodexBridge && pip install -r requirements.txt
python proxy.py

# 2. Open http://localhost:8787, add your API Key and save

# 3. Open Codex Desktop and use directly
```

## WebUI Dashboard

After starting the service, visit `http://localhost:8787` for the built-in WebUI dashboard:

- **Add/Edit Providers** — Choose preset templates or custom config, just fill in your API Key
- **One-Click Switch** — Switch between providers and models instantly
- **Test Connection** — Send test requests to verify API connectivity and latency
- **Import Config** — Auto-read existing config.json configurations
- **Duplicate Provider** — Quickly clone existing configs for modification
- **Settings** — Modify port, default provider, and other global settings

## Configuration

You can also directly edit `config.json` with only the providers you need:

```json
{
  "active_provider": "deepseek",
  "port": 8787,
  "providers": {
    "deepseek": {
      "name": "DeepSeek",
      "base_url": "https://api.deepseek.com",
      "api_key": "sk-xxx",
      "models": ["deepseek-chat", "deepseek-reasoner"],
      "has_reasoning": true
    },
    "qwen": {
      "name": "Qwen",
      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "api_key": "sk-xxx",
      "models": ["qwen-max", "qwen-plus"],
      "has_reasoning": true
    }
  }
}
```

**Configuration Fields:**

| Field | Description |
|-------|-------------|
| `active_provider` | Default provider ID (matches the providers key) |
| `port` | Service port, default 8787 |
| `base_url` | Provider API address (without `/chat/completions`, auto-appended) |
| `api_key` | API key |
| `models` | List of models supported by this provider |
| `has_reasoning` | Whether the model supports reasoning content (reasoning_content field) |

## Using with Codex Desktop

1. Start CodexBridge: `python proxy.py`
2. Open http://localhost:8787, add your API Key and save
3. Open Codex Desktop and use directly

CodexBridge automatically writes the config to `~/.codex/config.toml` and `~/.codex/auth.json` when you save — no manual steps needed.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/responses` | POST | Send conversation request (core endpoint) |
| `/v1/models` | GET | List all available models |
| `/v1/providers` | GET | List all configured providers |
| `/v1/providers/active` | POST | Switch active provider |
| `/health` | GET | Health check |
| `/docs` | GET | Swagger API docs |

## Adding New Providers

No code changes needed! Just add a new entry to `config.json` providers as long as the provider supports OpenAI-compatible format. You can also add directly through the WebUI dashboard.

## Command Line Arguments

```bash
python proxy.py --port 9000    # Custom port
```

## Development

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start backend
python proxy.py

# In another terminal, develop frontend
cd webui
npm install
npm run dev    # Dev mode with auto-proxy
npm run build  # Build production version
```

## Project Structure

```
CodexBridge/
├── providers/
│   ├── __init__.py             # Provider registration
│   ├── openai_provider.py      # Universal OpenAI-compatible Provider
│   └── anthropic_provider.py   # Anthropic Messages API Provider
├── provider_manager.py         # Provider manager
├── proxy.py                    # FastAPI main service
├── admin_api.py                # WebUI management API
├── webui/
│   └── dist/                   # Built frontend static files
├── config.example.json         # Config template (with all providers)
├── config.json                 # Your config (git ignored)
├── requirements.txt            # Python dependencies
├── start.sh                    # Start script
├── README.md                   # English documentation
├── README_zh.md                # Chinese documentation
├── LICENSE
└── .gitignore
```

## License

CC BY-NC-SA 4.0 — No commercial use
