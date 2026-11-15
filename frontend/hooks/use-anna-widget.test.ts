import { act, cleanup, renderHook, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { resetAnnaWidgetStateForTests, useAnnaWidget } from '@/hooks/use-anna-widget'
import type { Language } from '@/lib/translations'
import type { ElevenLabsConvaiElement } from '@/types/elevenlabs-convai'

const RETRY_MS = 400
const HINT_MS = 45_000
const WIDGET_SRC = '/widget/convai-widget-embed.js'
const TEST_AGENT_ID = 'agent_testagent0001'

/** `<elevenlabs-convai>` element: in the browser it only gets a shadowRoot once the widget script has registered. */
function makeHost(options: { show?: () => void; open?: () => void; shadow?: boolean } = {}) {
  const host = document.createElement('div') as unknown as ElevenLabsConvaiElement
  if (options.show) host.show = options.show
  if (options.open) host.open = options.open
  if (options.shadow) host.attachShadow({ mode: 'open' })
  return host
}

function openWidgetEvent() {
  act(() => {
    window.dispatchEvent(new Event('open-anna-widget'))
  })
}

function signedUrlResponse() {
  return Response.json({ signed_url: 'wss://example.test/signed' })
}

beforeEach(() => {
  vi.stubEnv('NEXT_PUBLIC_ELEVENLABS_AGENT_ID', TEST_AGENT_ID)
  vi.useFakeTimers()
  // The signed-url fetch is not under test here: keep it pending so it does not add console noise.
  vi.stubGlobal('fetch', vi.fn(() => new Promise<never>(() => {})))
  vi.spyOn(console, 'warn').mockImplementation(() => {})
  vi.spyOn(console, 'error').mockImplementation(() => {})
  resetAnnaWidgetStateForTests()
})

afterEach(() => {
  cleanup()
  resetAnnaWidgetStateForTests()
  vi.useRealTimers()
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('useAnnaWidget: opening the widget', () => {
  it('prefers show() and does not retry when shadowRoot exists', () => {
    const show = vi.fn()
    const open = vi.fn()
    const { result } = renderHook(() => useAnnaWidget('pl'))
    result.current.widgetRef.current = makeHost({ show, open, shadow: true })

    openWidgetEvent()
    vi.advanceTimersByTime(RETRY_MS * 3)

    expect(show).toHaveBeenCalledTimes(1)
    expect(open).not.toHaveBeenCalled()
  })

  it('falls back to open() when show() is missing', () => {
    const open = vi.fn()
    const { result } = renderHook(() => useAnnaWidget('pl'))
    result.current.widgetRef.current = makeHost({ open, shadow: true })

    openWidgetEvent()

    expect(open).toHaveBeenCalledTimes(1)
  })

  it('clicks the button inside shadowRoot when neither show() nor open() exists', () => {
    const click = vi.fn()
    const host = makeHost({ shadow: true })
    const button = document.createElement('button')
    button.addEventListener('click', click)
    host.shadowRoot!.appendChild(button)
    const { result } = renderHook(() => useAnnaWidget('pl'))
    result.current.widgetRef.current = host

    openWidgetEvent()

    expect(click).toHaveBeenCalledTimes(1)
  })

  it('retries after 400 ms when there is no shadowRoot at open time', () => {
    const show = vi.fn()
    const { result } = renderHook(() => useAnnaWidget('pl'))
    // Element already has show() but is not attached yet: no shadowRoot.
    result.current.widgetRef.current = makeHost({ show })

    openWidgetEvent()
    expect(show).toHaveBeenCalledTimes(1)

    vi.advanceTimersByTime(RETRY_MS - 1)
    expect(show).toHaveBeenCalledTimes(1)

    vi.advanceTimersByTime(1)
    expect(show).toHaveBeenCalledTimes(2)
  })

  it('warns in the console and does not throw when the widget element is missing', () => {
    renderHook(() => useAnnaWidget('pl'))

    expect(() => openWidgetEvent()).not.toThrow()
    expect(console.warn).toHaveBeenCalled()
  })

  it('logs an exception from show() instead of propagating it to the caller', () => {
    const { result } = renderHook(() => useAnnaWidget('pl'))
    result.current.widgetRef.current = makeHost({
      show: () => {
        throw new Error('boom')
      },
      shadow: true,
    })

    expect(() => openWidgetEvent()).not.toThrow()
    expect(console.error).toHaveBeenCalled()
  })

  it('removes the open-anna-widget listener on unmount', () => {
    const show = vi.fn()
    const { result, unmount } = renderHook(() => useAnnaWidget('pl'))
    result.current.widgetRef.current = makeHost({ show, shadow: true })

    unmount()
    openWidgetEvent()

    expect(show).not.toHaveBeenCalled()
  })
})

describe('useAnnaWidget: hint and dynamic variables', () => {
  it('shows the hint after 45 s and hides it once the widget is opened', () => {
    const { result } = renderHook(() => useAnnaWidget('pl'))
    result.current.widgetRef.current = makeHost({ show: vi.fn(), shadow: true })

    expect(result.current.showHint).toBe(false)
    act(() => {
      vi.advanceTimersByTime(HINT_MS)
    })
    expect(result.current.showHint).toBe(true)

    act(() => {
      result.current.triggerConvai()
    })
    expect(result.current.showHint).toBe(false)
  })

  it('sets dynamic-variables with the selected language, hotel name and location', () => {
    const host = makeHost({ show: vi.fn(), shadow: true })
    const { result, rerender } = renderHook(({ lang }: { lang: Language }) => useAnnaWidget(lang), {
      initialProps: { lang: 'pl' as Language },
    })
    result.current.widgetRef.current = host

    rerender({ lang: 'en' })

    const dyn = JSON.parse(host.getAttribute('dynamic-variables') ?? '{}')
    expect(dyn.user_language).toBe('en')
    expect(dyn.guest_language).toBe('English')
    expect(dyn.hotel_name).toBe('Bukowy Dwór')
    expect(dyn.location).toBe('Krynica-Zdrój')
  })

  it('logs an error when NEXT_PUBLIC_ELEVENLABS_AGENT_ID is missing', () => {
    vi.stubEnv('NEXT_PUBLIC_ELEVENLABS_AGENT_ID', '')

    renderHook(() => useAnnaWidget('pl'))

    expect(console.error).toHaveBeenCalledWith(expect.stringContaining('anna.agent_id_missing'))
  })
})

describe('useAnnaWidget: lazy loading', () => {
  // Lazy tests wait on real promises (fetch and script load), so they run without fake timers.
  beforeEach(() => {
    vi.useRealTimers()
  })

  it('does not fetch the signed URL or load the widget script on mount', () => {
    const fetchMock = vi.fn(() => new Promise<never>(() => {}))
    vi.stubGlobal('fetch', fetchMock)

    renderHook(() => useAnnaWidget('pl'))

    expect(fetchMock).not.toHaveBeenCalled()
    expect(document.querySelector(`script[src="${WIDGET_SRC}"]`)).toBeNull()
  })

  it('starts the signed-url request and the script on prepare(), once', async () => {
    const fetchMock = vi.fn(async () => signedUrlResponse())
    vi.stubGlobal('fetch', fetchMock)
    const { result } = renderHook(() => useAnnaWidget('pl'))

    act(() => {
      result.current.prepare()
      result.current.prepare()
    })

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
    expect(String((fetchMock.mock.calls as unknown as unknown[][])[0][0])).toBe('/api/anna/signed-url?lang=pl')
    expect(document.querySelectorAll(`script[src="${WIDGET_SRC}"]`)).toHaveLength(1)
  })

  it('reuses the cached signed URL for the same language in later mounts', async () => {
    const fetchMock = vi.fn(async () => signedUrlResponse())
    vi.stubGlobal('fetch', fetchMock)
    const first = renderHook(() => useAnnaWidget('pl'))
    act(() => first.result.current.prepare())
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
    first.unmount()

    const second = renderHook(() => useAnnaWidget('pl'))
    act(() => second.result.current.prepare())
    await act(async () => {
      await Promise.resolve()
    })

    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('requests a new signed URL when the language changes after the widget was started', async () => {
    const fetchMock = vi.fn(async () => signedUrlResponse())
    vi.stubGlobal('fetch', fetchMock)
    const { result, rerender } = renderHook(({ lang }: { lang: Language }) => useAnnaWidget(lang), {
      initialProps: { lang: 'pl' as Language },
    })
    act(() => result.current.prepare())
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))

    rerender({ lang: 'en' })

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2))
    expect(String((fetchMock.mock.calls as unknown as unknown[][])[1][0])).toBe('/api/anna/signed-url?lang=en')
  })

  it('opens the widget after the script loads when the visitor clicked before it was ready', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => signedUrlResponse()))
    const show = vi.fn()
    const { result } = renderHook(() => useAnnaWidget('pl'))
    const host = makeHost()
    result.current.widgetRef.current = host

    act(() => result.current.triggerConvai())
    expect(show).not.toHaveBeenCalled()

    // The widget script registers the element: simulate it, then the script's load event.
    host.show = show
    const script = document.querySelector<HTMLScriptElement>(`script[src="${WIDGET_SRC}"]`)
    expect(script).not.toBeNull()
    act(() => {
      script!.dispatchEvent(new Event('load'))
    })

    await waitFor(() => expect(show).toHaveBeenCalledTimes(1))
  })

  it('hides the consent notice once the visitor starts a conversation', () => {
    const { result } = renderHook(() => useAnnaWidget('pl'))
    expect(result.current.consentVisible).toBe(true)

    act(() => result.current.triggerConvai())

    expect(result.current.consentVisible).toBe(false)
  })
})
