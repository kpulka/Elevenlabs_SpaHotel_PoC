/**
 * Single place that reads and validates the Anna / ElevenLabs environment.
 *
 * - ELEVENLABS_API_KEY: server only (secret). Never imported by client code.
 * - ELEVENLABS_AGENT_ID: server only. Falls back to NEXT_PUBLIC_ELEVENLABS_AGENT_ID
 *   (same agent, not a secret), so one value is enough for local setups.
 * - NEXT_PUBLIC_ELEVENLABS_AGENT_ID: inlined into the browser bundle by Next.js.
 *   Must be read with the literal `process.env.NEXT_PUBLIC_...` expression, otherwise
 *   the build cannot replace it.
 *
 * There is no hardcoded fallback agent id: a missing or malformed value is an error.
 * Error messages name the variable but never print its value.
 */

const AGENT_ID_PATTERN = /^agent_[A-Za-z0-9]{8,}$/

export class EnvConfigError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'EnvConfigError'
  }
}

export function isValidAgentId(value: string | undefined | null): value is string {
  return typeof value === 'string' && AGENT_ID_PATTERN.test(value)
}

function requireAgentId(name: string, value: string | undefined): string {
  if (value === undefined || value === '') {
    throw new EnvConfigError(`${name} is not set`)
  }
  if (!isValidAgentId(value)) {
    // Value deliberately omitted from the message.
    throw new EnvConfigError(`${name} is malformed (expected "agent_" followed by letters and digits)`)
  }
  return value
}

/** Server side: agent id for the signed-url endpoint. Throws EnvConfigError when misconfigured. */
export function getServerAgentId(): string {
  return requireAgentId(
    'ELEVENLABS_AGENT_ID',
    process.env.ELEVENLABS_AGENT_ID || process.env.NEXT_PUBLIC_ELEVENLABS_AGENT_ID,
  )
}

/** Server side: API key. Throws EnvConfigError when missing. The value is never included in errors. */
export function getServerApiKey(): string {
  const key = process.env.ELEVENLABS_API_KEY
  if (!key) {
    throw new EnvConfigError('ELEVENLABS_API_KEY is not set')
  }
  return key
}

/**
 * Client side (and shared): public agent id, or null when not configured.
 * Returns null instead of throwing so that a missing value only disables the voice widget,
 * not the whole site.
 */
export function getPublicAgentId(): string | null {
  const value = process.env.NEXT_PUBLIC_ELEVENLABS_AGENT_ID
  return isValidAgentId(value) ? value : null
}
