export default function Logo({ size = 'md', showText = true, className = '' }) {
  const sizes = {
    sm: { icon: 16, box: 'w-7 h-7', text: 'text-sm' },
    md: { icon: 18, box: 'w-8 h-8', text: 'text-lg' },
    lg: { icon: 24, box: 'w-10 h-10', text: 'text-xl' },
  }
  const s = sizes[size] || sizes.md

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className={`${s.box} rounded-lg bg-coral flex items-center justify-center`}>
        <svg width={s.icon} height={s.icon} viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4 12h4m4 0h4m4 0" />
          <circle cx="4" cy="12" r="1.5" />
          <circle cx="12" cy="12" r="1.5" />
          <circle cx="20" cy="12" r="1.5" />
          <path d="M8 8l4 4-4 4" />
          <path d="M16 8l-4 4 4 4" />
        </svg>
      </div>
      {showText && <span className={`${s.text} font-semibold text-ink`}>CodexBridge</span>}
    </div>
  )
}
