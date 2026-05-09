import Logo from '../components/Logo'

const PROVIDERS = [
  { name: 'DeepSeek', icon: 'DS', color: '#4d6bfe', models: 'deepseek-chat, deepseek-reasoner' },
  { name: 'Qwen (通义千问)', icon: 'QW', color: '#615ced', models: 'qwen-max, qwen-plus, qwen3-coder' },
  { name: 'Kimi', icon: 'KM', color: '#000000', models: 'moonshot-v1-8k/32k/128k, kimi-k2' },
  { name: 'GLM (智谱)', icon: 'GL', color: '#3451b2', models: 'glm-4-plus, glm-4-flash' },
  { name: 'MiMo (小米)', icon: 'MM', color: '#ff6700', models: 'mimo-v2.5-pro, mimo-v2-flash' },
  { name: 'MiniMax', icon: 'MX', color: '#0084ff', models: 'MiniMax-Text-01' },
  { name: 'Baichuan (百川)', icon: 'BC', color: '#1a73e8', models: 'Baichuan4, Baichuan3-Turbo' },
  { name: 'Yi (零一万物)', icon: 'YI', color: '#000000', models: 'yi-lightning, yi-large' },
  { name: 'Doubao (豆包)', icon: 'DB', color: '#3b82f6', models: 'doubao-1.5-pro-256k' },
  { name: 'StepFun (阶跃星辰)', icon: 'SF', color: '#6366f1', models: 'step-2-16k/32k' },
  { name: 'SiliconFlow (硅基流动)', icon: 'SF', color: '#0ea5e9', models: 'DeepSeek-V3, Qwen3-235B' },
  { name: 'Anthropic (Claude)', icon: 'CL', color: '#d97706', models: 'claude-sonnet-4, claude-opus-4' },
]

