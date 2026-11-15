import type { Language } from "../translations"
import { type L, loc } from "../i18n"

// ---------------------------------------------------------------------------
// Diets
// ---------------------------------------------------------------------------

export type Diet = {
  id: string
  name: string
  description: string
  /** Extra practical note (e.g. the deadline for requesting a diet). */
  note?: string
}

type DietCopy = {
  id: string
  name: L<string>
  description: L<string>
  note?: L<string>
}

/**
 * Exactly THREE diets, as many as the restaurant actually offers. Do not add
 * more entries without confirmation in the hotel knowledge base.
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
// Meal times
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
