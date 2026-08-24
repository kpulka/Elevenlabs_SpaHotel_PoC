'use client'

import { CheckCircle2 } from 'lucide-react'
import { type FormEvent, useState } from 'react'

import { HotelButton } from '@/components/hotel-button'

type FormState = {
  name: string
  email: string
  phone: string
  topic: string
  message: string
}

const initialState: FormState = {
  name: '',
  email: '',
  phone: '',
  topic: 'Rezerwacja pokoju',
  message: '',
}

export function ContactForm() {
  const [form, setForm] = useState<FormState>(initialState)
  const [errors, setErrors] = useState<Partial<FormState>>({})
  const [submitted, setSubmitted] = useState(false)

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const nextErrors: Partial<FormState> = {}
    if (!form.name.trim()) nextErrors.name = 'Podaj swoje imię i nazwisko.'
    if (!/^\S+@\S+\.\S+$/.test(form.email)) nextErrors.email = 'Podaj prawidłowy adres e-mail.'
    if (!form.message.trim()) nextErrors.message = 'Napisz krótką treść zapytania.'

    setErrors(nextErrors)
    if (Object.keys(nextErrors).length === 0) {
      setSubmitted(true)
    }
  }

  if (submitted) {
    return (
      <div className="mt-6 flex flex-col items-center gap-3 rounded-2xl border border-sage/30 bg-sage/10 p-8 text-center">
        <CheckCircle2 className="size-10 text-sage" aria-hidden="true" />
        <h3 className="font-serif text-xl font-semibold text-navy">Dziękujemy za wiadomość</h3>
        <p className="text-base leading-relaxed text-charcoal/80">
          Odpowiemy na Twoje zapytanie w ciągu 24 godzin.
        </p>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-5" noValidate>
      <div className="flex flex-col gap-2">
        <label htmlFor="name" className="text-sm font-medium text-navy">
          Imię i nazwisko
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
          Adres e-mail
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
          Numer telefonu (opcjonalnie)
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
          Temat zapytania
        </label>
        <select
          id="topic"
          name="topic"
          value={form.topic}
          onChange={(e) => setForm({ ...form, topic: e.target.value })}
          className="min-h-[52px] rounded-lg border border-input bg-warm-white px-4 text-base text-charcoal outline-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
        >
          <option>Rezerwacja pokoju</option>
          <option>Zabiegi SPA</option>
          <option>Dieta lecznicza</option>
          <option>Dojazd i dostępność</option>
          <option>Inne</option>
        </select>
      </div>

      <div className="flex flex-col gap-2">
        <label htmlFor="message" className="text-sm font-medium text-navy">
          Treść wiadomości
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
        Wyślij zapytanie
      </HotelButton>
    </form>
  )
}
