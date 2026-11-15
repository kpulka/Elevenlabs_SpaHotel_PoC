'use client'

import { CheckCircle2 } from 'lucide-react'
import { type FormEvent, useEffect, useRef, useState } from 'react'

import { HotelButton } from '@/components/hotel-button'
import { useLanguage } from '@/context/language-context'
import { HONEYPOT_FIELD } from '@/lib/contact/validation'

type FormState = {
  name: string
  email: string
  phone: string
  topic: string
  message: string
}

type SubmitStatus = 'idle' | 'sending' | 'sent' | 'error'

export function ContactForm() {
  const { t } = useLanguage()
  const [form, setForm] = useState<FormState>({
    name: '',
    email: '',
    phone: '',
    topic: t.contactPage.topicOptions[0],
    message: '',
  })
  // Honeypot: hidden from people and assistive technology; bots that fill every input fill this too.
  const [honeypot, setHoneypot] = useState('')
  const [errors, setErrors] = useState<Partial<FormState>>({})
  const [status, setStatus] = useState<SubmitStatus>('idle')
  const [submitError, setSubmitError] = useState<string | null>(null)
  const successRef = useRef<HTMLDivElement>(null)

  // Move focus to the success message so screen reader users hear it and the form is not lost.
  useEffect(() => {
    if (status === 'sent') successRef.current?.focus()
  }, [status])

  const updateField =
    (field: keyof FormState) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
      setForm((prev) => ({ ...prev, [field]: e.target.value }))
    }

  async function submitToServer(payload: FormState): Promise<{ ok: boolean; status: number }> {
    const res = await fetch('/api/contact', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ ...payload, [HONEYPOT_FIELD]: honeypot }),
    })
    return { ok: res.ok, status: res.status }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (status === 'sending') return

    const nextErrors: Partial<FormState> = {}
    if (!form.name.trim()) {
      nextErrors.name = t.contactPage.formErrors.name
    }
    if (!/^\S+@\S+\.\S+$/.test(form.email)) {
      nextErrors.email = t.contactPage.formErrors.email
    }
    if (!form.message.trim()) {
      nextErrors.message = t.contactPage.formErrors.message
    }

    setErrors(nextErrors)
    if (Object.keys(nextErrors).length > 0) {
      // Put the cursor on the first invalid field; the error text is announced via role="alert".
      const firstInvalid = (['name', 'email', 'message'] as const).find((key) => nextErrors[key])
      if (firstInvalid) document.getElementById(firstInvalid)?.focus()
      return
    }

    setStatus('sending')
    setSubmitError(null)
    try {
      const result = await submitToServer(form)
      if (result.ok) {
        setStatus('sent')
        return
      }
      setSubmitError(result.status === 429 ? t.contactPage.rateLimited : t.contactPage.submitError)
      setStatus('error')
    } catch {
      setSubmitError(t.contactPage.submitError)
      setStatus('error')
    }
  }

  if (status === 'sent') {
    return (
      <div
        ref={successRef}
        tabIndex={-1}
        role="status"
        className="mt-6 flex flex-col items-center gap-3 rounded-2xl border border-sage/30 bg-sage/10 p-8 text-center outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
      >
        <CheckCircle2 className="size-10 text-sage" aria-hidden="true" />
        <h3 className="font-serif text-xl font-semibold text-navy">{t.contactPage.successTitle}</h3>
        <p className="text-base leading-relaxed text-charcoal/80">
          {t.contactPage.successText}
        </p>
        {/* Explicit notice: this is a demo, the message is not delivered anywhere. */}
        <p className="mt-1 rounded-lg border border-gold/40 bg-warm-white px-4 py-2 text-sm text-charcoal/70">
          {t.contactPage.demoNote}
        </p>
      </div>
    )
  }

  const sending = status === 'sending'

  return (
    <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-5" noValidate>
      <div className="flex flex-col gap-2">
        <label htmlFor="name" className="text-sm font-medium text-navy">
          {t.contactPage.nameLabel}
        </label>
        <input
          id="name"
          name="name"
          type="text"
          autoComplete="name"
          value={form.name}
          onChange={updateField('name')}
          aria-invalid={Boolean(errors.name)}
          aria-describedby={errors.name ? 'name-error' : undefined}
          className="min-h-[52px] rounded-lg border border-input bg-warm-white px-4 text-base text-charcoal outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
        />
        {errors.name && (
          <p id="name-error" role="alert" className="text-sm text-error">
            {errors.name}
          </p>
        )}
      </div>

      <div className="flex flex-col gap-2">
        <label htmlFor="email" className="text-sm font-medium text-navy">
          {t.contactPage.emailLabel}
        </label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          value={form.email}
          onChange={updateField('email')}
          aria-invalid={Boolean(errors.email)}
          aria-describedby={errors.email ? 'email-error' : undefined}
          className="min-h-[52px] rounded-lg border border-input bg-warm-white px-4 text-base text-charcoal outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
        />
        {errors.email && (
          <p id="email-error" role="alert" className="text-sm text-error">
            {errors.email}
          </p>
        )}
      </div>

      <div className="flex flex-col gap-2">
        <label htmlFor="phone" className="text-sm font-medium text-navy">
          {t.contactPage.phoneLabel} ({t.contactPage.phoneOptional})
        </label>
        <input
          id="phone"
          name="phone"
          type="tel"
          autoComplete="tel"
          value={form.phone}
          onChange={updateField('phone')}
          className="min-h-[52px] rounded-lg border border-input bg-warm-white px-4 text-base text-charcoal outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
        />
      </div>

      <div className="flex flex-col gap-2">
        <label htmlFor="topic" className="text-sm font-medium text-navy">
          {t.contactPage.topicLabel}
        </label>
        <select
          id="topic"
          name="topic"
          value={form.topic}
          onChange={updateField('topic')}
          className="min-h-[52px] rounded-lg border border-input bg-warm-white px-4 text-base text-charcoal outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
        >
          {t.contactPage.topicOptions.map((topic) => (
            <option key={topic}>{topic}</option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-2">
        <label htmlFor="message" className="text-sm font-medium text-navy">
          {t.contactPage.messageLabel}
        </label>
        <textarea
          id="message"
          name="message"
          rows={5}
          value={form.message}
          onChange={updateField('message')}
          aria-invalid={Boolean(errors.message)}
          aria-describedby={errors.message ? 'message-error' : undefined}
          className="rounded-lg border border-input bg-warm-white px-4 py-3 text-base text-charcoal outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
        />
        {errors.message && (
          <p id="message-error" role="alert" className="text-sm text-error">
            {errors.message}
          </p>
        )}
      </div>

      {/* Honeypot: positioned off-screen, removed from the accessibility tree and the tab order. */}
      <div aria-hidden="true" className="sr-only">
        <label htmlFor={HONEYPOT_FIELD}>Website</label>
        <input
          id={HONEYPOT_FIELD}
          name={HONEYPOT_FIELD}
          type="text"
          tabIndex={-1}
          autoComplete="off"
          value={honeypot}
          onChange={(e) => setHoneypot(e.target.value)}
        />
      </div>

      {submitError && (
        <p role="alert" className="text-sm text-error">
          {submitError}
        </p>
      )}

      <HotelButton type="submit" variant="primary" fullWidth disabled={sending} aria-busy={sending}>
        {sending ? t.contactPage.sending : t.contactPage.sendButton}
      </HotelButton>
    </form>
  )
}
