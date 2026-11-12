import type { Language } from "../translations"
import { type L, loc } from "../i18n"

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
