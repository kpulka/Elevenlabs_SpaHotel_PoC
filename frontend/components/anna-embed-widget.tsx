'use client'

import { Mic, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { useLanguage } from '@/context/language-context'

const AGENT_ID = 'agent_8401m0n03cggfgebhfh0cj96t7aj'
const WIDGET_SCRIPT = '/widget/convai-widget-embed.js'

export function AnnaEmbedWidget() {
  const { language, t } = useLanguage()
  const [signedUrl, setSignedUrl] = useState<string | null>(null)
  const [showHint, setShowHint] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const scriptInserted = useRef(false)
  const widgetRef = useRef<HTMLElement | null>(null)

  // 1. Fetch a signed URL from our API route, passing the active language.
  useEffect(() => {
    let cancelled = false
    fetch(`/api/anna/signed-url?lang=${language}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('HTTP ' + r.status))))
      .then((d) => {
        if (!cancelled && d?.signed_url) setSignedUrl(d.signed_url)
      })
      .catch((e) => {
        console.warn('Signed URL unavailable, falling back to agent-id:', e)
      })
    return () => {
      cancelled = true
    }
  }, [language])

  // 2. Load the ElevenLabs ConvAI widget script. It is self-hosted under /public/widget
  // because third-party CDN requests are often blocked by ad blockers or corporate networks.
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

  // 3. Make sure every ElevenLabs iframe is allowed to use the microphone.
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

  // 4. Set the widget attributes, including dynamic variables for the active language.
  useEffect(() => {
    const host = widgetRef.current
    if (!host) return
    host.setAttribute('agent-id', AGENT_ID)
    if (signedUrl) {
      host.setAttribute('signed-url', signedUrl)
    }

    // Pass the active language to the agent as dynamic variables.
    const dynVars = JSON.stringify({
      user_language: language,
      guest_language: language === 'en' ? 'English' : 'Polish',
      hotel_name: 'Bukowy Dwór',
      location: 'Krynica-Zdrój',
    })
    host.setAttribute('dynamic-variables', dynVars)
  }, [signedUrl, language])

  // 5. Show a hint bubble after 45 seconds on the page.
  useEffect(() => {
    const timer = setTimeout(() => setShowHint(true), 45000)
    return () => clearTimeout(timer)
  }, [])

  // 6. Open the conversation.
  function triggerConvai() {
    setShowHint(false)
    const host = widgetRef.current as any
    if (!host) {
      console.warn('Anna: widget element is not ready')
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
        console.error('Anna: failed to open the widget:', err)
      }
    }
    attempt()
    if (!host.shadowRoot) {
      setTimeout(attempt, 400)
    }
  }

  // 7. Listen for the global "open-anna-widget" event.
  useEffect(() => {
    window.addEventListener('open-anna-widget', triggerConvai)
    return () => window.removeEventListener('open-anna-widget', triggerConvai)
  }, [])

  return (
    <>
      {/* Floating hint bubble */}
      {showHint && (
        <div className="fixed right-4 bottom-24 z-[998] max-w-[280px] rounded-2xl border border-gold/30 bg-warm-white p-4 pr-9 shadow-2xl motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-2 sm:right-6">
          <button
            type="button"
            onClick={() => setShowHint(false)}
            aria-label={t.anna.closeHint}
            className="absolute top-2 right-2 flex size-7 items-center justify-center rounded-full text-muted-grey outline-none hover:bg-beige/60 focus-visible:outline-2 focus-visible:outline-gold"
          >
            <X className="size-4" aria-hidden="true" />
          </button>
          <p className="text-sm leading-relaxed text-charcoal">
            <strong>{t.anna.hintTitle}</strong> {t.anna.hintText}
          </p>
        </div>
      )}

      {/* Main floating call-to-action button */}
      <div className="fixed right-4 bottom-4 z-[999] sm:right-6 sm:bottom-6">
        <button
          id="anna-floating-trigger"
          type="button"
          onClick={triggerConvai}
          aria-label={t.anna.fabAria}
          className="group relative flex h-14 sm:h-16 items-center gap-2 sm:gap-3 rounded-full bg-gold px-5 sm:px-6 text-navy shadow-2xl outline-none select-none touch-manipulation transition-transform active:scale-95 hover:scale-105 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy"
        >
          <span
            className="absolute inset-0 -z-10 rounded-full bg-gold/60 motion-safe:animate-ping motion-safe:[animation-duration:2.4s]"
            aria-hidden="true"
          />
          <Mic className="size-6 sm:size-7 shrink-0 text-navy" aria-hidden="true" />
          <span className="text-sm sm:text-base font-semibold whitespace-nowrap">{t.anna.fabButton}</span>
        </button>
      </div>

      {/* Official ElevenLabs ConvAI web component */}
      <elevenlabs-convai
        ref={(el: any) => {
          widgetRef.current = el
        }}
        agent-id={AGENT_ID}
      />
    </>
  )
}
