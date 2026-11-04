'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { Language, translations } from '@/lib/translations'

type LanguageContextType = {
  language: Language
  setLanguage: (lang: Language) => void
  t: typeof translations['pl']
}

export const DEFAULT_LANGUAGE: Language = 'en'
const STORAGE_KEY = 'bukowy_dwor_lang'

const LanguageContext = createContext<LanguageContextType>({
  language: DEFAULT_LANGUAGE,
  setLanguage: () => {},
  t: translations[DEFAULT_LANGUAGE],
})

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>(DEFAULT_LANGUAGE)

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved === 'pl' || saved === 'en') {
        setLanguageState(saved)
        document.documentElement.lang = saved
      }
    } catch {
      // Storage can be unavailable (private mode, blocked site data); fall back to the default
      // language.
    }
  }, [])

  const setLanguage = (lang: Language) => {
    setLanguageState(lang)
    document.documentElement.lang = lang
    try {
      localStorage.setItem(STORAGE_KEY, lang)
    } catch {}

    // Notify non-React consumers (e.g. the embedded ElevenLabs widget)
    window.dispatchEvent(
      new CustomEvent('language-changed', {
        detail: { language: lang },
      })
    )
  }

  const value = {
    language,
    setLanguage,
    t: translations[language],
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
