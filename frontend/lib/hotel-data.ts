import type { Language } from "./translations"

export type Room = {
  id: string
  slug: string
  name: string
  price: number
  capacity: string
  image: string
  description: string
  longDescription: string
  features: string[]
}

export const rooms: Room[] = [
  {
    id: "jednoosobowy",
    slug: "pokoj-jednoosobowy",
    name: "Pokój jednoosobowy",
    price: 350,
    capacity: "1 osoba",
    image: "/images/room-single.png",
    description:
      "Spokojny, słoneczny pokój dla jednej osoby z widokiem na las bukowy. Idealny na dłuższy pobyt sanatoryjny.",
    longDescription:
      "Pokój jednoosobowy o powierzchni 22 m² urządzony w ciepłych, naturalnych barwach. Łóżko z materacem ortopedycznym, wygodny fotel do czytania i biurko. Duże okno zapewnia dużo naturalnego światła i widok na okoliczny las.",
    features: [
      "Łóżko z materacem ortopedycznym",
      "Łazienka z uchwytami i brodzikiem bez progu",
      "Przycisk alarmowy przy łóżku",
      "Balkon lub loggia",
      "Telewizor i radio",
      "Czajnik i zestaw do herbaty",
    ],
  },
  {
    id: "dwuosobowy",
    slug: "pokoj-dwuosobowy",
    name: "Pokój dwuosobowy",
    price: 500,
    capacity: "2 osoby",
    image: "/images/room-double.png",
    description:
      "Przestronny pokój dla dwóch osób z wygodną strefą wypoczynkową i widokiem na góry.",
    longDescription:
      "Pokój dwuosobowy o powierzchni 30 m² z dwoma łóżkami lub łóżkiem małżeńskim do wyboru. Oddzielna strefa wypoczynkowa z fotelami, duża łazienka przystosowana dla osób z ograniczoną mobilnością.",
    features: [
      "Dwa łóżka lub łóżko małżeńskie",
      "Łazienka z uchwytami i brodzikiem bez progu",
      "Przycisk alarmowy przy łóżku",
      "Strefa wypoczynkowa z fotelami",
      "Balkon z widokiem na las",
      "Telewizor, radio, sejf",
    ],
  },
  {
    id: "apartament",
    slug: "apartament",
    name: "Apartament",
    price: 750,
    capacity: "2–3 osoby",
    image: "/images/room-apartment.png",
    description:
      "Apartament z osobnym salonem — najwięcej przestrzeni i komfortu, dla gości z opiekunem lub rodziną.",
    longDescription:
      "Apartament o powierzchni 45 m² z sypialnią oraz osobnym salonem. Dodatkowe miejsce do spania dla osoby towarzyszącej. Duża, w pełni dostępna łazienka oraz prywatny balkon z widokiem na górski krajobraz.",
    features: [
      "Sypialnia + osobny salon",
      "Dodatkowe miejsce do spania",
      "Łazienka w pełni dostępna, prysznic bez progu",
      "Przycisk alarmowy w sypialni i łazience",
      "Prywatny, przestronny balkon",
      "Minibar, sejf, telewizor",
    ],
  },
]

