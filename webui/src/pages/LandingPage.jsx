import Logo from '../components/Logo'
import LanguageSwitcher from '../components/LanguageSwitcher'
import { useTranslation } from '../i18n'

const PROVIDERS = [
  { name: 'DeepSeek', icon: 'DS', color: '#4d6bfe', models: 'deepseek-chat, deepseek-reasoner' },
  { name: 'Qwen', icon: 'QW', color: '#615ced', models: 'qwen-max, qwen-plus, qwen3-coder' },
  { name: 'Kimi', icon: 'KM', color: '#000000', models: 'moonshot-v1-8k/32k/128k, kimi-k2' },
  { name: 'GLM', icon: 'GL', color: '#3451b2', models: 'glm-4-plus, glm-4-flash' },
  { name: 'MiMo', icon: 'MM', color: '#ff6700', models: 'mimo-v2.5-pro, mimo-v2-flash' },
  { name: 'MiniMax', icon: 'MX', color: '#0084ff', models: 'MiniMax-Text-01' },
  { name: 'Baichuan', icon: 'BC', color: '#1a73e8', models: 'Baichuan4, Baichuan3-Turbo' },
  { name: 'Yi', icon: 'YI', color: '#000000', models: 'yi-lightning, yi-large' },
  { name: 'Doubao', icon: 'DB', color: '#3b82f6', models: 'doubao-1.5-pro-256k' },
  { name: 'StepFun', icon: 'SF', color: '#6366f1', models: 'step-2-16k/32k' },
  { name: 'SiliconFlow', icon: 'SF', color: '#0ea5e9', models: 'DeepSeek-V3, Qwen3-235B' },
  { name: 'Anthropic', icon: 'CL', color: '#d97706', models: 'claude-sonnet-4, claude-opus-4' },
]

export default function LandingPage({ onGetStarted }) {
  const { t, lang } = useTranslation()

  const features = [
    { title: t('features.zeroCode'), desc: t('features.zeroCodeDesc'), icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg> },
    { title: t('features.compatible'), desc: t('features.compatibleDesc'), icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" /></svg> },
    { title: t('features.switch'), desc: t('features.switchDesc'), icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg> },
    { title: t('features.streaming'), desc: t('features.streamingDesc'), icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M13 10V3L4 14h7v7l9-11h-7z" /></svg> },
    { title: t('features.secure'), desc: t('features.secureDesc'), icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" /></svg> },
    { title: t('features.extensible'), desc: t('features.extensibleDesc'), icon: <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" /></svg> },
  ]

  return (
    <div className="min-h-screen">
      {/* Nav */}
      <nav className="sticky top-0 z-50 backdrop-blur-md bg-canvas/80 border-b border-hairline">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <Logo />
          <div className="flex items-center gap-3">
            <LanguageSwitcher />
            <a href="https://github.com/352727664/CodexBridge" target="_blank" rel="noopener" className="text-sm text-muted hover:text-ink transition-colors">
              {t('nav.github')}
            </a>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 pt-20 pb-16 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-coral-bg text-coral text-sm font-medium mb-6">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
          </svg>
          {t('hero.badge')}
        </div>
        <h1 className="text-5xl md:text-6xl font-bold text-ink leading-tight mb-6">
          {t('hero.title1')}
          <br />
          <span className="text-coral">{t('hero.title2')}</span>
        </h1>
        <p className="text-lg text-muted max-w-2xl mx-auto mb-10 leading-relaxed">
          {t('hero.desc')}
        </p>
        <div className="flex items-center justify-center gap-4">
          <button onClick={onGetStarted} className="px-6 py-3 bg-coral text-on-primary rounded-xl font-medium hover:bg-coral-active transition-colors shadow-sm cursor-pointer">
            {t('hero.cta')}
          </button>
          <a href="#features" className="px-6 py-3 bg-transparent text-body border border-hairline rounded-xl font-medium hover:bg-surface transition-colors">
            {t('hero.learnMore')}
          </a>
        </div>
      </section>

      {/* Quick Start */}
      <section className="max-w-6xl mx-auto px-6 pb-16">
        <div className="bg-surface-dark rounded-2xl p-8 text-left">
          <h3 className="text-on-dark font-semibold text-sm uppercase tracking-wider mb-4 opacity-60">{t('quickStart.title')}</h3>
          <pre className="text-on-dark/90 text-sm font-mono leading-relaxed overflow-x-auto"><code>{`${t('quickStart.step1')}
git clone https://github.com/352727664/CodexBridge.git
cd CodexBridge && pip install -r requirements.txt
python proxy.py

${t('quickStart.step2')}

${t('quickStart.step3')}`}</code></pre>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="max-w-6xl mx-auto px-6 pb-20">
        <h2 className="text-3xl font-bold text-ink text-center mb-12">{t('features.title')}</h2>
        <div className="grid md:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <div key={i} className="bg-surface rounded-2xl p-6 hover:bg-surface-hover transition-colors">
              <div className="w-10 h-10 rounded-xl bg-coral-bg text-coral flex items-center justify-center mb-4">{f.icon}</div>
              <h3 className="text-lg font-semibold text-ink mb-2">{f.title}</h3>
              <p className="text-sm text-muted leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Supported Providers */}
      <section className="bg-surface py-20">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-ink text-center mb-4">{t('providers.title')}</h2>
          <p className="text-muted text-center mb-12">{t('providers.subtitle')}</p>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {PROVIDERS.map((p) => (
              <div key={p.name} className="bg-canvas rounded-xl p-4 border border-hairline hover:border-coral/30 transition-colors">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-9 h-9 rounded-lg flex items-center justify-center text-white text-xs font-bold" style={{ backgroundColor: p.color }}>
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
          <h2 className="text-3xl font-bold text-ink mb-4">{t('cta.title')}</h2>
          <p className="text-muted mb-8">{t('cta.desc')}</p>
          <button onClick={onGetStarted} className="px-8 py-4 bg-coral text-on-primary rounded-xl font-medium text-lg hover:bg-coral-active transition-colors shadow-sm cursor-pointer">
            {t('cta.button')}
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-hairline py-8">
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between text-sm text-muted">
          <span>{t('footer.copyright')}</span>
          <div className="flex items-center gap-4">
            <a href="https://github.com/352727664/CodexBridge" target="_blank" rel="noopener" className="hover:text-ink transition-colors">{t('nav.github')}</a>
            <a href="/docs" className="hover:text-ink transition-colors">{t('footer.apiDocs')}</a>
          </div>
        </div>
      </footer>
    </div>
  )
}
