'use client'

import { useEffect, useRef, useState } from 'react'

import { getPublicAgentId } from '@/lib/env'
import { errorFields, logger } from '@/lib/logger'
import { contactInfo } from '@/lib/hotel/contact'
import { SITE_NAME } from '@/lib/site'
import type { Language } from '@/lib/translations'
import type { ElevenLabsConvaiElement } from '@/types/elevenlabs-convai'

const WIDGET_SCRIPT = '/widget/convai-widget-embed.js'

/**
 * How long a signed URL is reused in this browser tab. Conservative: the signed URL's own expiry is
 * not documented in this repo, so a fresh one is requested after this interval.
 */
export const SIGNED_URL_TTL_MS = 10 * 60_000

type CachedSignedUrl = { url: string; expiresAt: number }

// Module-level so that the cache survives re-mounts of the widget (page navigation) for the session.
const signedUrlCache = new Map<Language, CachedSignedUrl>()
const signedUrlInflight = new Map<Language, Promise<string | null>>()
let scriptPromise: Promise<void> | null = null

/**
 * Returns a signed URL for the language, from cache when still fresh. Resolves to `null` when the
 * server cannot provide one (the widget then starts from the agent id alone, depending on the plan).
 */
export function loadSignedUrl(language: Language): Promise<string | null> {
  const cached = signedUrlCache.get(language)
  if (cached && cached.expiresAt > Date.now()) return Promise.resolve(cached.url)

  const inflight = signedUrlInflight.get(language)
  if (inflight) return inflight

  const request = fetch(`/api/anna/signed-url?lang=${language}`)
    .then((res) => (res.ok ? res.json() : Promise.reject(new Error('HTTP ' + res.status))))
    .then((data: unknown) => {
      const url =
        typeof data === 'object' && data !== null && 'signed_url' in data && typeof data.signed_url === 'string'
          ? data.signed_url
          : null
      if (!url) throw new Error('signed_url missing from response')
      signedUrlCache.set(language, { url, expiresAt: Date.now() + SIGNED_URL_TTL_MS })
      return url
    })
    .catch((err: unknown) => {
      logger.warn('anna.signed_url_unavailable', errorFields(err))
      return null
    })
    .finally(() => {
      signedUrlInflight.delete(language)
    })

  signedUrlInflight.set(language, request)
  return request
}

/** Injects the official ElevenLabs widget script once per page load. Resolves when it has loaded. */
export function loadWidgetScript(): Promise<void> {
  if (scriptPromise) return scriptPromise
  scriptPromise = new Promise<void>((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>(`script[src="${WIDGET_SCRIPT}"]`)
    const el = existing ?? document.createElement('script')
    const done = () => {
      el.removeEventListener('load', done)
      el.removeEventListener('error', fail)
      resolve()
    }
    const fail = () => {
      el.removeEventListener('load', done)
      el.removeEventListener('error', fail)
      scriptPromise = null // a later interaction may retry
      reject(new Error('widget script failed to load'))
    }
    el.addEventListener('load', done)
    el.addEventListener('error', fail)
    if (!existing) {
      el.src = WIDGET_SCRIPT
      el.type = 'text/javascript'
      el.defer = true
      el.async = true
      document.head.appendChild(el)
    }
  })
  return scriptPromise
}

/** The element is usable once the widget script has registered it (show/open API or a shadow root). */
function isWidgetReady(host: ElevenLabsConvaiElement): boolean {
  return typeof host.show === 'function' || typeof host.open === 'function' || host.shadowRoot !== null
}

/** Opens the widget. Retries once after 400 ms when the element has no shadow root yet. */
function openWidget(host: ElevenLabsConvaiElement) {
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
      logger.error('anna.open_failed', errorFields(err))
    }
  }
  attempt()
  if (!host.shadowRoot) {
    setTimeout(attempt, 400)
  }
}

/**
 * Controls the ElevenLabs widget. Nothing is fetched or loaded on page load: the first interaction
 * (`prepare` on hover or focus, or opening the widget) starts the signed-url request and the widget
 * script. Signed URLs are cached per language for the session.
 */
