import { act, cleanup, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useAnnaWidget } from '@/hooks/use-anna-widget'
import type { Language } from '@/lib/translations'
import type { ElevenLabsConvaiElement } from '@/types/elevenlabs-convai'

const RETRY_MS = 400
const HINT_MS = 45_000

/** Element `<elevenlabs-convai>`: w przeglądarce ma shadowRoot dopiero po zarejestrowaniu skryptu widgetu. */
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

beforeEach(() => {
  vi.useFakeTimers()
  // Pobranie signed-url nie jest przedmiotem tego testu: zawieszamy je, żeby nie szumiało w konsoli.
  vi.stubGlobal('fetch', vi.fn(() => new Promise<never>(() => {})))
  vi.spyOn(console, 'warn').mockImplementation(() => {})
  vi.spyOn(console, 'error').mockImplementation(() => {})
})

afterEach(() => {
  cleanup()
  vi.useRealTimers()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('useAnnaWidget — otwieranie widgetu', () => {
  it('preferuje show() i nie ponawia, gdy shadowRoot istnieje', () => {
    const show = vi.fn()
    const open = vi.fn()
    const { result } = renderHook(() => useAnnaWidget('pl'))
    result.current.widgetRef.current = makeHost({ show, open, shadow: true })

    openWidgetEvent()
    vi.advanceTimersByTime(RETRY_MS * 3)

    expect(show).toHaveBeenCalledTimes(1)
    expect(open).not.toHaveBeenCalled()
  })

  it('używa open() jako fallbacku, gdy brak show()', () => {
    const open = vi.fn()
    const { result } = renderHook(() => useAnnaWidget('pl'))
    result.current.widgetRef.current = makeHost({ open, shadow: true })

    openWidgetEvent()

    expect(open).toHaveBeenCalledTimes(1)
  })

  it('klika przycisk w shadowRoot, gdy nie ma ani show(), ani open()', () => {
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

  it('gdy shadowRoot jest pusty w chwili otwarcia, ponawia próbę po 400 ms', () => {
    const show = vi.fn()
    const { result } = renderHook(() => useAnnaWidget('pl'))
    // Element jeszcze niezarejestrowany: brak shadowRoot.
    result.current.widgetRef.current = makeHost({ show })

    openWidgetEvent()
    expect(show).toHaveBeenCalledTimes(1)

    vi.advanceTimersByTime(RETRY_MS - 1)
    expect(show).toHaveBeenCalledTimes(1)

    vi.advanceTimersByTime(1)
    expect(show).toHaveBeenCalledTimes(2)
  })

  it('brak elementu widgetu: ostrzega w konsoli i nie rzuca', () => {
    renderHook(() => useAnnaWidget('pl'))

    expect(() => openWidgetEvent()).not.toThrow()
    expect(console.warn).toHaveBeenCalled()
  })

  it('wyjątek z show() jest logowany, nie propaguje się do wywołującego', () => {
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

  it('po odmontowaniu nasłuch eventu open-anna-widget jest usunięty', () => {
    const show = vi.fn()
    const { result, unmount } = renderHook(() => useAnnaWidget('pl'))
    result.current.widgetRef.current = makeHost({ show, shadow: true })

    unmount()
    openWidgetEvent()

    expect(show).not.toHaveBeenCalled()
  })
})

describe('useAnnaWidget — podpowiedź i atrybuty', () => {
  it('podpowiedź pojawia się po 45 s i znika po otwarciu widgetu', () => {
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

  it('ustawia agent-id i dynamic-variables z językiem wybranym przy zmianie języka', () => {
    const host = makeHost({ show: vi.fn(), shadow: true })
    const { result, rerender } = renderHook(({ lang }: { lang: Language }) => useAnnaWidget(lang), {
      initialProps: { lang: 'pl' as Language },
    })
    result.current.widgetRef.current = host

    rerender({ lang: 'en' })

    expect(host.getAttribute('agent-id')).toBeTruthy()
    const dyn = JSON.parse(host.getAttribute('dynamic-variables') ?? '{}')
    expect(dyn.user_language).toBe('en')
    expect(dyn.guest_language).toBe('English')
  })
})