export const roomsEn: Room[] = [
  {
    id: "jednoosobowy",
    slug: "single-room",
    name: "Single Comfort Room",
    price: 350,
    capacity: "1 Guest",
    image: "/images/room-single.png",
    description:
      "Quiet, sunlit room for one guest overlooking the beech forest. Ideal for health resort stays.",
    longDescription:
      "Single room (22 m²) decorated in warm natural tones. Orthopedic mattress, ergonomic reading chair, and desk. Large window with picturesque forest scenery.",
    features: [
      "Orthopedic medical mattress",
      "Walk-in step-free shower with safety grab bars",
      "Bedside emergency call button",
      "Private balcony or loggia",
      "Smart TV & radio",
      "Electric kettle & herbal tea set",
    ],
  },
  {
    id: "dwuosobowy",
    slug: "double-room",
    name: "Double Comfort Room",
    price: 500,
    capacity: "2 Guests",
    image: "/images/room-double.png",
    description:
      "Spacious room for two guests with a comfortable relaxation area and mountain views.",
    longDescription:
      "Double room (30 m²) with twin beds or king-size bed. Separate lounge area with armchairs and fully barrier-free accessible bathroom.",
    features: [
      "Twin beds or king-size bed",
      "Walk-in step-free shower with grab bars",
      "Emergency call buttons in bedroom & bathroom",
      "Lounge seating area with armchairs",
      "Balcony with panoramic forest view",
      "TV, digital radio, safe",
    ],
  },
  {
    id: "apartament",
    slug: "apartment-suite",
    name: "Executive Health Suite",
    price: 750,
    capacity: "2–3 Guests",
    image: "/images/room-apartment.png",
    description:
      "Suite with separate living room — maximum comfort and space for guests with family or caregiver.",
    longDescription:
      "Luxury apartment (45 m²) featuring a master bedroom and separate living room. Extra sofa bed, premium accessible bathroom, and wide private terrace.",
    features: [
      "Master bedroom + separate living room",
      "Extra sleeping accommodation for companion",
      "100% barrier-free bathroom with level-entry shower",
      "Emergency call buttons in bedroom & bathroom",
      "Private spacious scenic balcony",
      "Minibar, safe, 4K TV",
    ],
  },
]

export type Treatment = {
  id: string
  category: "Baseny termalne" | "Zabiegi balneologiczne" | "Masaże i fizykoterapia" | "Thermal Pools" | "Balneological Treatments" | "Massage & Physiotherapy"
  name: string
  duration: string
  price: number
  description: string
  image?: string
}

export const treatments: Treatment[] = [
  {
    id: "basen-32",
    category: "Baseny termalne",
    name: "Basen termalny 32°C",
    duration: "bez limitu w godzinach otwarcia",
    price: 0,
    image: "/images/spa-pool.png",
    description:
      "Basen relaksacyjny o łagodnej temperaturze, dostępny dla wszystkich gości hotelowych bez dodatkowych opłat.",
  },
  {
    id: "basen-34",
    category: "Baseny termalne",
    name: "Basen termalny 34°C",
    duration: "bez limitu w godzinach otwarcia",
    price: 0,
    image: "/images/hero-pool.png",
    description:
      "Cieplejszy basen o właściwościach rozluźniających mięśnie, polecany szczególnie przy dolegliwościach reumatycznych.",
  },
  {
    id: "kapiel-siarczkowa",
    category: "Zabiegi balneologiczne",
    name: "Kąpiel siarczkowa",
    duration: "20 min",
    price: 65,
    image: "/images/treatment-sulphur-bath.png",
    description:
      "Kąpiel w wodzie siarczkowej wspomagająca leczenie chorób stawów i skóry, wykonywana pod nadzorem personelu medycznego.",
  },
  {
    id: "kapiel-borowinowa",
    category: "Zabiegi balneologiczne",
    name: "Kąpiel borowinowa",
    duration: "20 min",
    price: 70,
    image: "/images/treatment-mud-bath.png",
    description:
      "Zabieg z użyciem naturalnego torfu leczniczego, łagodzący bóle stawów i wspomagający krążenie.",
  },
  {
    id: "jonoforeza",
    category: "Zabiegi balneologiczne",
    name: "Jonoforeza",
    duration: "15 min",
    price: 45,
    image: "/images/treatment-electrotherapy.png",
    description:
      "Zabieg fizykoterapeutyczny wykorzystujący prąd stały do wprowadzania leków przeciwbólowych przez skórę.",
  },
  {
    id: "masaz-leczniczy",
    category: "Masaże i fizykoterapia",
    name: "Masaż leczniczy",
    duration: "30 min",
    price: 90,
    image: "/images/treatment-massage.png",
    description:
      "Masaż wykonywany przez wykwalifikowanego fizjoterapeutę, dopasowany indywidualnie do stanu zdrowia gościa.",
  },
  {
    id: "gimnastyka-lecznicza",
    category: "Masaże i fizykoterapia",
    name: "Gimnastyka lecznicza (grupowa)",
    duration: "45 min",
    price: 30,
    image: "/images/treatment-gymnastics.png",
    description:
      "Zajęcia ruchowe prowadzone przez fizjoterapeutę, dostosowane do możliwości seniorów.",
  },
]

