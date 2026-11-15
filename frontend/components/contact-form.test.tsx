import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ContactForm } from '@/components/contact-form'

function fillValidForm() {
  fireEvent.change(screen.getByLabelText(/imi[eę]|name/i), { target: { value: 'Anna Test' } })
  fireEvent.change(screen.getByLabelText(/e-?mail/i), { target: { value: 'anna@example.test' } })
  fireEvent.change(screen.getByLabelText(/wiadomo|message/i), { target: { value: 'Hello' } })
}

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(async () => Response.json({ ok: true, delivered: false })))
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('ContactForm accessibility', () => {
  it('announces validation errors with role="alert" and focuses the first invalid field', () => {
    render(<ContactForm />)

    fireEvent.click(screen.getByRole('button', { name: /wy[sś]lij|send/i }))

    const alerts = screen.getAllByRole('alert')
    expect(alerts.length).toBeGreaterThanOrEqual(2)
    expect(document.activeElement).toBe(document.getElementById('name'))
    expect(screen.getByLabelText(/imi[eę]|name/i).getAttribute('aria-invalid')).toBe('true')
    expect(fetch).not.toHaveBeenCalled()
  })

  it('moves focus to the success message after a valid submit', async () => {
    render(<ContactForm />)

    fillValidForm()
    fireEvent.click(screen.getByRole('button', { name: /wy[sś]lij|send/i }))

    const status = await screen.findByRole('status')
    await waitFor(() => expect(document.activeElement).toBe(status))
    expect(status.getAttribute('tabindex')).toBe('-1')
  })
})

describe('ContactForm submission', () => {
  it('posts the message to /api/contact with the honeypot value', async () => {
    render(<ContactForm />)

    fillValidForm()
    fireEvent.click(screen.getByRole('button', { name: /wy[sś]lij|send/i }))

    await screen.findByRole('status')
    const call = vi.mocked(fetch).mock.calls[0]
    expect(call[0]).toBe('/api/contact')
    const body = JSON.parse(String((call[1] as RequestInit).body))
    expect(body).toMatchObject({ name: 'Anna Test', email: 'anna@example.test', message: 'Hello', website: '' })
  })

  it('keeps the demo notice on the success state', async () => {
    render(<ContactForm />)

    fillValidForm()
    fireEvent.click(screen.getByRole('button', { name: /wy[sś]lij|send/i }))

    const status = await screen.findByRole('status')
    expect(status.textContent).toMatch(/demo|demonstracyjna/i)
  })

  it('shows an error and keeps the form when the server rejects the message', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('{}', { status: 500 })))
    render(<ContactForm />)

    fillValidForm()
    fireEvent.click(screen.getByRole('button', { name: /wy[sś]lij|send/i }))

    const alert = await screen.findByText(/nie uda[łl]o|could not be sent/i)
    expect(alert.getAttribute('role')).toBe('alert')
    expect(screen.getByLabelText(/imi[eę]|name/i)).toBeTruthy()
  })

  it('shows the rate-limit message on 429', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('{}', { status: 429 })))
    render(<ContactForm />)

    fillValidForm()
    fireEvent.click(screen.getByRole('button', { name: /wy[sś]lij|send/i }))

    expect(await screen.findByText(/zbyt wiele pr[oó]b|too many attempts/i)).toBeTruthy()
  })
})
