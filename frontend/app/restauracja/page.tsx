'use client'

import Image from 'next/image'

import { HotelButton } from '@/components/hotel-button'
import { SiteFooter } from '@/components/site-footer'
import { SiteHeader } from '@/components/site-header'
import { useLanguage } from '@/context/language-context'
import { getDiets, getMealTimes } from '@/lib/hotel-data'

export default function RestaurantPage() {
  const { language, t } = useLanguage()
  const currentMealTimes = getMealTimes(language)
  const currentDiets = getDiets(language)

  return (
    <>
      <SiteHeader />
      <main id="main-content">
        <section className="relative flex min-h-[420px] items-center overflow-hidden">
          <Image
            src="/images/restaurant.png"
            alt={t.images.restaurantHeroAlt}
            fill
            priority
            className="object-cover"
          />
          <div className="absolute inset-0 bg-navy/60" />
          <div className="relative z-10 mx-auto max-w-[1280px] px-4 md:px-8">
            <p className="text-sm font-semibold tracking-[0.2em] text-gold uppercase">
              {t.diningPage.tag}
            </p>
            <h1 className="mt-3 max-w-2xl text-balance font-serif text-4xl font-bold text-white md:text-5xl">
              {t.diningPage.title}
            </h1>
            <p className="mt-4 max-w-2xl text-lg leading-relaxed text-white/90">
              {t.diningPage.subtitle}
            </p>
          </div>
        </section>

        <section className="bg-warm-white py-16 md:py-24">
          <div className="mx-auto max-w-[1280px] px-4 md:px-8">
            <h2 className="font-serif text-3xl font-bold text-navy">{t.diningPage.hoursHeader}</h2>
            <div className="mt-8 grid gap-6 sm:grid-cols-3">
              {currentMealTimes.map((meal) => (
                <div
                  key={meal.name}
                  className="rounded-2xl border border-gold/20 bg-cream p-6 text-center"
                >
                  <h3 className="font-serif text-xl font-semibold text-navy">{meal.name}</h3>
                  <p className="mt-2 text-lg text-charcoal/80">{meal.hours}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="bg-cream py-16 md:py-24">
          <div className="mx-auto max-w-[1280px] px-4 md:px-8">
            <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
              <div className="relative aspect-[4/3] w-full overflow-hidden rounded-2xl border border-gold/20 shadow-md">
                <Image
                  src="/images/restaurant-dishes.png"
                  alt={t.images.restaurantDishesAlt}
                  fill
                  className="object-cover"
                />
              </div>
              <div>
                <p className="text-sm font-semibold tracking-[0.15em] text-sage uppercase">
                  {t.diningPage.philosophyEyebrow}
                </p>
                <h2 className="mt-3 font-serif text-3xl font-bold text-navy md:text-4xl">
                  {t.diningPage.philosophyTitle}
                </h2>
                <p className="mt-4 text-lg leading-relaxed text-charcoal/85">
                  {t.diningPage.philosophyText}
                </p>
                <div className="mt-6 flex flex-wrap gap-4 text-sm font-medium text-navy">
                  <span className="rounded-full bg-warm-white px-4 py-2 border border-gold/20">
                    {t.diningPage.philosophyBadgeProduce}
                  </span>
                  <span className="rounded-full bg-warm-white px-4 py-2 border border-gold/20">
                    {t.diningPage.philosophyBadgeSalt}
                  </span>
                  <span className="rounded-full bg-warm-white px-4 py-2 border border-gold/20">
                    {t.diningPage.philosophyBadgeFish}
                  </span>
                </div>
              </div>
            </div>

            <div className="mt-20">
              <p className="text-sm font-semibold tracking-[0.15em] text-sage uppercase text-center">
                {t.diningPage.dietHeader}
              </p>
              <h2 className="mt-2 text-center font-serif text-3xl font-bold text-navy md:text-4xl">
                {t.diningPage.dietSubtitle}
              </h2>
              <p className="mx-auto mt-3 max-w-2xl text-center text-base text-charcoal/80">
                {t.diningPage.dietNotice}
              </p>
              <div className="mt-10 grid gap-6 sm:grid-cols-3">
                {currentDiets.map((diet) => (
                  <div
                    key={diet.id}
                    className="flex flex-col gap-3 rounded-2xl border border-gold/20 bg-warm-white p-6"
                  >
                    <h3 className="font-serif text-xl font-semibold text-navy">{diet.name}</h3>
                    <p className="text-base leading-relaxed text-charcoal/80">{diet.description}</p>
                    {diet.note && (
                      <p className="text-sm font-medium text-sage">{diet.note}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="bg-navy py-16 text-center md:py-20">
          <div className="mx-auto max-w-2xl px-4 md:px-8">
            <h2 className="font-serif text-3xl font-bold text-white">
              {t.diningPage.dietCtaTitle}
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-white/85">
              {t.diningPage.dietCtaText}
            </p>
            <div className="mt-8 flex justify-center">
              <HotelButton href="/kontakt" variant="primary" className="bg-gold text-navy hover:bg-gold/90">
                {t.diningPage.dietCtaButton}
              </HotelButton>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  )
}
