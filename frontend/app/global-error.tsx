'use client'

import Link from 'next/link'
import { useEffect } from 'react'

import { logger } from '@/lib/logger'
import { translations } from '@/lib/translations'

/**
 * Root error boundary. It replaces the root layout, so there is no language provider, no global CSS and no
 * site header here: styles are inline and both languages are shown. Logs the digest and error name only.
 */
export default function GlobalError({
  error,
  retry,
}: {
  error: Error & { digest?: string }
  retry: () => void
}) {
  useEffect(() => {
    logger.error('app.global_error', { digest: error.digest ?? null, errorName: error.name })
  }, [error])

  const pl = translations.pl.errorPage
  const en = translations.en.errorPage
  const button = {
    display: 'inline-flex',
    minHeight: 52,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 8,
    padding: '0 24px',
    fontSize: 16,
    fontWeight: 500,
    cursor: 'pointer',
    border: '2px solid #1b2a4a',
    background: '#1b2a4a',
    color: '#ffffff',
  } as const

  return (
    <html lang="pl">
      <head>
        <title>Bukowy Dwór</title>
      </head>
      <body style={{ margin: 0, background: '#fbf8f3', color: '#1b2a4a', fontFamily: 'system-ui, sans-serif' }}>
        <main
          id="main-content"
          style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 16, padding: 16, textAlign: 'center' }}
        >
          <h1 style={{ fontSize: 28, margin: 0 }}>
            {pl.title} / {en.title}
          </h1>
          <p style={{ maxWidth: 560, lineHeight: 1.6, margin: 0 }}>
            {pl.text}
            <br />
            {en.text}
          </p>
          <button type="button" onClick={() => retry()} style={button}>
            {pl.retry} / {en.retry}
          </button>
          <Link href="/" style={{ color: '#1b2a4a' }}>
            {pl.home} / {en.home}
          </Link>
        </main>
      </body>
    </html>
  )
}
