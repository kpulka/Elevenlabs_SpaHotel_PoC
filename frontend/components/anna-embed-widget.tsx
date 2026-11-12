'use client'

import { Mic, X } from 'lucide-react'

import { useLanguage } from '@/context/language-context'
import { AGENT_ID, useAnnaWidget } from '@/hooks/use-anna-widget'

export function AnnaEmbedWidget() {
  const { language, t } = useLanguage()
  const { showHint, setShowHint, widgetRef, triggerConvai } = useAnnaWidget(language)

  return (
    <>
      {/* Pływający pasek podpowiedzi */}
      {showHint && (
        <div className="fixed right-4 bottom-24 z-[998] max-w-[280px] rounded-2xl border border-gold/30 bg-warm-white p-4 pr-9 shadow-2xl motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-bottom-2 sm:right-6">
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

      {/* Główny, markowy przycisk pływający na dole ekranu */}
      <div className="fixed right-4 bottom-4 z-[999] sm:right-6 sm:bottom-6">
        <button
          id="anna-floating-trigger"
          type="button"
          onClick={triggerConvai}
          aria-label={t.anna.fabAria}
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

      {/* Oficjalny komponent ElevenLabs ConvAI */}
      <elevenlabs-convai
        ref={(el) => {
          widgetRef.current = el
        }}
        agent-id={AGENT_ID}
      />
    </>
  )
}
