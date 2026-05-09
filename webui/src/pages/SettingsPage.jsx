import { useState, useEffect } from 'react'
import { api } from '../lib/api'
import LanguageSwitcher from '../components/LanguageSwitcher'
import { useTranslation } from '../i18n'

export default function SettingsPage({ onBack }) {
  const { t } = useTranslation()
  const [settings, setSettings] = useState({ active_provider: '', port: 8787 })
  const [providers, setProviders] = useState([])
  const [toast, setToast] = useState(null)
  const [saving, setSaving] = useState(false)

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 2500)
  }

  useEffect(() => {
    api.getSettings().then(setSettings).catch(() => {})
    api.listProviders().then(res => setProviders(res.data || [])).catch(() => {})
  }, [])

  const handleSave = async () => {
    setSaving(true)
    try {
      await api.updateSettings(settings)
      showToast(t('settings.toastSaved'))
    } catch (e) {
      showToast(t('settings.toastSaveErr') + e.message, 'error')
    }
    setSaving(false)
  }

  return (
    <div className="min-h-screen bg-canvas">
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-2.5 rounded-xl text-sm font-medium shadow-lg animate-fade-in ${toast.type === 'error' ? 'bg-error text-on-primary' : 'bg-surface-dark text-on-dark'}`}>
          {toast.msg}
        </div>
      )}

      <header className="border-b border-hairline bg-canvas/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-2xl mx-auto px-6 h-14 flex items-center gap-4">
          <button onClick={onBack} className="w-8 h-8 flex items-center justify-center rounded-lg text-muted hover:text-ink hover:bg-surface transition-colors cursor-pointer">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 12H5m7-7l-7 7 7 7"/></svg>
          </button>
          <h1 className="text-base font-semibold text-ink">{t('settings.title')}</h1>
          <div className="flex-1" />
          <LanguageSwitcher />
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-8 space-y-8">
        <section>
          <h2 className="text-sm font-medium text-muted uppercase tracking-wider mb-4">{t('settings.server')}</h2>
          <div className="bg-surface rounded-xl p-5 space-y-5">
            <div>
              <label className="block text-sm font-medium text-ink mb-1.5">{t('settings.port')}</label>
              <input type="number" value={settings.port} onChange={e => setSettings(prev => ({ ...prev, port: parseInt(e.target.value) || 8787 }))} className="w-full px-3 py-2 bg-canvas border border-hairline rounded-xl text-sm text-ink focus:outline-none focus:border-coral/50 focus:ring-1 focus:ring-coral/20 transition-colors" />
              <p className="text-xs text-muted mt-1">{t('settings.portHelp')}</p>
            </div>
          </div>
        </section>

        <section>
          <h2 className="text-sm font-medium text-muted uppercase tracking-wider mb-4">{t('settings.defaultProvider')}</h2>
          <div className="bg-surface rounded-xl p-5">
            <select value={settings.active_provider} onChange={e => setSettings(prev => ({ ...prev, active_provider: e.target.value }))} className="w-full px-3 py-2 bg-canvas border border-hairline rounded-xl text-sm text-ink focus:outline-none focus:border-coral/50 focus:ring-1 focus:ring-coral/20 transition-colors cursor-pointer">
              <option value="">{t('settings.notSelected')}</option>
              {providers.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
            <p className="text-xs text-muted mt-1">{t('settings.providerHelp')}</p>
          </div>
        </section>

        <section>
          <h2 className="text-sm font-medium text-muted uppercase tracking-wider mb-4">{t('settings.about')}</h2>
          <div className="bg-surface rounded-xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-body">{t('settings.version')}</span>
              <span className="text-sm text-ink font-mono">2.0.0</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-body">{t('settings.license')}</span>
              <span className="text-sm text-ink">CC BY-NC-SA 4.0</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-body">{t('settings.github')}</span>
              <a href="https://github.com/352727664/CodexBridge" target="_blank" rel="noopener" className="text-sm text-coral hover:text-coral-active transition-colors">{t('settings.viewRepo')}</a>
            </div>
          </div>
        </section>

        <div className="flex justify-end pb-8">
          <button onClick={handleSave} disabled={saving} className="flex items-center gap-2 px-6 py-2.5 bg-coral text-on-primary rounded-xl text-sm font-medium hover:bg-coral-active transition-colors disabled:opacity-50 cursor-pointer">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
            {saving ? t('settings.saving') : t('settings.saveBtn')}
          </button>
        </div>
      </main>
    </div>
  )
}
