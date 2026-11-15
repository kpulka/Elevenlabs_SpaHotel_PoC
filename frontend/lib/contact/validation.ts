/**
 * Validation for the contact form payload (POST /api/contact).
 *
 * Pure functions, no I/O. Errors name the field only, never the submitted value, so they can be logged.
 */

export const CONTACT_LIMITS = {
  name: 100,
  email: 254,
  phone: 30,
  topic: 80,
  message: 2000,
} as const

/** Honeypot field name. Real visitors never see or fill it; simple bots fill every input. */
export const HONEYPOT_FIELD = 'website'

export type ContactMessage = {
  name: string
  email: string
  phone: string
  topic: string
  message: string
}

export type ContactValidation =
  | { kind: 'ok'; value: ContactMessage }
  | { kind: 'honeypot' }
  | { kind: 'invalid'; field: keyof ContactMessage | 'body' }

// Local part and domain without whitespace or extra @; the domain needs a dot. Deliberately simple:
// deliverability is checked by the mail system, not by a regex.
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
// Optional phone: digits, spaces, dashes, parentheses and an optional leading plus.
const PHONE_PATTERN = /^\+?[0-9 ()-]{6,30}$/

function readString(source: Record<string, unknown>, key: string): string | null {
  const value = source[key]
  return typeof value === 'string' ? value.trim() : null
}

/** Validates an already JSON-parsed body. Unknown extra fields are ignored. */
export function validateContactPayload(input: unknown): ContactValidation {
  if (typeof input !== 'object' || input === null || Array.isArray(input)) {
    return { kind: 'invalid', field: 'body' }
  }
  const source = input as Record<string, unknown>

  const honeypot = source[HONEYPOT_FIELD]
  if (typeof honeypot === 'string' && honeypot.trim() !== '') {
    return { kind: 'honeypot' }
  }

  const name = readString(source, 'name')
  if (name === null || name === '' || name.length > CONTACT_LIMITS.name) {
    return { kind: 'invalid', field: 'name' }
  }

  const email = readString(source, 'email')
  if (email === null || email.length > CONTACT_LIMITS.email || !EMAIL_PATTERN.test(email)) {
    return { kind: 'invalid', field: 'email' }
  }

  const phone = readString(source, 'phone')
  if (phone === null || phone.length > CONTACT_LIMITS.phone) {
    return { kind: 'invalid', field: 'phone' }
  }
  if (phone !== '' && !PHONE_PATTERN.test(phone)) {
    return { kind: 'invalid', field: 'phone' }
  }

  const topic = readString(source, 'topic')
  if (topic === null || topic.length > CONTACT_LIMITS.topic) {
    return { kind: 'invalid', field: 'topic' }
  }

  const message = readString(source, 'message')
  if (message === null || message === '' || message.length > CONTACT_LIMITS.message) {
    return { kind: 'invalid', field: 'message' }
  }

  return { kind: 'ok', value: { name, email, phone, topic, message } }
}
