import type { Language } from "../translations"
import { ROOM_FACTS } from "../generated/hotel-facts"
import { type L, loc } from "../i18n"

// ---------------------------------------------------------------------------
// Rooms
// Prices and the list of room types come from mock_backend/data/rooms.json via
// lib/generated/hotel-facts.ts. This file holds PL/EN copy only.
// ---------------------------------------------------------------------------

export type RoomId = (typeof ROOM_FACTS)[number]["id"]

type RoomCopy = {
  slug: L<string>
  name: L<string>
  capacity: L<string>
  image: string
  description: L<string>
  longDescription: L<string>
  features: L<string[]>
}

/**
 * `Record<RoomId, RoomCopy>` makes a new room type in rooms.json without copy
 * (or copy without a backend room) a compile error.
 */
const roomCopy: Record<RoomId, RoomCopy> = {
  jednoosobowy: {
    slug: { pl: "pokoj-jednoosobowy", en: "single-room" },
    name: { pl: "Pokój jednoosobowy", en: "Single Comfort Room" },
    capacity: { pl: "1 osoba", en: "1 Guest" },
    image: "/images/room-single.webp",
    description: {
      pl: "Spokojny, słoneczny pokój dla jednej osoby z widokiem na las bukowy. Idealny na dłuższy pobyt sanatoryjny.",
      en: "Quiet, sunlit room for one guest overlooking the beech forest. Ideal for health resort stays.",
    },
    longDescription: {
      pl: "Pokój jednoosobowy o powierzchni 22 m² urządzony w ciepłych, naturalnych barwach. Łóżko z materacem ortopedycznym, wygodny fotel do czytania i biurko. Duże okno zapewnia dużo naturalnego światła i widok na okoliczny las.",
      en: "Single room (22 m²) decorated in warm natural tones. Orthopedic mattress, ergonomic reading chair, and desk. Large window with picturesque forest scenery.",
    },
    features: {
      pl: [
        "Łóżko z materacem ortopedycznym",
        "Łazienka z uchwytami i brodzikiem bez progu",
        "Przycisk alarmowy przy łóżku",
        "Balkon lub loggia",
        "Telewizor i radio",
        "Czajnik i zestaw do herbaty",
      ],
      en: [
        "Orthopedic medical mattress",
        "Walk-in step-free shower with safety grab bars",
        "Bedside emergency call button",
        "Private balcony or loggia",
        "Smart TV & radio",
        "Electric kettle & herbal tea set",
      ],
    },
  },
  dwuosobowy: {
    slug: { pl: "pokoj-dwuosobowy", en: "double-room" },
    name: { pl: "Pokój dwuosobowy", en: "Double Comfort Room" },
    capacity: { pl: "2 osoby", en: "2 Guests" },
    image: "/images/room-double.webp",
    description: {
      pl: "Przestronny pokój dla dwóch osób z wygodną strefą wypoczynkową i widokiem na góry.",
      en: "Spacious room for two guests with a comfortable relaxation area and mountain views.",
    },
    longDescription: {
      pl: "Pokój dwuosobowy o powierzchni 30 m² z dwoma łóżkami lub łóżkiem małżeńskim do wyboru. Oddzielna strefa wypoczynkowa z fotelami, duża łazienka przystosowana dla osób z ograniczoną mobilnością.",
      en: "Double room (30 m²) with twin beds or king-size bed. Separate lounge area with armchairs and fully barrier-free accessible bathroom.",
    },
    features: {
      pl: [
        "Dwa łóżka lub łóżko małżeńskie",
        "Łazienka z uchwytami i brodzikiem bez progu",
        "Przycisk alarmowy przy łóżku",
        "Strefa wypoczynkowa z fotelami",
        "Balkon z widokiem na las",
        "Telewizor, radio, sejf",
      ],
      en: [
        "Twin beds or king-size bed",
        "Walk-in step-free shower with grab bars",
        "Emergency call buttons in bedroom & bathroom",
        "Lounge seating area with armchairs",
        "Balcony with panoramic forest view",
        "TV, digital radio, safe",
      ],
    },
  },
  apartament: {
    slug: { pl: "apartament", en: "apartment-suite" },
    name: { pl: "Apartament", en: "Executive Health Suite" },
    capacity: { pl: "2–3 osoby", en: "2–3 Guests" },
    image: "/images/room-apartment.webp",
    description: {
      pl: "Apartament z osobnym salonem — najwięcej przestrzeni i komfortu, dla gości z opiekunem lub rodziną.",
      en: "Suite with separate living room — maximum comfort and space for guests with family or caregiver.",
    },
    longDescription: {
      pl: "Apartament o powierzchni 55 m² z sypialnią oraz osobnym salonem. Dodatkowe miejsce do spania dla osoby towarzyszącej. Duża, w pełni dostępna łazienka oraz prywatny balkon z widokiem na górski krajobraz.",
      en: "Luxury apartment (55 m²) featuring a master bedroom and separate living room. Extra sofa bed, premium accessible bathroom, and wide private terrace.",
    },
    features: {
      pl: [
        "Sypialnia + osobny salon",
        "Dodatkowe miejsce do spania",
        "Łazienka w pełni dostępna, prysznic bez progu",
        "Przycisk alarmowy w sypialni i łazience",
        "Prywatny, przestronny balkon",
        "Minibar, sejf, telewizor",
      ],
      en: [
        "Master bedroom + separate living room",
        "Extra sleeping accommodation for companion",
        "100% barrier-free bathroom with level-entry shower",
        "Emergency call buttons in bedroom & bathroom",
        "Private spacious scenic balcony",
        "Minibar, safe, 4K TV",
      ],
    },
  },
}

export type Room = {
  id: RoomId
  slug: string
  name: string
  price: number
  capacity: string
  image: string
  description: string
  longDescription: string
  features: string[]
}

export function getRooms(lang: Language): Room[] {
  return ROOM_FACTS.map((fact) => {
    const copy = roomCopy[fact.id]
    return {
      id: fact.id,
      slug: loc(copy.slug, lang),
      name: loc(copy.name, lang),
      price: fact.pricePerNight,
      capacity: loc(copy.capacity, lang),
      image: copy.image,
      description: loc(copy.description, lang),
      longDescription: loc(copy.longDescription, lang),
      features: loc(copy.features, lang),
    }
  })
}