export function useAnnaWidget(language: Language) {
  const [started, setStarted] = useState(false)
  const [opened, setOpened] = useState(false)
  const [scriptReady, setScriptReady] = useState(false)
  const [showHint, setShowHint] = useState(false)
  // Signed URL per language: undefined = still loading, null = unavailable, string = ready.
  const [signedUrls, setSignedUrls] = useState<Partial<Record<Language, string | null>>>({})
  const widgetRef = useRef<ElevenLabsConvaiElement | null>(null)
  const openRequested = useRef(false)

  const signedUrl = signedUrls[language] ?? null
  const signedUrlSettled = signedUrls[language] !== undefined

  // 0. The agent id itself is rendered as the element's `agent-id` attribute; here we only report a missing value.
  useEffect(() => {
    if (!getPublicAgentId()) {
      logger.error('anna.agent_id_missing', { variable: 'NEXT_PUBLIC_ELEVENLABS_AGENT_ID' })
    }
  }, [])

  // 1. Signed URL for the selected language, requested once the widget has been started.
  useEffect(() => {
    if (!started) return
    let active = true
    loadSignedUrl(language).then((url) => {
      if (active) setSignedUrls((prev) => ({ ...prev, [language]: url }))
    })
    return () => {
      active = false
    }
  }, [started, language])

  // 2. Official widget script, loaded on the first interaction only.
  useEffect(() => {
    if (!started) return
    loadWidgetScript().then(
      () => setScriptReady(true),
      (err: unknown) => logger.error('anna.widget_script_failed', errorFields(err)),
    )
  }, [started])

  // 3. Make sure every ElevenLabs iframe is allowed to use the microphone (only once the widget runs).
  useEffect(() => {
    if (!started) return
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
  }, [started])

  // 4. Signed URL and dynamic variables (language, hotel name and location) on the element.
  useEffect(() => {
    const host = widgetRef.current
    if (!host) return
    if (signedUrl) {
      host.setAttribute('signed-url', signedUrl)
    }
    const dynVars = JSON.stringify({
      user_language: language,
      guest_language: language === 'en' ? 'English' : 'Polish',
      hotel_name: SITE_NAME,
      location: contactInfo.city,
    })
    host.setAttribute('dynamic-variables', dynVars)
  }, [signedUrl, language])

  // 5. Show the hint after 45 s on the page
  useEffect(() => {
    const timer = setTimeout(() => setShowHint(true), 45000)
    return () => clearTimeout(timer)
  }, [])

  // 6. Open the widget once the script has loaded and the signed URL has settled, if the visitor
  //    asked for it before the widget was ready.
  useEffect(() => {
    if (!scriptReady || !signedUrlSettled || !openRequested.current) return
    openRequested.current = false
    const host = widgetRef.current
    if (host) openWidget(host)
  }, [scriptReady, signedUrlSettled])

  /** Starts loading without opening anything (hover or focus on the trigger). */
  function prepare() {
    setStarted(true)
  }

  // 7. Start the conversation (visitor click, or the global 'open-anna-widget' event).
  function triggerConvai() {
    setShowHint(false)
    setOpened(true)
    setStarted(true)
    const host = widgetRef.current
    if (!host) {
      logger.warn('anna.widget_not_ready')
      return
    }
    if (isWidgetReady(host)) {
      openWidget(host)
      return
    }
    // Script not registered yet: the effect above opens the widget once it is.
    openRequested.current = true
  }

  // 8. Listen for the global 'open-anna-widget' event
  useEffect(() => {
    window.addEventListener('open-anna-widget', triggerConvai)
    return () => window.removeEventListener('open-anna-widget', triggerConvai)
  }, [])

  return {
    showHint,
    setShowHint,
    widgetRef,
    triggerConvai,
    prepare,
    /** False once the visitor has started a conversation; the consent notice is hidden then. */
    consentVisible: !opened,
  }
}

/** Test helper: forget cached signed URLs and the script promise. Not used by the app. */
export function resetAnnaWidgetStateForTests() {
  signedUrlCache.clear()
  signedUrlInflight.clear()
  scriptPromise = null
  document.querySelector(`script[src="${WIDGET_SCRIPT}"]`)?.remove()
}
