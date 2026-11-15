import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { AnnaEmbedWidget } from '@/components/anna-embed-widget'
import { resetAnnaWidgetStateForTests } from '@/hooks/use-anna-widget'

const TEST_AGENT_ID = 'agent_testagent0001'

beforeEach(() => {
  vi.stubEnv('NEXT_PUBLIC_ELEVENLABS_AGENT_ID', TEST_AGENT_ID)
  vi.stubGlobal('fetch', vi.fn(() => new Promise<never>(() => {})))
  vi.spyOn(console, 'warn').mockImplementation(() => {})
  vi.spyOn(console, 'error').mockImplementation(() => {})
  resetAnnaWidgetStateForTests()
})

afterEach(() => {
  cleanup()
  resetAnnaWidgetStateForTests()
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('AnnaEmbedWidget', () => {
  it('sets the agent id once on the ElevenLabs element', () => {
    const { container } = render(<AnnaEmbedWidget />)

    const host = container.querySelector('elevenlabs-convai')
    expect(host?.getAttribute('agent-id')).toBe(TEST_AGENT_ID)
  })

  it('shows the consent notice with a link to the privacy page, linked to the trigger', () => {
    render(<AnnaEmbedWidget />)

    const trigger = screen.getByRole('button', { name: /porozmawiaj z ann/i })
    const notice = document.getElementById('anna-consent-notice')
    expect(notice?.textContent).toMatch(/ElevenLabs/)
    expect(notice?.querySelector('a')?.getAttribute('href')).toBe('/polityka')
    expect(trigger.getAttribute('aria-describedby')).toBe('anna-consent-notice')
  })

  it('does not request the signed URL on mount, but does on hover', () => {
    const fetchMock = vi.mocked(fetch)
    render(<AnnaEmbedWidget />)
    expect(fetchMock).not.toHaveBeenCalled()

    fireEvent.pointerEnter(screen.getByRole('button', { name: /porozmawiaj z ann/i }))

    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('hides the consent notice after the visitor clicks to start the conversation', () => {
    render(<AnnaEmbedWidget />)

    fireEvent.click(screen.getByRole('button', { name: /porozmawiaj z ann/i }))

    expect(document.getElementById('anna-consent-notice')).toBeNull()
  })

  it('renders the hint inside a polite live region', () => {
    vi.useFakeTimers()
    try {
      render(<AnnaEmbedWidget />)
      expect(screen.getByRole('status').getAttribute('aria-live')).toBe('polite')
      act(() => {
        vi.advanceTimersByTime(45_000)
      })
      expect(screen.getByRole('status').textContent).toMatch(/Anna/)
    } finally {
      vi.useRealTimers()
    }
  })

  it('does not fetch again when the trigger is clicked after hovering', async () => {
    const fetchMock = vi.mocked(fetch)
    render(<AnnaEmbedWidget />)
    const trigger = screen.getByRole('button', { name: /porozmawiaj z ann/i })

    fireEvent.pointerEnter(trigger)
    fireEvent.click(trigger)

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
  })
})
