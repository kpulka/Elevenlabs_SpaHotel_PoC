'use client'

import { Check } from 'lucide-react'
import Image from 'next/image'

import { HotelButton } from '@/components/hotel-button'
import { useLanguage } from '@/context/language-context'
import type { Room } from '@/lib/hotel-data'

export function RoomCard({ room }: { room: Room }) {
  const { t } = useLanguage()

  return (
    <article className="flex flex-col overflow-hidden rounded-2xl border border-gold/20 bg-warm-white">
      <div className="relative aspect-[4/3] w-full">
        <Image
          src={room.image}
          alt={`${room.name} — Bukowy Dwór`}
          fill
          sizes="(min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw"
          className="object-cover"
        />
      </div>
      <div className="flex flex-1 flex-col gap-4 p-6">
        <div>
          <h3 className="font-serif text-2xl font-bold text-navy">{room.name}</h3>
          <p className="mt-1 text-sm text-muted-grey">{room.capacity}</p>
        </div>
        <p className="text-base leading-relaxed text-charcoal/85">{room.description}</p>
        <ul className="flex flex-col gap-2">
          {room.features.slice(0, 3).map((feature) => (
            <li key={feature} className="flex items-start gap-2 text-sm text-charcoal/80">
              <Check className="mt-0.5 size-4 shrink-0 text-sage" aria-hidden="true" />
              {feature}
            </li>
          ))}
        </ul>
        <div className="mt-auto flex items-center justify-between gap-4 pt-2">
          <p className="font-serif text-2xl font-bold text-navy">
            {room.price} <span className="text-sm font-normal text-muted-grey">{t.roomsPage.perNight}</span>
          </p>
          <HotelButton href="/kontakt" variant="secondary" className="px-6">
            {t.roomsPage.bookRoom}
          </HotelButton>
        </div>
      </div>
    </article>
  )
}
