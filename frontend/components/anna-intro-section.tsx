'use client'

import { BedDouble, MapPinned, Mic, Waves } from 'lucide-react'
import Image from 'next/image'

import { useLanguage } from '@/context/language-context'
import { contactInfo } from '@/lib/hotel-data'

export function AnnaIntroSection() {
  const { t, language } = useLanguage()

  const helpTopics = [
    {
      icon: BedDouble,
      text:
        language === 'pl'
          ? 'Zarezerwuje pokój i odpowie na pytania o pobyt'
          : 'Reserves your room and answers any questions regarding your stay',
    },
    {
      icon: Waves,
      text:
        language === 'pl'
          ? 'Podpowie, jakie zabiegi SPA będą dla Pani/Pana odpowiednie'
          : 'Recommends suitable balneotherapy and spa treatments based on your health',
    },
    {
      icon: MapPinned,
      text:
        language === 'pl'
          ? 'Wyjaśni, jak dojechać i gdzie zaparkować'
          : 'Explains directions, parking, and complimentary electric shuttle pickup',
    },
  ]

  return (
    <section aria-labelledby="anna-heading" className="bg-navy py-16 md:py-24">
      <div className="mx-auto max-w-[1280px] px-4 md:px-8">
        <div className="grid gap-10 lg:grid-cols-[280px_1fr] lg:items-center">
          <div className="flex justify-center lg:justify-start">
            <div className="relative">
              <div
                className="absolute inset-0 -z-10 scale-110 rounded-full bg-gold/20 motion-safe:animate-pulse motion-safe:[animation-duration:3s]"
                aria-hidden="true"
              />
              <Image
                src="/images/anna-avatar.png"
                alt={t.anna.introTitle}
                width={220}
                height={220}
                className="size-[220px] rounded-full border-4 border-gold/40 object-cover"
              />
              <span className="absolute right-4 bottom-2 flex items-center gap-2 rounded-full bg-sage px-3 py-1.5 text-sm font-semibold text-white shadow-md">
                <span className="size-2 rounded-full bg-white" aria-hidden="true" />
                24/7 AI
              </span>
            </div>
          </div>

          <div>
            <p className="text-sm font-semibold tracking-[0.2em] text-gold uppercase">
              {t.anna.introBadge}
            </p>
            <h2 id="anna-heading" className="mt-3 font-serif text-3xl font-bold text-white md:text-4xl">
              {t.anna.introTitle}
            </h2>
            <p className="mt-4 max-w-2xl text-lg leading-relaxed text-white/85">
              {t.anna.introSubtitle}
            </p>

            <ul className="mt-8 flex flex-col gap-4">
              {helpTopics.map((topic) => {
                const Icon = topic.icon
                return (
                  <li key={topic.text} className="flex items-start gap-4">
                    <span className="flex size-11 shrink-0 items-center justify-center rounded-full bg-white/10 text-gold">
                      <Icon className="size-5" aria-hidden="true" />
                    </span>
                    <p className="pt-2 text-lg leading-relaxed text-white/90">{topic.text}</p>
                  </li>
                )
              })}
            </ul>

            <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:items-center">
              <button
                type="button"
                onClick={() => window.dispatchEvent(new CustomEvent('open-anna-widget'))}
                className="flex min-h-[56px] items-center justify-center gap-3 rounded-full bg-gold px-8 text-lg font-semibold text-navy outline-none transition-transform hover:scale-105 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
              >
                <Mic className="size-6" aria-hidden="true" />
                {t.anna.introCta}
              </button>
              <p className="text-base text-white/70">
                {language === 'pl' ? 'Wolisz zadzwonić?' : 'Prefer to call?'}{' '}
                <a
                  href={contactInfo.phoneHref}
                  className="font-semibold text-white underline-offset-4 outline-none hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold"
                >
                  {contactInfo.phone}
                </a>
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
