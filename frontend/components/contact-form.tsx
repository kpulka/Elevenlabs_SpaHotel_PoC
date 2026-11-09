'use client'

import { CheckCircle2 } from 'lucide-react'
import { type FormEvent, useState } from 'react'

import { HotelButton } from '@/components/hotel-button'
import { useLanguage } from '@/context/language-context'

type FormState = {
  name: string
  email: string
  phone: string
  topic: string
  message: string
}

export function ContactForm() {
  const { language, t } = useLanguage()
  const [form, setForm] = useState<FormState>({
    name: '',
    email: '',
    phone: '',
    topic: language === 'pl' ? 'Rezerwacja pokoju' : 'Room Reservation',
    message: '',
  })
  const [errors, setErrors] = useState<Partial<FormState>>({})
  const [submitted, setSubmitted] = useState(false)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextErrors: Partial<FormState> = {}
    if (!form.name.trim()) {
      nextErrors.name = language === 'pl' ? 'Podaj swoje imię i nazwisko.' : 'Please provide your full name.'
    }
    if (!/^\S+@\S+\.\S+$/.test(form.email)) {
      nextErrors.email = language === 'pl' ? 'Podaj prawidłowy adres e-mail.' : 'Please enter a valid email address.'
    }
    if (!form.message.trim()) {
      nextErrors.message = language === 'pl' ? 'Napisz krótką treść zapytania.' : 'Please provide a message.'
    }

    setErrors(nextErrors)
    if (Object.keys(nextErrors).length === 0) {
      setSubmitted(true)
    }
  }

  if (submitted) {
    return (
      <div className="mt-6 flex flex-col items-center gap-3 rounded-2xl border border-sage/30 bg-sage/10 p-8 text-center">
        <CheckCircle2 className="size-10 text-sage" aria-hidden="true" />
        <h3 className="font-serif text-xl font-semibold text-navy">{t.contactPage.successTitle}</h3>
        <p className="text-base leading-relaxed text-charcoal/80">
          {t.contactPage.successText}
        </p>
        {/* Jawna informacja: to demo, formularz nic nie wysyła. */}
        <p className="mt-1 rounded-lg border border-gold/40 bg-warm-white px-4 py-2 text-sm text-charcoal/70">
          {language === 'pl'
            ? 'Wersja demonstracyjna: formularz nie wysyła wiadomości i nie zapisuje danych — w razie pilnej rezerwacji zadzwoń do recepcji.'
            : 'Demo build: this form does not send or store anything — for an urgent booking, please call the front desk.'}
        </p>
      </div>
    )
  }

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
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          aria-invalid={Boolean(errors.name)}
          aria-describedby={errors.name ? 'name-error' : undefined}
          className="min-h-[52px] rounded-lg border border-input bg-warm-white px-4 text-base text-charcoal outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
        />
        {errors.name && (
          <p id="name-error" className="text-sm text-error">
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
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          aria-invalid={Boolean(errors.email)}
          aria-describedby={errors.email ? 'email-error' : undefined}
          className="min-h-[52px] rounded-lg border border-input bg-warm-white px-4 text-base text-charcoal outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
        />
        {errors.email && (
          <p id="email-error" className="text-sm text-error">
            {errors.email}
          </p>
        )}
      </div>

      <div className="flex flex-col gap-2">
        <label htmlFor="phone" className="text-sm font-medium text-navy">
          {t.contactPage.phoneLabel} ({language === 'pl' ? 'opcjonalnie' : 'optional'})
        </label>
        <input
          id="phone"
          name="phone"
          type="tel"
          autoComplete="tel"
          value={form.phone}
          onChange={(e) => setForm({ ...form, phone: e.target.value })}
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
          onChange={(e) => setForm({ ...form, topic: e.target.value })}
          className="min-h-[52px] rounded-lg border border-input bg-warm-white px-4 text-base text-charcoal outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
        >
          {language === 'pl' ? (
            <>
              <option>Rezerwacja pokoju</option>
              <option>Zabiegi SPA</option>
              <option>Dieta lecznicza</option>
              <option>Dojazd i dostępność</option>
              <option>Inne</option>
            </>
          ) : (
            <>
              <option>Room Reservation</option>
              <option>Medical Spa Treatments</option>
              <option>Specialized Diets</option>
              <option>Directions & Accessibility</option>
              <option>Other Inquiry</option>
            </>
          )}
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
          onChange={(e) => setForm({ ...form, message: e.target.value })}
          aria-invalid={Boolean(errors.message)}
          aria-describedby={errors.message ? 'message-error' : undefined}
          className="rounded-lg border border-input bg-warm-white px-4 py-3 text-base text-charcoal outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
        />
        {errors.message && (
          <p id="message-error" className="text-sm text-error">
            {errors.message}
          </p>
        )}
      </div>

      <HotelButton type="submit" variant="primary" fullWidth>
        {t.contactPage.sendButton}
      </HotelButton>
    </form>
  )
}
