import { useTranslation } from '../i18n'

export default function LanguageSwitcher() {
  const { lang, setLang } = useTranslation()

  return (
    <button
      onClick={() => setLang(lang === 'zh' ? 'en' : 'zh')}
      className="px-2 py-1 text-xs font-medium text-muted hover:text-ink border border-hairline rounded-md hover:bg-surface transition-colors cursor-pointer"
    >
      {lang === 'zh' ? 'EN' : '中文'}
    </button>
  )
}
