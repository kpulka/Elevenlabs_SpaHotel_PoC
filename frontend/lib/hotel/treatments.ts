import type { Language } from "../translations"
import { SITE_TREATMENTS } from "../generated/hotel-facts"
import { type L, loc } from "../i18n"

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
      throw new Error(`[hotel/treatments] zabieg "${id}" nie ma ani faktu z backendu, ani czasu lokalnego`)
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
