'use client'

import { Mic, X } from 'lucide-react'
import Link from 'next/link'

import { useLanguage } from '@/context/language-context'
import { useAnnaWidget } from '@/hooks/use-anna-widget'
import { getPublicAgentId } from '@/lib/env'

export function AnnaEmbedWidget() {
  const { language, t } = useLanguage()
  const { showHint, setShowHint, widgetRef, triggerConvai, prepare, consentVisible } = useAnnaWidget(language)

  return (
    <>
      <div className="fixed right-4 bottom-4 z-[999] flex flex-col items-end gap-3 sm:right-6 sm:bottom-6">
        {/* Live region is always mounted so that the hint is announced when it appears. */}
        <div role="status" aria-live="polite" className="empty:hidden">
          {showHint && (
            <div className="max-w-[280px] rounded-2xl border border-gold/30 bg-warm-white p-4 pr-9 shadow-2xl motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-2">
              <button
                type="button"
                onClick={() => setShowHint(false)}
                aria-label={t.anna.closeHint}
                className="absolute top-2 right-2 flex size-7 items-center justify-center rounded-full text-muted-grey outline-none hover:bg-beige/60 focus-visible:outline-2 focus-visible:outline-gold"
              >
                <X className="size-4" aria-hidden="true" />
              </button>
              <p className="text-sm leading-relaxed text-charcoal">
                <strong>{t.anna.hintTitle}</strong> {t.anna.hintText}
              </p>
            </div>
          )}
        </div>

        {consentVisible && (
          <p
            id="anna-consent-notice"
            className="max-w-[280px] rounded-lg bg-navy/90 px-3 py-2 text-xs leading-relaxed text-white shadow-lg"
          >
            {t.anna.consentNotice}{' '}
            <Link href="/polityka" className="font-semibold text-gold underline-offset-2 outline-none hover:underline focus-visible:outline-2 focus-visible:outline-gold">
              {t.footer.privacyPolicy}
            </Link>
          </p>
        )}

        {/* Main branded floating button. Hover and focus start loading; only a click starts the conversation. */}
        <button
          id="anna-floating-trigger"
          type="button"
          onClick={triggerConvai}
          onPointerEnter={prepare}
          onFocus={prepare}
          aria-label={t.anna.fabAria}
          aria-describedby={consentVisible ? 'anna-consent-notice' : undefined}
          className="group relative flex h-14 sm:h-16 items-center gap-2 sm:gap-3 rounded-full bg-gold px-5 sm:px-6 text-navy shadow-2xl outline-none select-none touch-manipulation transition-transform active:scale-95 hover:scale-105 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-navy"
        >
          <span
            className="absolute inset-0 -z-10 rounded-full bg-gold/60 motion-safe:animate-ping motion-safe:[animation-duration:2.4s]"
            aria-hidden="true"
          />
          <Mic className="size-6 sm:size-7 shrink-0 text-navy" aria-hidden="true" />
          <span className="text-sm sm:text-base font-semibold whitespace-nowrap">{t.anna.fabButton}</span>
        </button>
      </div>

      {/* Official ElevenLabs ConvAI element. The agent id is set here, once, from the public variable. */}
      <elevenlabs-convai
        ref={(el) => {
          widgetRef.current = el
        }}
        agent-id={getPublicAgentId() ?? undefined}
      />
    </>
  )
}