export const treatmentsEn: Treatment[] = [
  {
    id: "basen-32",
    category: "Thermal Pools",
    name: "Thermal Relaxation Pool 32°C",
    duration: "Unlimited during opening hours",
    price: 0,
    image: "/images/spa-pool.png",
    description:
      "Gentle mineral relaxation pool, open to all resort guests at no extra charge.",
  },
  {
    id: "basen-34",
    category: "Thermal Pools",
    name: "Thermal Hydrotherapy Pool 34°C",
    duration: "Unlimited during opening hours",
    price: 0,
    image: "/images/hero-pool.png",
    description:
      "Warm mineral hydrotherapy pool with muscle-relaxing jets, recommended for rheumatic relief.",
  },
  {
    id: "kapiel-siarczkowa",
    category: "Balneological Treatments",
    name: "Mineral Sulphur Bath",
    duration: "20 min",
    price: 65,
    image: "/images/treatment-sulphur-bath.png",
    description:
      "Natural thermal sulphur bath aiding in joint, spine, and skin rehabilitation under medical oversight.",
  },
  {
    id: "kapiel-borowinowa",
    category: "Balneological Treatments",
    name: "Therapeutic Peat Mud Bath",
    duration: "20 min",
    price: 70,
    image: "/images/treatment-mud-bath.png",
    description:
      "Natural medical peat mud wrap, relieving deep joint pain and boosting circulation.",
  },
  {
    id: "jonoforeza",
    category: "Balneological Treatments",
    name: "Iontophoresis Electrotherapy",
    duration: "15 min",
    price: 45,
    image: "/images/treatment-electrotherapy.png",
    description:
      "Physiotherapy treatment using direct electrical current to deliver anti-inflammatory analgesics through skin.",
  },
  {
    id: "masaz-leczniczy",
    category: "Massage & Physiotherapy",
    name: "Therapeutic Back Massage",
    duration: "30 min",
    price: 90,
    image: "/images/treatment-massage.png",
    description:
      "Customized back and spine massage delivered by certified medical physiotherapists.",
  },
  {
    id: "gimnastyka-lecznicza",
    category: "Massage & Physiotherapy",
    name: "Therapeutic Group Gymnastics",
    duration: "45 min",
    price: 30,
    image: "/images/treatment-gymnastics.png",
    description:
      "Low-impact mobility gymnastics led by a senior physiotherapist.",
  },
]

export type Diet = {
  id: string
  name: string
  description: string
}

export const diets: Diet[] = [
  {
    id: "cukrzycowa",
    name: "Dieta cukrzycowa",
    description:
      "Posiłki o kontrolowanej zawartości cukru i węglowodanów, przygotowywane pod nadzorem dietetyka.",
  },
  {
    id: "lekkostrawna",
    name: "Dieta lekkostrawna",
    description:
      "Łagodne dla żołądka posiłki, polecane po zabiegach oraz w okresie rekonwalescencji.",
  },
  {
    id: "bezglutenowa",
    name: "Dieta bezglutenowa",
    description:
      "Posiłki przygotowywane bez produktów zawierających gluten, z zachowaniem pełnej wartości odżywczej.",
  },
]

export const dietsEn: Diet[] = [
  {
    id: "cukrzycowa",
    name: "Diabetic Menu (Low-GI)",
    description:
      "Controlled carbohydrates and low glycemic index meals supervised by a clinical dietitian.",
  },
  {
    id: "lekkostrawna",
    name: "Light Digestive Menu",
    description:
      "Gentle, easily digestible dishes recommended during recovery and post-treatment rest.",
  },
  {
    id: "bezglutenowa",
    name: "Gluten-Free Menu",
    description:
      "Meals prepared in dedicated allergen-safe environment preserving complete nutritional balance.",
  },
]

