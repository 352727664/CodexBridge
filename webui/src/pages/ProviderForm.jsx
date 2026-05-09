import { useState, useEffect } from 'react'
import { api } from '../lib/api'
import LanguageSwitcher from '../components/LanguageSwitcher'
import { useTranslation } from '../i18n'

const PRESETS = [
  { id: 'deepseek', name: 'DeepSeek', base_url: 'https://api.deepseek.com', model: 'deepseek-chat', has_reasoning: true },
  { id: 'qwen', name: 'Qwen', base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1', model: 'qwen-max', has_reasoning: true },
  { id: 'kimi', name: 'Kimi', base_url: 'https://api.moonshot.cn/v1', model: 'moonshot-v1-128k', has_reasoning: false },
  { id: 'glm', name: 'GLM', base_url: 'https://open.bigmodel.cn/api/paas/v4', model: 'glm-4-plus', has_reasoning: false },
  { id: 'mimo', name: 'MiMo', base_url: 'https://api.xiaomimimo.com/v1', model: 'mimo-v2.5-pro', has_reasoning: true },
  { id: 'minimax', name: 'MiniMax', base_url: 'https://api.minimax.chat/v1', model: 'MiniMax-Text-01', has_reasoning: false },
  { id: 'baichuan', name: 'Baichuan', base_url: 'https://api.baichuan-ai.com/v1', model: 'Baichuan4', has_reasoning: false },
  { id: 'yi', name: 'Yi', base_url: 'https://api.lingyiwanwu.com/v1', model: 'yi-lightning', has_reasoning: false },
  { id: 'doubao', name: 'Doubao', base_url: 'https://ark.cn-beijing.volces.com/api/v3', model: 'doubao-1.5-pro-256k', has_reasoning: true },
  { id: 'stepfun', name: 'StepFun', base_url: 'https://api.stepfun.com/v1', model: 'step-2-16k', has_reasoning: false },
  { id: 'siliconflow', name: 'SiliconFlow', base_url: 'https://api.siliconflow.cn/v1', model: 'deepseek-ai/DeepSeek-V3', has_reasoning: true },
  { id: 'anthropic', name: 'Anthropic', base_url: 'https://api.anthropic.com', model: 'claude-sonnet-4-20250514', has_reasoning: true, api_format: 'anthropic' },
]

export default function ProviderForm({ provider, onBack }) {
  const { t } = useTranslation()
  const isEdit = !!provider?.id

  const [form, setForm] = useState({
    name: '', api_format: 'openai', base_url: '', api_key: '', model: '', has_reasoning: false, note: '', website: '',
  })
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState(null)
  const [showKey, setShowKey] = useState(false)
  const [fetchingModels, setFetchingModels] = useState(false)
  const [fetchedModels, setFetchedModels] = useState([])
  const [showModelDropdown, setShowModelDropdown] = useState(false)
  const [toast, setToast] = useState(null)
  const [showPresets, setShowPresets] = useState(!isEdit)
  const [configText, setConfigText] = useState('')
  const [configError, setConfigError] = useState(null)

  useEffect(() => {
    if (provider?.id) {
      const models = provider.models || []
      setForm({
        name: provider.name || '', api_format: provider.api_format || 'openai', base_url: provider.base_url || '',
        api_key: provider.api_key || '', model: models[0] || '', has_reasoning: provider.has_reasoning || false,
        note: provider.note || '', website: provider.website || '',
      })
    }
  }, [provider])

  useEffect(() => {
    const preview = {
      name: form.name || 'provider', api_format: form.api_format, base_url: form.base_url,
      api_key: form.api_key ? 'sk-***' : '', models: form.model ? [form.model] : [], has_reasoning: form.has_reasoning,
    }
    setConfigText(JSON.stringify(preview, null, 2))
    setConfigError(null)
  }, [form.name, form.api_format, form.base_url, form.api_key, form.model, form.has_reasoning])

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 2500)
  }

  const update = (key, val) => setForm(prev => ({ ...prev, [key]: val }))

  const applyPreset = (preset) => {
    setForm(prev => ({ ...prev, name: preset.name, base_url: preset.base_url, model: preset.model, has_reasoning: preset.has_reasoning, api_format: preset.api_format || 'openai' }))
    setShowPresets(false)
  }

  const handleTest = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const res = await api.testConnection({ base_url: form.base_url, api_key: form.api_key, api_format: form.api_format, model: form.model || '' })
      setTestResult(res)
    } catch (e) {
      setTestResult({ status: 'error', message: e.message })
    }
    setTesting(false)
  }

  const handleFetchModels = async () => {
    setFetchingModels(true)
    try {
      const res = await api.fetchModels({ base_url: form.base_url, api_key: form.api_key, api_format: form.api_format })
      if (res.status === 'ok' && res.models?.length) {
        setFetchedModels(res.models)
        setShowModelDropdown(true)
        showToast(t('providerForm.toastModelsFetched', { count: res.models.length }))
      } else {
        showToast(res.message || t('providerForm.toastNoModels'), 'error')
      }
    } catch (e) {
      showToast(t('providerForm.toastFetchErr') + e.message, 'error')
    }
    setFetchingModels(false)
  }

  const handleSave = async () => {
    if (!form.name.trim()) { showToast(t('providerForm.errNoName'), 'error'); return }
    if (!form.model.trim()) { showToast(t('providerForm.errNoModel'), 'error'); return }

    let configData
    try { configData = JSON.parse(configText) } catch { showToast(t('providerForm.errBadJson'), 'error'); return }

    const data = {
      name: configData.name || form.name.trim(), api_format: form.api_format, base_url: form.base_url.trim(),
      api_key: form.api_key.trim(), models: Array.isArray(configData.models) ? configData.models : [form.model],
      has_reasoning: configData.has_reasoning !== undefined ? configData.has_reasoning : form.has_reasoning,
      note: form.note.trim(), website: form.website.trim(),
    }

    try {
      if (isEdit) { await api.updateProvider(provider.id, data); showToast(t('providerForm.toastUpdated')) }
      else { await api.createProvider(data); showToast(t('providerForm.toastAdded')) }
      onBack()
    } catch (e) {
      showToast(t('providerForm.toastSaveErr') + e.message, 'error')
    }
  }

  const handleConfigChange = (e) => {
    const val = e.target.value
    setConfigText(val)
    try {
      const parsed = JSON.parse(val)
      setConfigError(null)
      if (parsed.name !== undefined) setForm(prev => ({ ...prev, name: parsed.name }))
      if (parsed.models && Array.isArray(parsed.models) && parsed.models.length > 0) setForm(prev => ({ ...prev, model: parsed.models[0] }))
      if (parsed.has_reasoning !== undefined) setForm(prev => ({ ...prev, has_reasoning: parsed.has_reasoning }))
    } catch { setConfigError(t('providerForm.errInvalidJson')) }
  }

  return (
    <div className="min-h-screen bg-canvas">
      {toast && <div className={`fixed top-4 right-4 z-50 px-4 py-2.5 rounded-xl text-sm font-medium shadow-lg animate-fade-in ${toast.type === 'error' ? 'bg-error text-on-primary' : 'bg-surface-dark text-on-dark'}`}>{toast.msg}</div>}

      <header className="border-b border-hairline bg-canvas/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-2xl mx-auto px-6 h-14 flex items-center gap-4">
          <button onClick={onBack} className="w-8 h-8 flex items-center justify-center rounded-lg text-muted hover:text-ink hover:bg-surface transition-colors cursor-pointer">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 12H5m7-7l-7 7 7 7"/></svg>
          </button>
          <h1 className="text-base font-semibold text-ink">{isEdit ? t('providerForm.editTitle') : t('providerForm.addTitle')}</h1>
          <div className="flex-1" />
          <LanguageSwitcher />
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-6 py-8">
        {showPresets && !isEdit && (
          <div className="mb-8 animate-fade-in">
            <h2 className="text-sm font-medium text-muted mb-3">{t('providerForm.presetHint')}</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {PRESETS.map(p => (
                <button key={p.id} onClick={() => applyPreset(p)} className="flex items-center gap-2 px-3 py-2.5 bg-surface rounded-xl text-left hover:bg-surface-hover transition-colors cursor-pointer">
                  <div className="w-7 h-7 rounded-lg bg-coral-bg text-coral flex items-center justify-center text-[10px] font-bold shrink-0">{p.name.charAt(0)}</div>
                  <span className="text-xs font-medium text-ink truncate">{p.name}</span>
                </button>
              ))}
              <button onClick={() => setShowPresets(false)} className="flex items-center gap-2 px-3 py-2.5 border border-dashed border-hairline rounded-xl text-left hover:bg-surface transition-colors cursor-pointer">
                <div className="w-7 h-7 rounded-lg bg-surface flex items-center justify-center text-muted">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                </div>
                <span className="text-xs font-medium text-muted">{t('providerForm.custom')}</span>
              </button>
            </div>
          </div>
        )}

        <div className="space-y-6">
          <div className="flex items-start gap-4">
            <div className="w-16 h-16 rounded-2xl bg-surface flex items-center justify-center text-xl font-bold text-muted shrink-0 mt-1">{form.name ? form.name.charAt(0).toUpperCase() : '?'}</div>
            <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-ink mb-1.5">{t('providerForm.name')}</label>
                <input type="text" value={form.name} onChange={e => update('name', e.target.value)} placeholder={t('providerForm.namePlaceholder')} className="w-full px-3 py-2 bg-canvas border border-hairline rounded-xl text-sm text-ink placeholder:text-muted/50 focus:outline-none focus:border-coral/50 focus:ring-1 focus:ring-coral/20 transition-colors" />
              </div>
              <div>
                <label className="block text-sm font-medium text-ink mb-1.5">{t('providerForm.note')}</label>
                <input type="text" value={form.note} onChange={e => update('note', e.target.value)} placeholder={t('providerForm.notePlaceholder')} className="w-full px-3 py-2 bg-canvas border border-hairline rounded-xl text-sm text-ink placeholder:text-muted/50 focus:outline-none focus:border-coral/50 focus:ring-1 focus:ring-coral/20 transition-colors" />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-ink mb-1.5">{t('providerForm.website')}</label>
            <input type="url" value={form.website} onChange={e => update('website', e.target.value)} placeholder="https://example.com" className="w-full px-3 py-2 bg-canvas border border-hairline rounded-xl text-sm text-ink placeholder:text-muted/50 focus:outline-none focus:border-coral/50 focus:ring-1 focus:ring-coral/20 transition-colors" />
          </div>

          <div>
            <label className="block text-sm font-medium text-ink mb-1.5">{t('providerForm.apiFormat')}</label>
            <div className="flex gap-2">
              {['openai', 'anthropic'].map(fmt => (
                <button key={fmt} onClick={() => update('api_format', fmt)} className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors cursor-pointer ${form.api_format === fmt ? 'bg-coral text-on-primary' : 'bg-surface text-muted hover:bg-surface-hover'}`}>
                  {fmt === 'openai' ? t('providerForm.openaiCompat') : 'Anthropic'}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-ink mb-1.5">{t('providerForm.apiKey')}</label>
            <div className="relative">
              <input type={showKey ? 'text' : 'password'} value={form.api_key} onChange={e => update('api_key', e.target.value)} placeholder="sk-..." className="w-full px-3 py-2 pr-10 bg-canvas border border-hairline rounded-xl text-sm text-ink placeholder:text-muted/50 focus:outline-none focus:border-coral/50 focus:ring-1 focus:ring-coral/20 transition-colors font-mono" />
              <button type="button" onClick={() => setShowKey(!showKey)} className="absolute right-2 top-1/2 -translate-y-1/2 w-7 h-7 flex items-center justify-center rounded-lg text-muted hover:text-ink transition-colors cursor-pointer">
                {showKey ? <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg> : <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-ink mb-1.5">{t('providerForm.baseUrl')}</label>
            <input type="url" value={form.base_url} onChange={e => update('base_url', e.target.value)} placeholder="https://api.example.com/v1" className="w-full px-3 py-2 bg-canvas border border-hairline rounded-xl text-sm text-ink placeholder:text-muted/50 focus:outline-none focus:border-coral/50 focus:ring-1 focus:ring-coral/20 transition-colors" />
            <p className="text-xs text-muted mt-1">{t('providerForm.baseUrlHelp')}</p>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-sm font-medium text-ink">{t('providerForm.model')}</label>
              <button onClick={handleFetchModels} disabled={fetchingModels || !form.base_url || !form.api_key} className="flex items-center gap-1 text-xs text-coral hover:text-coral-active transition-colors disabled:opacity-40 cursor-pointer">
                {fetchingModels ? <svg className="animate-spin" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2v4m0 12v4m-7.07-3.93l2.83-2.83m8.48-8.48l2.83-2.83M2 12h4m12 0h4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83"/></svg> : <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>}
                {t('providerForm.fetchModels')}
              </button>
            </div>
            <div className="relative">
              <input type="text" value={form.model} onChange={e => { update('model', e.target.value); setShowModelDropdown(false) }} onFocus={() => { if (fetchedModels.length) setShowModelDropdown(true) }} placeholder="deepseek-chat" className="w-full px-3 py-2 bg-canvas border border-hairline rounded-xl text-sm text-ink placeholder:text-muted/50 focus:outline-none focus:border-coral/50 focus:ring-1 focus:ring-coral/20 transition-colors" />
              {showModelDropdown && fetchedModels.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-canvas border border-hairline rounded-xl shadow-lg max-h-48 overflow-y-auto">
                  <button onClick={() => setShowModelDropdown(false)} className="absolute top-2 right-2 w-6 h-6 flex items-center justify-center rounded text-muted hover:text-ink cursor-pointer">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </button>
                  {fetchedModels.map(m => (
                    <button key={m} onClick={() => { update('model', m); setShowModelDropdown(false) }} className={`w-full text-left px-3 py-2 text-sm hover:bg-surface transition-colors cursor-pointer ${form.model === m ? 'bg-coral-bg text-coral font-medium' : 'text-ink'}`}>{m}</button>
                  ))}
                </div>
              )}
            </div>
            <p className="text-xs text-muted mt-1">{t('providerForm.modelHelp')}</p>
          </div>

          <div className="flex items-center gap-3">
            <button onClick={() => update('has_reasoning', !form.has_reasoning)} className={`relative w-10 h-6 rounded-full transition-colors cursor-pointer ${form.has_reasoning ? 'bg-coral' : 'bg-hairline'}`}>
              <div className={`absolute top-1 w-4 h-4 rounded-full bg-white shadow-sm transition-all ${form.has_reasoning ? 'left-5' : 'left-1'}`} />
            </button>
            <span className="text-sm font-medium text-ink">{t('providerForm.reasoning')}</span>
          </div>

          <div className="bg-surface rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-ink">{t('providerForm.testSection')}</span>
              <button onClick={handleTest} disabled={testing || !form.base_url || !form.api_key} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-coral text-on-primary rounded-lg hover:bg-coral-active transition-colors disabled:opacity-40 cursor-pointer">
                {testing ? <>{t('providerForm.testing')}</> : <>{t('providerForm.testBtn')}</>}
              </button>
            </div>
            {testResult && (
              <div className={`px-3 py-2 rounded-lg text-xs ${testResult.status === 'ok' ? 'bg-success-bg text-success' : 'bg-error-bg text-error'}`}>
                <span className="font-medium">{testResult.status === 'ok' ? t('providerForm.testOk') : t('providerForm.testFail')}</span>
                {testResult.latency_ms && <span className="ml-2 opacity-70">{testResult.latency_ms}ms</span>}
                {testResult.message && <span className="ml-2">{testResult.message}</span>}
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-ink mb-1.5">{t('providerForm.configPreview')}</label>
            <textarea value={configText} onChange={handleConfigChange} spellCheck={false} className="w-full bg-surface-dark rounded-xl p-4 text-xs text-on-dark/80 font-mono leading-relaxed overflow-x-auto border border-hairline focus:border-coral/50 focus:ring-1 focus:ring-coral/20 transition-colors resize-y min-h-[180px]" rows={12} />
            {configError && <p className="text-xs text-error mt-1">{configError}</p>}
          </div>

          <div className="flex justify-end pt-4 pb-8">
            <button onClick={handleSave} className="flex items-center gap-2 px-6 py-2.5 bg-coral text-on-primary rounded-xl text-sm font-medium hover:bg-coral-active transition-colors cursor-pointer">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>
              {t('providerForm.save')}
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}
