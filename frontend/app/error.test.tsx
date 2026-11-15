import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AppError from '@/app/error'
import NotFound from '@/app/not-found'

const SECRET_DETAIL = 'customer-token-abc123'

beforeEach(() => {
  vi.spyOn(console, 'error').mockImplementation(() => {})
  vi.spyOn(console, 'info').mockImplementation(() => {})
})

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('app/error.tsx', () => {
  it('renders the error message and calls retry when the button is pressed', () => {
    const retry = vi.fn()
    render(<AppError error={new Error(SECRET_DETAIL)} retry={retry} />)

    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Coś poszło nie tak')
    fireEvent.click(screen.getByRole('button', { name: 'Spróbuj ponownie' }))

    expect(retry).toHaveBeenCalledTimes(1)
  })

  it('logs the digest and error name, never the error message', () => {
    const error = Object.assign(new TypeError(SECRET_DETAIL), { digest: 'd-123' })
    render(<AppError error={error} retry={vi.fn()} />)

    expect(console.error).toHaveBeenCalledWith(expect.stringContaining('"event":"app.error_boundary"'))
    expect(console.error).toHaveBeenCalledWith(expect.stringContaining('"digest":"d-123"'))
    expect(console.error).toHaveBeenCalledWith(expect.stringContaining('"errorName":"TypeError"'))
    const logged = vi.mocked(console.error).mock.calls.map((call) => call.join(' ')).join('\n')
    expect(logged).not.toContain(SECRET_DETAIL)
  })
})

describe('app/not-found.tsx', () => {
  it('renders the not-found heading with a link back to the home page', () => {
    render(<NotFound />)

    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe('Nie znaleziono strony')
    expect(screen.getByRole('link', { name: 'Wróć na stronę główną' }).getAttribute('href')).toBe('/')
  })

  it('logs a not-found event without the requested path', () => {
    render(<NotFound />)

    expect(console.info).toHaveBeenCalledWith(expect.stringContaining('"event":"app.not_found"'))
  })
})