export const mealTimes = [
  { name: "Śniadanie", hours: "7:30 – 9:30" },
  { name: "Obiad", hours: "13:00 – 15:00" },
  { name: "Kolacja", hours: "18:00 – 19:30" },
]

export const mealTimesEn = [
  { name: "Breakfast", hours: "7:30 AM – 9:30 AM" },
  { name: "Lunch", hours: "1:00 PM – 3:00 PM" },
  { name: "Dinner", hours: "6:00 PM – 7:30 PM" },
]

export function getRooms(lang: Language) {
  return lang === "en" ? roomsEn : rooms
}

export function getTreatments(lang: Language) {
  return lang === "en" ? treatmentsEn : treatments
}

export function getDiets(lang: Language) {
  return lang === "en" ? dietsEn : diets
}

export function getMealTimes(lang: Language) {
  return lang === "en" ? mealTimesEn : mealTimes
}

export const accessibilityFeatures = [
  {
    icon: "door-open" as const,
    title: "Brak progów w całym obiekcie",
    description: "Wszystkie pokoje, korytarze i strefy wspólne są wolne od progów i barier architektonicznych.",
  },
  {
    icon: "move-vertical" as const,
    title: "4 windy z komunikatami głosowymi",
    description: "Windy obsługują wszystkie piętra i informują głosowo o każdym przystanku.",
  },
  {
    icon: "car" as const,
    title: "10 miejsc parkingowych dla osób z niepełnosprawnościami",
    description: "Szerokie miejsca parkingowe usytuowane najbliżej wejścia głównego.",
  },
  {
    icon: "hand" as const,
    title: "Poręcze na całej długości korytarzy",
    description: "Poręcze zamontowane w korytarzach, łazienkach i na basenie termalnym.",
  },
  {
    icon: "bath" as const,
    title: "Brodziki bez progu i uchwyty w łazienkach",
    description: "Każda łazienka jest przystosowana do potrzeb osób o ograniczonej mobilności.",
  },
  {
    icon: "bus" as const,
    title: "Transport meleksem po terenie ośrodka",
    description: "Bezpłatny meleks dowozi gości między budynkiem głównym, SPA i parkingiem.",
  },
]

export const accessibilityFeaturesEn = [
  {
    icon: "door-open" as const,
    title: "100% Step-Free Throughout Resort",
    description: "All guestrooms, hallways, and wellness areas are completely free of architectural thresholds.",
  },
  {
    icon: "move-vertical" as const,
    title: "4 Voice-Guided Elevators",
    description: "Spacious elevators serve every floor with clear auditory floor announcements.",
  },
  {
    icon: "car" as const,
    title: "10 Dedicated Accessible Parking Spots",
    description: "Extra-wide parking spaces situated immediately adjacent to the main entrance ramp.",
  },
  {
    icon: "hand" as const,
    title: "Full-Length Hallway Handrails",
    description: "Continuous sturdy grab rails in corridors, private bathrooms, and pool areas.",
  },
  {
    icon: "bath" as const,
    title: "Walk-In Zero-Threshold Showers",
    description: "Every bathroom is equipped with ergonomic safety grab bars and fold-down shower seating.",
  },
  {
    icon: "bus" as const,
    title: "Complimentary Electric Resort Shuttle",
    description: "Dedicated electric cart transfers guests smoothly between main building, spa, and station.",
  },
]

export function getAccessibilityFeatures(lang: Language) {
  return lang === "en" ? accessibilityFeaturesEn : accessibilityFeatures
}

const phoneNumber = "+48 18 123 45 67"

export const contactInfo = {
  address: "ul. Zdrojowa 15, 33-380 Krynica-Zdrój",
  phone: phoneNumber,
  // Link tel: wyprowadzony z numeru wyświetlanego — jedno źródło prawdy.
  phoneHref: `tel:+${phoneNumber.replace(/\D/g, "")}`,
  email: "recepcja@bukowydwor.pl",
  receptionHours: "Recepcja: całodobowo, 24 godziny na dobę",
}
