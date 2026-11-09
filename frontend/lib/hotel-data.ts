import type { Language } from "./translations"
import { ROOM_FACTS, SITE_TREATMENTS } from "./generated/hotel-facts"

/** Dwujęzyczna wartość — jedno miejsce na parę PL/EN zamiast dwóch równoległych tablic. */
export type L<T> = { pl: T; en: T }

/** Wybór wariantu językowego z rekordu dwujęzycznego. */
export function loc<T>(value: L<T>, lang: Language): T {
  return lang === "en" ? value.en : value.pl
}

// ---------------------------------------------------------------------------
// Pokoje
// Cena i lista typów pochodzą z mock_backend/data/rooms.json przez
// lib/generated/hotel-facts.ts. Tutaj jest wyłącznie copy PL/EN.
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
 * `Record<RoomId, RoomCopy>` sprawia, że nowy typ pokoju w rooms.json bez copy
 * (albo copy bez pokoju w backendzie) jest błędem kompilacji.
 */
const roomCopy: Record<RoomId, RoomCopy> = {
  jednoosobowy: {
    slug: { pl: "pokoj-jednoosobowy", en: "single-room" },
    name: { pl: "Pokój jednoosobowy", en: "Single Comfort Room" },
    capacity: { pl: "1 osoba", en: "1 Guest" },
    image: "/images/room-single.png",
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
    image: "/images/room-double.png",
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
    image: "/images/room-apartment.png",
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

// ---------------------------------------------------------------------------
// Zabiegi
// Id, ceny i czasy trwania pochodzą z mock_backend/data/spa_schedule.json
// (przez lib/generated/hotel-facts.ts). Tutaj jest wyłącznie copy PL/EN oraz
// dwa wpisy lokalne: baseny to udogodnienia strefy basenowej (w cenie pobytu,
// bez rezerwacji), a nie zabiegi z katalogu głosowego.
// ---------------------------------------------------------------------------

/** Klucz kategorii; etykiety PL/EN żyją w translations.spaPage.category*. */
export type TreatmentCategory = "thermal" | "balneo" | "physio"

type SiteTreatmentId = (typeof SITE_TREATMENTS)[number]["id"]

/** Wpisy wyłącznie lokalne — nie ma ich w katalogu backendu, więc nie są rezerwowalne. */
type LocalTreatmentId = "basen-32" | "basen-34"

export type TreatmentId = SiteTreatmentId | LocalTreatmentId

type TreatmentCopy = {
  category: TreatmentCategory
  name: L<string>
  description: L<string>
  image?: string
  /** Baseny: wstęp w cenie pobytu, bez rezerwacji i bez limitu czasu. */
  includedInStay?: boolean
  /** Czas trwania wpisu lokalnego; zabiegi z backendu biorą go z durationMin. */
  durationNote?: L<string>
}

/**
 * `Record<TreatmentId, TreatmentCopy>` wymusza komplet copy dla każdego
 * identyfikatora z katalogu backendu — brak wpisu to błąd kompilacji,
 * a nie pusta etykieta na stronie. Kolejność kluczy = kolejność wyświetlania.
 * Ceny i czasy trwania NIE są tu wpisywane — pochodzą z danych generowanych.
 */
const treatmentCopy: Record<TreatmentId, TreatmentCopy> = {
  "basen-32": {
    category: "thermal",
    name: { pl: "Basen termalny 32°C", en: "Thermal Relaxation Pool 32°C" },
    includedInStay: true,
    durationNote: { pl: "bez limitu w godzinach otwarcia", en: "Unlimited during opening hours" },
    image: "/images/spa-pool.png",
    description: {
      pl: "Basen relaksacyjny o łagodnej temperaturze, dostępny dla wszystkich gości hotelowych w ramach pobytu.",
      en: "Gentle mineral relaxation pool, open to all resort guests as part of their stay.",
    },
  },
  "basen-34": {
    category: "thermal",
    name: { pl: "Basen termalny 34°C", en: "Thermal Hydrotherapy Pool 34°C" },
    includedInStay: true,
    durationNote: { pl: "bez limitu w godzinach otwarcia", en: "Unlimited during opening hours" },
    image: "/images/hero-pool.png",
    description: {
      pl: "Cieplejszy basen solankowy o właściwościach rozluźniających mięśnie, polecany szczególnie przy dolegliwościach reumatycznych.",
      en: "Warmer brine pool with muscle-relaxing properties, recommended especially for rheumatic complaints.",
    },
  },
  "kapiel-siarczkowa": {
    category: "balneo",
    name: { pl: "Kąpiel siarczkowa „Ukojenie Stawów”", en: "Sulphur Bath “Joint Relief”" },
    image: "/images/treatment-sulphur-bath.png",
    description: {
      pl: "Kąpiel w naturalnej wodzie siarczkowej pod nadzorem personelu medycznego — działa przeciwzapalnie, ułatwia ruch w stawach i przynosi ulgę w dolegliwościach reumatycznych.",
      en: "Bath in natural sulphur-rich thermal water supervised by medical staff — anti-inflammatory, eases joint movement, and relieves rheumatic complaints.",
    },
  },
  "masaz-leczniczy": {
    category: "physio",
    name: {
      pl: "Delikatny masaż leczniczy pleców",
      en: "Gentle Therapeutic Back Massage",
    },
    image: "/images/treatment-massage.png",
    description: {
      pl: "Delikatny masaż pleców wykonywany przez fizjoterapeutę i dopasowany do stanu zdrowia gościa — rozluźnia napięcie mięśniowe i uśmierza ból kręgosłupa.",
      en: "Gentle back massage delivered by a physiotherapist and adapted to your health — releases muscle tension and eases spinal pain.",
    },
  },
  "kapiel-borowinowa": {
    category: "balneo",
    name: {
      pl: "Kąpiel borowinowa „Głęboka Regeneracja”",
      en: "Peat Mud Bath “Deep Regeneration”",
    },
    image: "/images/treatment-mud-bath.png",
    description: {
      pl: "Kąpiel z naturalnym torfem leczniczym — głęboko rozgrzewa, łagodzi bóle stawów i wspomaga krążenie.",
      en: "Bath in natural therapeutic peat — warms deeply, relieves joint pain, and supports circulation.",
    },
  },
  jonoforeza: {
    category: "balneo",
    name: {
      pl: "Jonoforeza (zabieg elektrolecznicowy)",
      en: "Iontophoresis (Electrotherapy Treatment)",
    },
    image: "/images/treatment-electrotherapy.png",
    description: {
      pl: "Zabieg elektroleczniczy wprowadzający leki przeciwbólowe przez skórę prądem stałym — stosowany w bólach kręgosłupa i stawów.",
      en: "Electrotherapy treatment introducing pain-relieving medication through the skin with direct current — used for spinal and joint pain.",
    },
  },
  "masaz-klasyczny": {
    category: "physio",
    name: { pl: "Masaż klasyczny relaksacyjny", en: "Classic Relaxation Massage" },
    image: "/images/treatment-massage.png",
    description: {
      pl: "Masaż całego ciała w spokojnym, relaksacyjnym tempie — poprawia krążenie, rozluźnia napięcie mięśniowe i dopełnia pobyt sanatoryjny.",
      en: "Full-body massage at a calm, relaxing pace — improves circulation, releases muscle tension, and complements your health-resort stay.",
    },
  },
  "gimnastyka-lecznicza": {
    category: "physio",
    name: { pl: "Gimnastyka lecznicza (grupowa)", en: "Therapeutic Group Gymnastics" },
    image: "/images/treatment-gymnastics.png",
    description: {
      pl: "Zajęcia grupowe z fizjoterapeutą, dostosowane do możliwości seniorów — poprawiają ruchomość stawów i bezpieczeństwo codziennych czynności.",
      en: "Group sessions led by a physiotherapist and adapted to seniors’ abilities — improve joint mobility and everyday safety.",
    },
  },
}

/** Fakty z backendu po id — cena i czas trwania nie są nigdzie wpisywane ręcznie. */
const treatmentFacts = new Map<string, (typeof SITE_TREATMENTS)[number]>(
  SITE_TREATMENTS.map((fact) => [fact.id, fact])
)

/** Kolejność wyświetlania: baseny (strefa) -> zabiegi w kolejności z katalogu backendu. */
const treatmentOrder: TreatmentId[] = [
  "basen-32",
  "basen-34",
  ...SITE_TREATMENTS.map((fact) => fact.id),
]

export type Treatment = {
  id: TreatmentId
  category: TreatmentCategory
  name: string
  duration: string
  price: number
  includedInStay: boolean
  description: string
  image?: string
}

export function getTreatments(lang: Language): Treatment[] {
  return treatmentOrder.map((id) => {
    const copy = treatmentCopy[id]
    const fact = treatmentFacts.get(id)
    if (!fact && !copy.durationNote) {
      throw new Error(`[hotel-data] zabieg "${id}" nie ma ani faktu z backendu, ani czasu lokalnego`)
    }
    return {
      id,
      category: copy.category,
      name: loc(copy.name, lang),
      duration: fact
        ? `${fact.durationMin} min`
        : loc(copy.durationNote as L<string>, lang),
      price: fact ? fact.pricePln : 0,
      includedInStay: Boolean(copy.includedInStay),
      description: loc(copy.description, lang),
      image: copy.image,
    }
  })
}

// ---------------------------------------------------------------------------
// Diety
// ---------------------------------------------------------------------------

export type Diet = {
  id: string
  name: string
  description: string
  /** Dodatkowa informacja praktyczna (np. termin zgłoszenia diety). */
  note?: string
}

type DietCopy = {
  id: string
  name: L<string>
  description: L<string>
  note?: L<string>
}

/**
 * Dokładnie TRZY diety — tyle, ile realnie oferuje restauracja. Nie dopisuj
 * kolejnych pozycji bez potwierdzenia w bazie wiedzy hotelu.
 */
const dietCopy: DietCopy[] = [
  {
    id: "cukrzycowa",
    name: { pl: "Dieta cukrzycowa", en: "Diabetic Menu (Low-GI)" },
    description: {
      pl: "Posiłki o kontrolowanej zawartości cukru i węglowodanów, przygotowywane pod nadzorem dietetyka.",
      en: "Controlled carbohydrates and low glycemic index meals supervised by a clinical dietitian.",
    },
  },
  {
    id: "lekkostrawna",
    name: { pl: "Dieta lekkostrawna", en: "Light Digestive Menu" },
    description: {
      pl: "Łagodne dla żołądka posiłki, polecane po zabiegach oraz w okresie rekonwalescencji.",
      en: "Gentle, easily digestible dishes recommended during recovery and post-treatment rest.",
    },
  },
  {
    id: "bezglutenowa-bezmleczna",
    name: {
      pl: "Dieta bezglutenowa i bezmleczna",
      en: "Gluten-Free & Dairy-Free Menu",
    },
    description: {
      pl: "Posiłki bez glutenu i bez mleka, przygotowywane w wydzielonej strefie kuchni z zachowaniem pełnej wartości odżywczej.",
      en: "Gluten-free and dairy-free meals prepared in a dedicated kitchen zone while preserving complete nutritional balance.",
    },
    note: {
      pl: "Zgłoś tę dietę najpóźniej 3 dni przed przyjazdem.",
      en: "Please request this diet at least 3 days before arrival.",
    },
  },
]

export function getDiets(lang: Language): Diet[] {
  return dietCopy.map((diet) => ({
    id: diet.id,
    name: loc(diet.name, lang),
    description: loc(diet.description, lang),
    ...(diet.note ? { note: loc(diet.note, lang) } : {}),
  }))
}

// ---------------------------------------------------------------------------
// Godziny posiłków
// ---------------------------------------------------------------------------

export type MealTime = {
  name: string
  hours: string
}

const mealTimeCopy: Array<{ name: L<string>; hours: L<string> }> = [
  {
    name: { pl: "Śniadanie", en: "Breakfast" },
    hours: { pl: "7:30 – 10:00", en: "7:30 AM – 10:00 AM" },
  },
  {
    name: { pl: "Obiad", en: "Lunch" },
    hours: { pl: "13:00 – 15:00", en: "1:00 PM – 3:00 PM" },
  },
  {
    name: { pl: "Kolacja", en: "Dinner" },
    hours: { pl: "17:30 – 19:30", en: "5:30 PM – 7:30 PM" },
  },
]

export function getMealTimes(lang: Language): MealTime[] {
  return mealTimeCopy.map((meal) => ({
    name: loc(meal.name, lang),
    hours: loc(meal.hours, lang),
  }))
}

// ---------------------------------------------------------------------------
// Udogodnienia dla osób z niepełnosprawnościami
// ---------------------------------------------------------------------------

export type AccessibilityIcon =
  | "door-open"
  | "move-vertical"
  | "car"
  | "hand"
  | "bath"
  | "bus"

type AccessibilityFeatureCopy = {
  icon: AccessibilityIcon
  title: L<string>
  description: L<string>
}

export type AccessibilityFeature = {
  icon: AccessibilityIcon
  title: string
  description: string
}

const accessibilityFeatureCopy: AccessibilityFeatureCopy[] = [
  {
    icon: "door-open",
    title: { pl: "Brak progów w całym obiekcie", en: "100% Step-Free Throughout Resort" },
    description: {
      pl: "Wszystkie pokoje, korytarze i strefy wspólne są wolne od progów i barier architektonicznych.",
      en: "All guestrooms, hallways, and wellness areas are completely free of architectural thresholds.",
    },
  },
  {
    icon: "move-vertical",
    title: { pl: "4 windy z komunikatami głosowymi", en: "4 Voice-Guided Elevators" },
    description: {
      pl: "Windy obsługują wszystkie piętra i informują głosowo o każdym przystanku.",
      en: "Spacious elevators serve every floor with clear auditory floor announcements.",
    },
  },
  {
    icon: "car",
    title: {
      pl: "10 miejsc parkingowych dla osób z niepełnosprawnościami",
      en: "10 Dedicated Accessible Parking Spots",
    },
    description: {
      pl: "Szerokie miejsca parkingowe usytuowane najbliżej wejścia głównego.",
      en: "Extra-wide parking spaces situated immediately adjacent to the main entrance ramp.",
    },
  },
  {
    icon: "hand",
    title: { pl: "Poręcze na całej długości korytarzy", en: "Full-Length Hallway Handrails" },
    description: {
      pl: "Poręcze zamontowane w korytarzach, łazienkach i na basenie termalnym.",
      en: "Continuous sturdy grab rails in corridors, private bathrooms, and pool areas.",
    },
  },
  {
    icon: "bath",
    title: { pl: "Brodziki bez progu i uchwyty w łazienkach", en: "Walk-In Zero-Threshold Showers" },
    description: {
      pl: "Każda łazienka jest przystosowana do potrzeb osób o ograniczonej mobilności.",
      en: "Every bathroom is equipped with ergonomic safety grab bars and fold-down shower seating.",
    },
  },
  {
    icon: "bus",
    title: { pl: "Transport meleksem po terenie ośrodka", en: "Complimentary Electric Resort Shuttle" },
    description: {
      pl: "Bezpłatny meleks dowozi gości między budynkiem głównym, SPA i parkingiem.",
      en: "Dedicated electric cart transfers guests smoothly between main building, spa, and station.",
    },
  },
]

export function getAccessibilityFeatures(lang: Language): AccessibilityFeature[] {
  return accessibilityFeatureCopy.map((feature) => ({
    icon: feature.icon,
    title: loc(feature.title, lang),
    description: loc(feature.description, lang),
  }))
}

// ---------------------------------------------------------------------------
// Kontakt
// ---------------------------------------------------------------------------

const phoneNumber = "+48 18 123 45 67"

export const contactInfo = {
  address: "ul. Zdrojowa 15, 33-380 Krynica-Zdrój",
  phone: phoneNumber,
  // Link tel: wyprowadzony z numeru wyświetlanego — jedno źródło prawdy.
  phoneHref: `tel:+${phoneNumber.replace(/\D/g, "")}`,
  email: "recepcja@bukowydwor.pl",
  receptionHours: "Recepcja: całodobowo, 24 godziny na dobę",
}
