import { createContext, useContext, useState, useEffect } from 'react'
import zh from './zh.json'
import en from './en.json'

const translations = { zh, en }

function getInitialLang() {
  const saved = localStorage.getItem('codexbridge-lang')
  if (saved && translations[saved]) return saved
  const browser = navigator.language || 'en'
  return browser.startsWith('zh') ? 'zh' : 'en'
}

const I18nContext = createContext()

export function I18nProvider({ children }) {
  const [lang, setLang] = useState(getInitialLang)

  useEffect(() => {
    localStorage.setItem('codexbridge-lang', lang)
    document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en'
  }, [lang])

  const t = (key, vars = {}) => {
    const keys = key.split('.')
    let value = translations[lang]
    for (const k of keys) {
      if (value && typeof value === 'object') value = value[k]
      else return key
    }
    if (typeof value !== 'string') return key
    return value.replace(/\{(\w+)\}/g, (_, name) => vars[name] ?? `{${name}}`)
  }

  return (
    <I18nContext.Provider value={{ lang, setLang, t }}>
      {children}
    </I18nContext.Provider>
  )
}

export function useTranslation() {
  return useContext(I18nContext)
}
