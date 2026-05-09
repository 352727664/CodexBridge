# CodexBridge — 让 Codex 用上 DeepSeek、MiMo、通义千问等国产大模型

> **Codex 自定义模型** | **Codex 第三方 API** | **Codex 国产模型接入** | **OpenAI Codex 代理**

[English](README.md)

OpenAI Codex 桌面版只支持 Responses API，无法直接使用国产大模型。CodexBridge 是一个本地代理，将 Codex 的 Responses API 翻译为 Chat Completions 格式，让你在 Codex 中使用 **DeepSeek**、**MiMo**、**通义千问**、**Kimi**、**智谱**、**百川**、**豆包**、**Claude** 等任意模型。

```
Codex (Responses API) → CodexBridge → AI 提供商 (Chat Completions API)
```

## 支持的模型

| 提供商 | 模型 | 推理 |
|--------|------|------|
| **DeepSeek** | deepseek-chat, deepseek-reasoner, DeepSeek-V3, DeepSeek-R1 | ✅ |
| **Qwen (通义千问)** | qwen-max, qwen-plus, qwen3-235b-a22b, qwen3-coder-plus | ✅ |
| **Kimi (月之暗面)** | moonshot-v1-8k/32k/128k, kimi-k2 | - |
| **GLM (智谱)** | glm-4-plus, glm-4-flash, glm-z2-airx | - |
| **MiMo (小米)** | mimo-v2.5-pro, mimo-v2-flash | ✅ |
| **MiniMax** | MiniMax-Text-01, abab6.5-chat | - |
| **Baichuan (百川)** | Baichuan4, Baichuan3-Turbo | - |
| **Yi (零一万物)** | yi-lightning, yi-large, yi-spark | - |
| **Doubao (豆包)** | doubao-1.5-pro-256k, doubao-1.5-lite-32k | ✅ |
| **StepFun (阶跃星辰)** | step-2-16k/32k, step-1-flash | - |
| **SiliconFlow (硅基流动)** | DeepSeek-V3, Qwen3-235B, DeepSeek-R1 | ✅ |
| **Anthropic (Claude)** | claude-sonnet-4, claude-opus-4 | ✅ |
| **OpenAI Compatible** | 自定义任何 OpenAI 兼容 API | ✅ |

## 三步开始

```bash
# 1. 安装并启动
git clone https://github.com/352727664/CodexBridge.git
cd CodexBridge && pip install -r requirements.txt
python proxy.py

# 2. 打开 http://localhost:8787，添加 API Key 并保存

# 3. 打开 Codex 桌面版，直接使用
```

## WebUI 管理面板

启动服务后，浏览器访问 `http://localhost:8787` 即可使用内置的 WebUI 管理面板：

- **添加/编辑提供商** — 选择预设模板或自定义配置，填写 API Key 即可
- **一键启用** — 在列表中切换当前活跃的提供商
- **测试连接** — 发送测试请求验证 API 连通性和延迟
- **导入配置** — 自动读取 config.json 中已有配置
- **复制提供商** — 快速克隆已有配置进行修改
- **设置管理** — 修改端口、默认提供商等全局设置

## 配置说明

也可以直接编辑 `config.json`，只填你需要的提供商：

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
      "name": "Qwen (通义千问)",
      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "api_key": "sk-xxx",
      "models": ["qwen-max", "qwen-plus"],
      "has_reasoning": true
    }
  }
}
```

**配置字段说明：**

| 字段 | 说明 |
|------|------|
| `active_provider` | 默认使用的提供商 ID（对应 providers 的 key） |
| `port` | 服务端口，默认 8787 |
| `base_url` | 提供商 API 地址（不含 `/chat/completions`，会自动拼接） |
| `api_key` | API 密钥 |
| `models` | 该提供商支持的模型列表 |
| `has_reasoning` | 模型是否支持推理内容（reasoning_content 字段） |

## 在 Codex 桌面版中使用

1. 启动 CodexBridge: `python proxy.py`
2. 打开 http://localhost:8787，添加 API Key 并保存
3. 打开 Codex 桌面版，直接使用

CodexBridge 会在保存时自动将配置写入 `~/.codex/config.toml` 和 `~/.codex/auth.json`，无需手动操作。

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/v1/responses` | POST | 发送对话请求（核心端点） |
| `/v1/models` | GET | 列出所有可用模型 |
| `/v1/providers` | GET | 列出所有已配置的提供商 |
| `/v1/providers/active` | POST | 切换当前活跃提供商 |
| `/health` | GET | 健康检查 |
| `/docs` | GET | Swagger 交互文档 |

## 添加新提供商

不需要写代码！只要提供商支持 OpenAI 兼容格式，在 `config.json` 的 `providers` 中加一个新条目即可。也可以通过 WebUI 管理面板直接添加。

## 命令行参数

```bash
python proxy.py --port 9000    # 自定义端口
```

## 开发

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 启动后端
python proxy.py

# 在另一个终端，开发前端
cd webui
npm install
npm run dev    # 开发模式，自动代理到后端
npm run build  # 构建生产版本
```

## 项目结构

```
CodexBridge/
├── providers/
│   ├── __init__.py             # Provider 注册
│   ├── openai_provider.py      # 通用 OpenAI 兼容 Provider
│   └── anthropic_provider.py   # Anthropic Messages API Provider
├── provider_manager.py         # 提供商管理器
├── proxy.py                    # FastAPI 主服务
├── admin_api.py                # WebUI 管理 API
├── webui/
│   └── dist/                   # 构建后的前端静态文件
├── config.example.json         # 配置模板（含所有提供商）
├── config.json                 # 你的配置（git ignored）
├── requirements.txt            # Python 依赖
├── start.sh                    # 启动脚本
├── README.md
├── LICENSE
└── .gitignore
```

## License

CC BY-NC-SA 4.0 — 禁止商业使用
