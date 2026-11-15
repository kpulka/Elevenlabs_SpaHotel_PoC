/**
 * Tiny structured logger: one JSON object per line, same shape in server and browser.
 *
 * Safety: callers pass only what they want to log. As a last line of defence, fields whose
 * name looks like a credential (key, secret, token, authorization, password) are dropped
 * before output. Never pass request headers, API keys or full upstream bodies.
 */

export type LogLevel = 'debug' | 'info' | 'warn' | 'error'
export type LogFields = Record<string, string | number | boolean | null | undefined>

const SENSITIVE_KEY = /key|secret|token|authorization|password|cookie/i

const CONSOLE_METHOD: Record<LogLevel, 'debug' | 'info' | 'warn' | 'error'> = {
  debug: 'debug',
  info: 'info',
  warn: 'warn',
  error: 'error',
}

export function sanitizeFields(fields: LogFields): LogFields {
  const out: LogFields = {}
  for (const [key, value] of Object.entries(fields)) {
    if (SENSITIVE_KEY.test(key)) continue
    out[key] = value
  }
  return out
}

/** Turns an unknown thrown value into loggable fields (name and message only, no stack). */
export function errorFields(err: unknown): LogFields {
  if (err instanceof Error) {
    return { errorName: err.name, errorMessage: err.message.slice(0, 300) }
  }
  return { errorMessage: String(err).slice(0, 300) }
}

export function log(level: LogLevel, event: string, fields: LogFields = {}): void {
  const line = JSON.stringify({
    ts: new Date().toISOString(),
    level,
    event,
    ...sanitizeFields(fields),
  })
  console[CONSOLE_METHOD[level]](line)
}

export const logger = {
  debug: (event: string, fields?: LogFields) => log('debug', event, fields),
  info: (event: string, fields?: LogFields) => log('info', event, fields),
  warn: (event: string, fields?: LogFields) => log('warn', event, fields),
  error: (event: string, fields?: LogFields) => log('error', event, fields),
}
