'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { Language, translations } from '@/lib/translations'

type LanguageContextType = {
  language: Language
  setLanguage: (lang: Language) => void
  t: typeof translations['pl']
}

const LanguageContext = createContext<LanguageContextType>({
  language: 'pl',
  setLanguage: () => {},
  t: translations.pl,
})

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>('pl')

  useEffect(() => {
    try {
      const saved = localStorage.getItem('bukowy_dwor_lang') as Language | null
      if (saved && (saved === 'pl' || saved === 'en')) {
        setLanguageState(saved)
        document.documentElement.lang = saved
      }
    } catch {
      // ignore localStorage errors in private mode
    }
  }, [])

  const setLanguage = (lang: Language) => {
    setLanguageState(lang)
    document.documentElement.lang = lang
    try {
      localStorage.setItem('bukowy_dwor_lang', lang)
    } catch {}

    // Dispatch global event for non-React or embedded widgets
    window.dispatchEvent(
      new CustomEvent('language-changed', {
        detail: { language: lang },
      })
    )
  }

  const value = {
    language,
    setLanguage,
    t: translations[language] || translations.pl,
  }

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider')
  }
  return context
}
