'use client'

import { Globe } from 'lucide-react'
import { useLanguage } from '@/context/language-context'
import { isPl } from '@/lib/translations'

export function LanguageSwitcher({ className = '' }: { className?: string }) {
  const { language, setLanguage } = useLanguage()

  return (
    <div className={`flex items-center gap-1 rounded-full border border-gold/40 bg-navy-light/80 p-1 backdrop-blur-sm ${className}`}>
      <button
        type="button"
        onClick={() => setLanguage('pl')}
        aria-label="Przełącz na język polski"
        aria-pressed={isPl(language)}
        className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold tracking-wider transition-all ${
          isPl(language)
            ? 'bg-gold text-navy shadow-sm'
            : 'text-white/80 hover:text-gold hover:bg-white/5'
        }`}
      >
        <span>PL</span>
      </button>

      <button
        type="button"
        onClick={() => setLanguage('en')}
        aria-label="Switch to English language"
        aria-pressed={language === 'en'}
        className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold tracking-wider transition-all ${
          language === 'en'
            ? 'bg-gold text-navy shadow-sm'
            : 'text-white/80 hover:text-gold hover:bg-white/5'
        }`}
      >
        <span>EN</span>
      </button>
    </div>
  )
}
