'use client'

import { Mic, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

const AGENT_ID = 'agent_8401m0n03cggfgebhfh0cj96t7aj'
// Self-hosted widget skrypt (public/widget/) — niezależny od zewnętrznego CDN (unpkg.com),
// który bywał blokowany w przeglądarkach (403/adblock/VPN) → widget się nie ładował
// i przycisk "Porozmawiaj z Anną" nie otwierał rozmowy.
const WIDGET_SCRIPT = '/widget/convai-widget-embed.js'

export function AnnaEmbedWidget() {
  const [signedUrl, setSignedUrl] = useState<string | null>(null)
  const [showHint, setShowHint] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const scriptInserted = useRef(false)
  const widgetRef = useRef<HTMLElement | null>(null)

  // 1. Pobierz Signed URL z serwera (opcjonalny, podwyższone bezpieczeństwo)
  useEffect(() => {
    let cancelled = false
    fetch('/api/anna/signed-url')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('HTTP ' + r.status))))
      .then((d) => {
        if (!cancelled && d?.signed_url) setSignedUrl(d.signed_url)
      })
      .catch((e) => {
        // Fallback na agent-id jeśli signed-url nie jest dostępny
        console.warn('Signed-url unavailable, fallback to agent-id:', e)
      })
    return () => {
      cancelled = true
    }
  }, [])

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

  // 4. Ustaw atrybuty na custom elemencie
  useEffect(() => {
    const host = widgetRef.current
    if (!host) return
    host.setAttribute('agent-id', AGENT_ID)
    if (signedUrl) {
      host.setAttribute('signed-url', signedUrl)
    }
  }, [signedUrl])

  // 5. Podpowiedź (hint) po 45s na stronie
  useEffect(() => {
    const timer = setTimeout(() => setShowHint(true), 45000)
    return () => clearTimeout(timer)
  }, [])

  // 6. Funkcja uruchamiania rozmowy
  function triggerConvai() {
    setShowHint(false)
    const host = widgetRef.current as any
    if (!host) {
      console.warn('Anna: element widgetu nie gotowy')
      return
    }
    // Spróbuj natywnego API widgetu; shadow-root button klik jako fallback.
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
    // Custom element może się jeszcze nie stworzić: odczekaj krótko i spróbuj ponownie,
    // jeśli shadowRoot (natywny UI widgetu) jeszcze nie jest gotowy.
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

  return (
    <>
      {/* Pływający pasek podpowiedzi */}
      {showHint && (
        <div className="fixed right-4 bottom-24 z-[998] max-w-[280px] rounded-2xl border border-gold/30 bg-warm-white p-4 pr-9 shadow-2xl motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-2 sm:right-6">
          <button
            type="button"
            onClick={() => setShowHint(false)}
            aria-label="Zamknij podpowiedź"
            className="absolute top-2 right-2 flex size-7 items-center justify-center rounded-full text-muted-grey outline-none hover:bg-beige/60 focus-visible:outline-2 focus-visible:outline-gold"
          >
            <X className="size-4" aria-hidden="true" />
          </button>
          <p className="text-sm leading-relaxed text-charcoal">
            <strong>Potrzebuje Pani/Pan pomocy?</strong> Wystarczy kliknąć przycisk poniżej — Anna pomoże zarezerwować zabieg lub pokój.
          </p>
        </div>
      )}

      {/* Główny, markowy przycisk pływający na dole ekranu */}
      <div className="fixed right-4 bottom-4 z-[999] sm:right-6 sm:bottom-6">
        <button
          id="anna-floating-trigger"
          type="button"
          onClick={triggerConvai}
          aria-label="Porozmawiaj z Anną, wirtualną recepcjonistką Bukowego Dworu"
          className="group relative flex h-14 sm:h-16 items-center gap-2 sm:gap-3 rounded-full bg-gold px-5 sm:px-6 text-navy shadow-2xl outline-none select-none touch-manipulation transition-transform active:scale-95 hover:scale-105 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy"
        >
          <span
            className="absolute inset-0 -z-10 rounded-full bg-gold/60 motion-safe:animate-ping motion-safe:[animation-duration:2.4s]"
            aria-hidden="true"
          />
          <Mic className="size-6 sm:size-7 shrink-0 text-navy" aria-hidden="true" />
          <span className="text-sm sm:text-base font-semibold whitespace-nowrap">Porozmawiaj z Anną</span>
        </button>
      </div>

      {/* Oficjalny komponent ElevenLabs ConvAI */}
      <elevenlabs-convai
        ref={(el: any) => {
          widgetRef.current = el
        }}
        agent-id={AGENT_ID}
      />
    </>
  )
}
