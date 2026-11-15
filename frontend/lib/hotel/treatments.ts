import type { Language } from "../translations"
import { SITE_TREATMENTS } from "../generated/hotel-facts"
import { type L, loc } from "../i18n"

// ---------------------------------------------------------------------------
// Treatments
// Ids, prices and durations come from mock_backend/data/spa_schedule.json
// (via lib/generated/hotel-facts.ts). This file holds PL/EN copy only, plus
// two local entries: the pools are pool-area amenities (included in the stay,
// no booking), not treatments from the voice catalogue.
// ---------------------------------------------------------------------------

/** Category key; the PL/EN labels live in translations.spaPage.category*. */
export type TreatmentCategory = "thermal" | "balneo" | "physio"

type SiteTreatmentId = (typeof SITE_TREATMENTS)[number]["id"]

/** Local-only entries: absent from the backend catalogue, so they cannot be booked. */
type LocalTreatmentId = "basen-32" | "basen-34"

export type TreatmentId = SiteTreatmentId | LocalTreatmentId

type TreatmentCopy = {
  category: TreatmentCategory
  name: L<string>
  description: L<string>
  image?: string
  /** Pools: admission included in the stay, no booking and no time limit. */
  includedInStay?: boolean
  /** Duration of a local entry; backend treatments take it from durationMin. */
  durationNote?: L<string>
}

/**
 * `Record<TreatmentId, TreatmentCopy>` enforces complete copy for every
 * id in the backend catalogue: a missing entry is a compile error,
 * not an empty label on the page. Key order = display order.
 * Prices and durations are NOT written here; they come from the generated data.
 */
const treatmentCopy: Record<TreatmentId, TreatmentCopy> = {
  "basen-32": {
    category: "thermal",
    name: { pl: "Basen termalny 32°C", en: "Thermal Relaxation Pool 32°C" },
    includedInStay: true,
    durationNote: { pl: "bez limitu w godzinach otwarcia", en: "Unlimited during opening hours" },
    image: "/images/spa-pool.webp",
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
    image: "/images/hero-pool.webp",
    description: {
      pl: "Cieplejszy basen solankowy o właściwościach rozluźniających mięśnie, polecany szczególnie przy dolegliwościach reumatycznych.",
      en: "Warmer brine pool with muscle-relaxing properties, recommended especially for rheumatic complaints.",
    },
  },
  "kapiel-siarczkowa": {
    category: "balneo",
    name: { pl: "Kąpiel siarczkowa „Ukojenie Stawów”", en: "Sulphur Bath “Joint Relief”" },
    image: "/images/treatment-sulphur-bath.webp",
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
    image: "/images/treatment-massage.webp",
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
    image: "/images/treatment-mud-bath.webp",
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
    image: "/images/treatment-electrotherapy.webp",
    description: {
      pl: "Zabieg elektroleczniczy wprowadzający leki przeciwbólowe przez skórę prądem stałym — stosowany w bólach kręgosłupa i stawów.",
      en: "Electrotherapy treatment introducing pain-relieving medication through the skin with direct current — used for spinal and joint pain.",
    },
  },
  "masaz-klasyczny": {
    category: "physio",
    name: { pl: "Masaż klasyczny relaksacyjny", en: "Classic Relaxation Massage" },
    image: "/images/treatment-massage.webp",
    description: {
      pl: "Masaż całego ciała w spokojnym, relaksacyjnym tempie — poprawia krążenie, rozluźnia napięcie mięśniowe i dopełnia pobyt sanatoryjny.",
      en: "Full-body massage at a calm, relaxing pace — improves circulation, releases muscle tension, and complements your health-resort stay.",
    },
  },
  "gimnastyka-lecznicza": {
    category: "physio",
    name: { pl: "Gimnastyka lecznicza (grupowa)", en: "Therapeutic Group Gymnastics" },
    image: "/images/treatment-gymnastics.webp",
    description: {
      pl: "Zajęcia grupowe z fizjoterapeutą, dostosowane do możliwości seniorów — poprawiają ruchomość stawów i bezpieczeństwo codziennych czynności.",
      en: "Group sessions led by a physiotherapist and adapted to seniors’ abilities — improve joint mobility and everyday safety.",
    },
  },
}

/** Backend facts by id: price and duration are never typed in by hand. */
const treatmentFacts = new Map<string, (typeof SITE_TREATMENTS)[number]>(
  SITE_TREATMENTS.map((fact) => [fact.id, fact])
)

/** Display order: pools (area) -> treatments in backend catalogue order. */
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
      throw new Error(`[hotel/treatments] treatment "${id}" has neither a backend fact nor a local duration`)
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
