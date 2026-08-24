import type { Metadata } from 'next'
import Image from 'next/image'

import { HotelButton } from '@/components/hotel-button'
import { SiteFooter } from '@/components/site-footer'
import { SiteHeader } from '@/components/site-header'
import { diets, mealTimes } from '@/lib/hotel-data'

export const metadata: Metadata = {
  title: 'Restauracja — Bukowy Dwór',
  description:
    'Restauracja Bukowego Dworu — posiłki dostosowane do diet leczniczych, przygotowywane przez dietetyka. Śniadania, obiady i kolacje w ustalonych godzinach.',
}

export default function RestaurantPage() {
  return (
    <>
      <SiteHeader />
      <main id="main-content">
        <section className="relative flex min-h-[420px] items-center overflow-hidden">
          <Image
            src="/images/restaurant.png"
            alt="Wnętrze restauracji Bukowego Dworu"
            fill
            priority
            className="object-cover"
          />
          <div className="absolute inset-0 bg-navy/60" />
          <div className="relative z-10 mx-auto max-w-[1280px] px-4 md:px-8">
            <p className="text-sm font-semibold tracking-[0.2em] text-gold uppercase">
              Odżywianie i regeneracja
            </p>
            <h1 className="mt-3 max-w-2xl text-balance font-serif text-4xl font-bold text-white md:text-5xl">
              Restauracja
            </h1>
            <p className="mt-4 max-w-2xl text-lg leading-relaxed text-white/90">
              Posiłki przygotowywane pod nadzorem dietetyka, dostosowane do zaleceń zdrowotnych
              każdego gościa.
            </p>
          </div>
        </section>

        <section className="bg-warm-white py-16 md:py-24">
          <div className="mx-auto max-w-[1280px] px-4 md:px-8">
            <h2 className="font-serif text-3xl font-bold text-navy">Godziny posiłków</h2>
            <div className="mt-8 grid gap-6 sm:grid-cols-3">
              {mealTimes.map((meal) => (
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
                  alt="Zdrowe danie diety leczniczej przygotowane przez dietetyka Bukowego Dworu"
                  fill
                  className="object-cover"
                />
              </div>
              <div>
                <p className="text-sm font-semibold tracking-[0.15em] text-sage uppercase">
                  Filozofia kulinarna
                </p>
                <h2 className="mt-3 font-serif text-3xl font-bold text-navy md:text-4xl">
                  Leczenie poprzez smak i naturę
                </h2>
                <p className="mt-4 text-lg leading-relaxed text-charcoal/85">
                  Wszystkie dania w Bukowym Dworze przygotowujemy ze świeżych, lokalnych produktów
                  z regionu Beskidu Sądeckiego. Nasz zespół kucharzy współpracuje bezpośrednio z
                  lekarzem i dietetykiem, łącząc tradycyjną kuchnię z nowoczesnymi zasadami
                  dietetyki klinicznej.
                </p>
                <div className="mt-6 flex flex-wrap gap-4 text-sm font-medium text-navy">
                  <span className="rounded-full bg-warm-white px-4 py-2 border border-gold/20">🌱 Świeże zioła i warzywa</span>
                  <span className="rounded-full bg-warm-white px-4 py-2 border border-gold/20">💧 Ograniczona sól</span>
                  <span className="rounded-full bg-warm-white px-4 py-2 border border-gold/20">🐟 Ryby i chude mięsa</span>
                </div>
              </div>
            </div>

            <div className="mt-20">
              <p className="text-sm font-semibold tracking-[0.15em] text-sage uppercase text-center">
                Diety lecznicze
              </p>
              <h2 className="mt-2 text-center font-serif text-3xl font-bold text-navy md:text-4xl">
                Posiłki dopasowane do potrzeb zdrowotnych
              </h2>
              <div className="mt-10 grid gap-6 sm:grid-cols-3">
                {diets.map((diet) => (
                  <div
                    key={diet.id}
                    className="flex flex-col gap-3 rounded-2xl border border-gold/20 bg-warm-white p-6"
                  >
                    <h3 className="font-serif text-xl font-semibold text-navy">{diet.name}</h3>
                    <p className="text-base leading-relaxed text-charcoal/80">{diet.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="bg-navy py-16 text-center md:py-20">
          <div className="mx-auto max-w-2xl px-4 md:px-8">
            <h2 className="font-serif text-3xl font-bold text-white">
              Potrzebujesz diety specjalnej?
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-white/85">
              Poinformuj nas o swoich zaleceniach dietetycznych podczas rezerwacji — nasz
              dietetyk przygotuje odpowiedni jadłospis.
            </p>
            <div className="mt-8 flex justify-center">
              <HotelButton href="/kontakt" variant="primary" className="bg-gold text-navy hover:bg-gold/90">
                Skontaktuj się z nami
              </HotelButton>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  )
}
