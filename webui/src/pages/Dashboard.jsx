import { useState, useEffect, useCallback } from 'react'
import { api } from '../lib/api'
import Logo from '../components/Logo'

function ProviderCard({ provider, onEnable, onEdit, onDuplicate, onDelete, onTest }) {
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState(null)

  const handleTest = async () => {
    setTesting(true)
    setTestResult(null)
    try {
      const res = await api.testConnection({
        base_url: provider.base_url,
        api_key: provider.api_key,
        api_format: provider.api_format,
        model: provider.models[0] || '',
      })
      setTestResult(res)
    } catch (e) {
      setTestResult({ status: 'error', message: e.message })
    }
    setTesting(false)
  }

  return (
    <div
      className={`bg-canvas rounded-xl border transition-all duration-200 ${
        provider.is_active ? 'border-coral shadow-sm' : 'border-hairline hover:border-coral/30'
      }`}
    >
      <div className="flex items-center gap-4 p-4">
        {/* Avatar */}
        <div className={`w-11 h-11 rounded-xl flex items-center justify-center text-sm font-bold shrink-0 ${
          provider.is_active
            ? 'bg-coral text-on-primary'
            : 'bg-surface text-muted'
        }`}>
          {provider.name.charAt(0).toUpperCase()}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-ink truncate">{provider.name}</h3>
            {provider.is_active && (
              <span className="px-1.5 py-0.5 text-[10px] font-medium bg-coral-bg text-coral rounded">
                启用中
              </span>
            )}
          </div>
          <p className="text-xs text-muted truncate mt-0.5">{provider.base_url || '未配置'}</p>
          {provider.note && (
            <p className="text-xs text-muted/60 truncate mt-0.5">{provider.note}</p>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 shrink-0">
          {!provider.is_active && (
            <button
              onClick={() => onEnable(provider.id)}
              className="px-3 py-1.5 text-xs font-medium bg-coral text-on-primary rounded-lg hover:bg-coral-active transition-colors cursor-pointer"
            >
              启用
            </button>
          )}
          <button
            onClick={() => onEdit(provider)}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-muted hover:text-ink hover:bg-surface transition-colors cursor-pointer"
            title="编辑"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          </button>
          <button
            onClick={() => onDuplicate(provider.id)}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-muted hover:text-ink hover:bg-surface transition-colors cursor-pointer"
            title="复制"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
          </button>
          <button
            onClick={handleTest}
            disabled={testing}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-muted hover:text-ink hover:bg-surface transition-colors cursor-pointer disabled:opacity-50"
            title="测试连接"
          >
            {testing ? (
              <svg className="animate-spin" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2v4m0 12v4m-7.07-3.93l2.83-2.83m8.48-8.48l2.83-2.83M2 12h4m12 0h4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83"/></svg>
            ) : (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
            )}
          </button>
          <button
            onClick={() => onDelete(provider.id, provider.name)}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-muted hover:text-error hover:bg-error-bg transition-colors cursor-pointer"
            title="删除"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
          </button>
        </div>
      </div>

      {/* Test Result */}
      {testResult && (
        <div className={`mx-4 mb-3 px-3 py-2 rounded-lg text-xs ${
          testResult.status === 'ok'
            ? 'bg-success-bg text-success'
            : 'bg-error-bg text-error'
        }`}>
          <span className="font-medium">
            {testResult.status === 'ok' ? '连接成功' : '连接失败'}
          </span>
          {testResult.latency_ms && <span className="ml-2 opacity-70">{testResult.latency_ms}ms</span>}
          {testResult.message && <span className="ml-2">{testResult.message}</span>}
        </div>
      )}
    </div>
  )
}

function DeleteDialog({ name, onConfirm, onCancel }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
      <div className="bg-canvas rounded-2xl p-6 w-[360px] shadow-xl animate-fade-in">
        <h3 className="text-lg font-semibold text-ink mb-2">确认删除</h3>
        <p className="text-sm text-muted mb-6">确定要删除供应商「{name}」吗？此操作不可撤销。</p>
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm text-body border border-hairline rounded-lg hover:bg-surface transition-colors cursor-pointer"
          >
            取消
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 text-sm text-on-primary bg-error rounded-lg hover:opacity-90 transition-colors cursor-pointer"
          >
            删除
          </button>
        </div>
      </div>
    </div>
  )
}

function ImportDialog({ onImport, onCancel }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
      <div className="bg-canvas rounded-2xl p-6 w-[400px] shadow-xl animate-fade-in">
        <h3 className="text-lg font-semibold text-ink mb-2">导入配置</h3>
        <p className="text-sm text-muted mb-6">
          将从 config.json 导入已有配置，包括所有已配置的 API Key 和提供商信息。
        </p>
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm text-body border border-hairline rounded-lg hover:bg-surface transition-colors cursor-pointer"
          >
            取消
          </button>
          <button
            onClick={onImport}
            className="px-4 py-2 text-sm text-on-primary bg-coral rounded-lg hover:bg-coral-active transition-colors cursor-pointer"
          >
            导入
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Dashboard({ onNavigate }) {
  const [providers, setProviders] = useState([])
  const [activeProvider, setActiveProvider] = useState('')
  const [loading, setLoading] = useState(true)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [showImport, setShowImport] = useState(false)
  const [toast, setToast] = useState(null)
  const [serverStatus, setServerStatus] = useState(null)

  useEffect(() => {
    api.health().then(d => setServerStatus(d)).catch(() => setServerStatus(null))
  }, [])

  const showToast = (msg, type = 'success') => {
    setToast({ msg, type })
    setTimeout(() => setToast(null), 2500)
  }

  const loadProviders = useCallback(async () => {
    try {
      const res = await api.listProviders()
      setProviders(res.data || [])
      setActiveProvider(res.active_provider || '')
    } catch (e) {
      showToast('加载失败: ' + e.message, 'error')
    }
    setLoading(false)
  }, [])

  useEffect(() => { loadProviders() }, [loadProviders])

  const handleEnable = async (id) => {
    try {
      await api.enableProvider(id)
      setActiveProvider(id)
      showToast('已切换提供商')
    } catch (e) {
      showToast('操作失败: ' + e.message, 'error')
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    try {
      await api.deleteProvider(deleteTarget.id)
      setDeleteTarget(null)
      showToast('已删除')
      loadProviders()
    } catch (e) {
      showToast('删除失败: ' + e.message, 'error')
    }
  }

  const handleDuplicate = async (id) => {
    try {
      const res = await api.duplicateProvider(id)
      showToast(`已复制为「${res.provider.name}」`)
      loadProviders()
    } catch (e) {
      showToast('复制失败: ' + e.message, 'error')
    }
  }

  const handleImport = async () => {
    try {
      const res = await api.getRawConfig()
      const config = res.config
      if (config?.providers) {
        for (const [pid, pcfg] of Object.entries(config.providers)) {
          const exists = providers.some(p => p.id === pid)
          if (!exists) {
            await api.createProvider({
              name: pcfg.name || pid,
              api_format: pcfg.api_format || 'openai',
              base_url: pcfg.base_url || '',
              api_key: pcfg.api_key || '',
              models: pcfg.models || [],
              has_reasoning: pcfg.has_reasoning || false,
              note: pcfg.note || '',
              website: pcfg.website || '',
            })
          }
        }
        await loadProviders()
        setShowImport(false)
        showToast('导入成功')
      }
    } catch (e) {
      showToast('导入失败: ' + e.message, 'error')
    }
  }

  return (
    <div className="min-h-screen bg-canvas">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-2.5 rounded-xl text-sm font-medium shadow-lg animate-fade-in ${
          toast.type === 'error' ? 'bg-error text-on-primary' : 'bg-surface-dark text-on-dark'
        }`}>
          {toast.msg}
        </div>
      )}

      {/* Delete Dialog */}
      {deleteTarget && (
        <DeleteDialog
          name={deleteTarget.name}
          onConfirm={handleDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}

      {/* Import Dialog */}
      {showImport && (
        <ImportDialog onImport={handleImport} onCancel={() => setShowImport(false)} />
      )}

      {/* Header */}
      <header className="border-b border-hairline bg-canvas/80 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-4xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Logo size="sm" />
            <span className="text-xs text-muted">管理面板</span>
          </div>
          <div className="flex items-center gap-3">
            {serverStatus && (
              <span className="text-xs text-muted flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse-dot" />
                服务运行中
              </span>
            )}
            <button
              onClick={() => onNavigate('settings')}
              className="w-8 h-8 flex items-center justify-center rounded-lg text-muted hover:text-ink hover:bg-surface transition-colors cursor-pointer"
              title="设置"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
            </button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-6 py-8">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-6 h-6 border-2 border-coral border-t-transparent rounded-full animate-spin" />
          </div>
        ) : providers.length === 0 ? (
          /* Empty State */
          <div className="flex flex-col items-center justify-center py-20 animate-fade-in">
            <div className="w-20 h-20 rounded-full bg-surface flex items-center justify-center mb-6">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-muted">
                <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <path d="M23 21v-2a4 4 0 00-3-3.87" />
                <path d="M16 3.13a4 4 0 010 7.75" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-ink mb-2">还没有添加任何供应商</h2>
            <p className="text-sm text-muted mb-8 text-center max-w-md">
              如果你已有配置，请点击「导入当前配置」，所有数据将安全保存在 default 供应商中
            </p>
            <div className="flex flex-col gap-3">
              <button
                onClick={() => setShowImport(true)}
                className="flex items-center gap-2 px-5 py-2.5 bg-coral text-on-primary rounded-xl font-medium hover:bg-coral-active transition-colors cursor-pointer"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                导入当前配置
              </button>
              <button
                onClick={() => onNavigate('provider-form')}
                className="flex items-center gap-2 px-5 py-2.5 text-body border border-hairline rounded-xl font-medium hover:bg-surface transition-colors cursor-pointer"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                添加供应商
              </button>
            </div>
          </div>
        ) : (
          /* Provider List */
          <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-xl font-semibold text-ink">供应商</h1>
                <p className="text-sm text-muted mt-0.5">{providers.length} 个已配置</p>
              </div>
              <button
                onClick={() => onNavigate('provider-form')}
                className="flex items-center gap-1.5 px-4 py-2 bg-coral text-on-primary rounded-xl text-sm font-medium hover:bg-coral-active transition-colors cursor-pointer"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                添加
              </button>
            </div>
            <div className="space-y-3">
              {providers.map((p) => (
                <ProviderCard
                  key={p.id}
                  provider={p}
                  onEnable={handleEnable}
                  onEdit={(prov) => onNavigate('provider-form', prov)}
                  onDuplicate={handleDuplicate}
                  onDelete={(id, name) => setDeleteTarget({ id, name })}
                  onTest={() => {}}
                />
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
