'use client'

import { useEffect, useRef, useState } from 'react'

import type { Language } from '@/lib/translations'
import type { ElevenLabsConvaiElement } from '@/types/elevenlabs-convai'

// Nadpisywalne przez env; literał zostaje jako udokumentowany fallback dla dev/demo.
export const AGENT_ID = process.env.NEXT_PUBLIC_ELEVENLABS_AGENT_ID ?? 'agent_8401m0n03cggfgebhfh0cj96t7aj'
const WIDGET_SCRIPT = '/widget/convai-widget-embed.js'

export function useAnnaWidget(language: Language) {
  const [signedUrl, setSignedUrl] = useState<string | null>(null)
  const [showHint, setShowHint] = useState(false)
  const scriptInserted = useRef(false)
  const widgetRef = useRef<ElevenLabsConvaiElement | null>(null)

  // 1. Pobierz Signed URL z serwera z parametrem wybranego języka
  useEffect(() => {
    let cancelled = false
    fetch(`/api/anna/signed-url?lang=${language}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('HTTP ' + r.status))))
      .then((d) => {
        if (!cancelled && d?.signed_url) setSignedUrl(d.signed_url)
      })
      .catch((e) => {
        console.warn('Signed-url unavailable, fallback to agent-id:', e)
      })
    return () => {
      cancelled = true
    }
  }, [language])

  // 2. Wstrzyknij oficjalny skrypt widgetu ElevenLabs
  useEffect(() => {
    if (scriptInserted.current) return
    scriptInserted.current = true
    const el = document.createElement('script')
    el.src = WIDGET_SCRIPT
    el.type = 'text/javascript'
    el.defer = true
    el.async = true
    document.head.appendChild(el)
  }, [])

  // 3. Sprawdź uprawnienia microphone dla każdego iframe ElevenLabs
  useEffect(() => {
    const observer = new MutationObserver(() => {
      const frames = document.querySelectorAll<HTMLIFrameElement>(
        'iframe[src*="elevenlabs"], iframe[src*="elevenlabs.io"]',
      )
      frames.forEach((frame) => {
        const allow = frame.getAttribute('allow') || ''
        if (!allow.includes('microphone')) {
          frame.setAttribute('allow', allow ? `${allow}; microphone` : 'microphone')
        }
      })
    })
    observer.observe(document.body, { childList: true, subtree: true })
    return () => observer.disconnect()
  }, [])

  // 4. Ustaw atrybuty na custom elemencie wraz z dynamic_variables języka
  useEffect(() => {
    const host = widgetRef.current
    if (!host) return
    host.setAttribute('agent-id', AGENT_ID)
    if (signedUrl) {
      host.setAttribute('signed-url', signedUrl)
    }

    // Wstrzyknij zmienną dynamiczną wybranego języka (user_language)
    const dynVars = JSON.stringify({
      user_language: language,
      guest_language: language === 'en' ? 'English' : 'Polish',
      hotel_name: 'Bukowy Dwór',
      location: 'Krynica-Zdrój',
    })
    host.setAttribute('dynamic-variables', dynVars)
  }, [signedUrl, language])

  // 5. Podpowiedź (hint) po 45s na stronie
  useEffect(() => {
    const timer = setTimeout(() => setShowHint(true), 45000)
    return () => clearTimeout(timer)
  }, [])

  // 6. Funkcja uruchamiania rozmowy
  function triggerConvai() {
    setShowHint(false)
    const host = widgetRef.current
    if (!host) {
      console.warn('Anna: element widgetu nie gotowy')
      return
    }
    const attempt = () => {
      try {
        if (typeof host.show === 'function') { host.show(); return }
        if (typeof host.open === 'function') { host.open(); return }
        const sr = host.shadowRoot
        if (sr) {
          const btn = sr.querySelector('button')
          if (btn) { btn.click(); return }
        }
        host.click?.()
      } catch (err) {
        console.error('Błąd otwierania widgetu Anny:', err)
      }
    }
    attempt()
    if (!host.shadowRoot) {
      setTimeout(attempt, 400)
    }
  }

  // 7. Nasłuchuj globalnego eventu 'open-anna-widget'
  useEffect(() => {
    window.addEventListener('open-anna-widget', triggerConvai)
    return () => window.removeEventListener('open-anna-widget', triggerConvai)
  }, [])

  return {
    showHint,
    setShowHint,
    widgetRef,
    triggerConvai,
  }
}