export default function LandingPage({ onGetStarted }) {
  return (
    <div className="min-h-screen">
      {/* Nav */}
      <nav className="sticky top-0 z-50 backdrop-blur-md bg-canvas/80 border-b border-hairline">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <Logo />
          <a
            href="https://github.com/yourname/CodexBridge"
            target="_blank"
            rel="noopener"
            className="text-sm text-muted hover:text-ink transition-colors"
          >
            GitHub
          </a>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 pt-20 pb-16 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-coral-bg text-coral text-sm font-medium mb-6">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
          </svg>
          开源免费 &middot; 本地运行 &middot; 隐私安全
        </div>
        <h1 className="text-5xl md:text-6xl font-bold text-ink leading-tight mb-6">
          让 Codex 桌面版
          <br />
          <span className="text-coral">用上所有 AI 模型</span>
        </h1>
        <p className="text-lg text-muted max-w-2xl mx-auto mb-10 leading-relaxed">
          Codex 桌面版只支持 Responses API。CodexBridge 作为本地代理，将 Responses API 翻译为各家 AI 提供商的 Chat Completions 格式，
          让你在 Codex 中使用 DeepSeek、MiMo、通义千问、Kimi、智谱等任意模型。
        </p>
        <div className="flex items-center justify-center gap-4">
          <button
            onClick={onGetStarted}
            className="px-6 py-3 bg-coral text-on-primary rounded-xl font-medium hover:bg-coral-active transition-colors shadow-sm cursor-pointer"
          >
            进入控制台
          </button>
          <a
            href="#features"
            className="px-6 py-3 bg-transparent text-body border border-hairline rounded-xl font-medium hover:bg-surface transition-colors"
          >
            了解更多
          </a>
        </div>
      </section>

      {/* Quick Start */}
      <section className="max-w-6xl mx-auto px-6 pb-16">
        <div className="bg-surface-dark rounded-2xl p-8 text-left">
          <h3 className="text-on-dark font-semibold text-sm uppercase tracking-wider mb-4 opacity-60">三步开始</h3>
          <pre className="text-on-dark/90 text-sm font-mono leading-relaxed overflow-x-auto"><code>{`# 1. 安装并启动
git clone https://github.com/yourname/CodexBridge.git
cd CodexBridge && pip install -r requirements.txt
python proxy.py

# 2. 打开 http://localhost:8787，添加你的 API Key 并保存

# 3. 打开 Codex 桌面版，直接使用`}</code></pre>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="max-w-6xl mx-auto px-6 pb-20">
        <h2 className="text-3xl font-bold text-ink text-center mb-12">为什么选择 CodexBridge</h2>
        <div className="grid md:grid-cols-3 gap-6">
          {[
            {
              title: '零代码配置',
              desc: '通过 WebUI 管理面板添加 API Key，无需手动编辑 JSON 文件。支持导入已有配置。',
              icon: (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
              ),
            },
            {
              title: '全面兼容',
              desc: '支持 OpenAI 和 Anthropic 两种 API 格式，覆盖 14+ 家 AI 提供商，包括推理和工具调用。',
              icon: (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" /></svg>
              ),
            },
            {
              title: '一键切换',
              desc: '在控制台中一键启用不同提供商和模型，无需重启服务，配置即时生效。',
              icon: (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
              ),
            },
            {
              title: '流式响应',
              desc: '完整支持 SSE 流式输出，包括推理内容（thinking/reasoning）和工具调用的流式传输。',
              icon: (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
              ),
            },
            {
              title: '安全本地运行',
              desc: '所有请求在本地处理，API Key 存储在本地 config.json 中，不会上传到任何第三方服务器。',
              icon: (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" /></svg>
              ),
            },
            {
              title: '易于扩展',
              desc: '只需在 config.json 中添加一行配置即可接入新的 OpenAI 兼容 API，无需编写代码。',
              icon: (
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" /></svg>
              ),
            },
          ].map((f, i) => (
            <div key={i} className="bg-surface rounded-2xl p-6 hover:bg-surface-hover transition-colors">
              <div className="w-10 h-10 rounded-xl bg-coral-bg text-coral flex items-center justify-center mb-4">
                {f.icon}
              </div>
              <h3 className="text-lg font-semibold text-ink mb-2">{f.title}</h3>
              <p className="text-sm text-muted leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Supported Providers */}
      <section className="bg-surface py-20">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-ink text-center mb-4">支持的 AI 提供商</h2>
          <p className="text-muted text-center mb-12">一站式接入主流 AI 服务</p>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {PROVIDERS.map((p) => (
              <div key={p.name} className="bg-canvas rounded-xl p-4 border border-hairline hover:border-coral/30 transition-colors">
                <div className="flex items-center gap-3 mb-2">
                  <div
                    className="w-9 h-9 rounded-lg flex items-center justify-center text-white text-xs font-bold"
                    style={{ backgroundColor: p.color }}
                  >
                    {p.icon}
                  </div>
                  <span className="text-sm font-medium text-ink truncate">{p.name}</span>
                </div>
                <p className="text-xs text-muted truncate">{p.models}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 text-center">
        <div className="max-w-2xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-ink mb-4">准备好开始了吗？</h2>
          <p className="text-muted mb-8">三步启动：安装依赖、配置 API Key、启动服务</p>
          <button
            onClick={onGetStarted}
            className="px-8 py-4 bg-coral text-on-primary rounded-xl font-medium text-lg hover:bg-coral-active transition-colors shadow-sm cursor-pointer"
          >
            进入控制台
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-hairline py-8">
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between text-sm text-muted">
          <span>CodexBridge &copy; 2026 &middot; MIT License</span>
          <div className="flex items-center gap-4">
            <a href="https://github.com/yourname/CodexBridge" target="_blank" rel="noopener" className="hover:text-ink transition-colors">GitHub</a>
            <a href="/docs" className="hover:text-ink transition-colors">API 文档</a>
          </div>
        </div>
      </footer>
    </div>
  )
}
