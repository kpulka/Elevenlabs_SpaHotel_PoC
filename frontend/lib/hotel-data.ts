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
    id: 'jednoosobowy',
    slug: 'pokoj-jednoosobowy',
    name: 'Pokój jednoosobowy',
    price: 350,
    capacity: '1 osoba',
    image: '/images/room-single.png',
    description:
      'Spokojny, słoneczny pokój dla jednej osoby z widokiem na las bukowy. Idealny na dłuższy pobyt sanatoryjny.',
    longDescription:
      'Pokój jednoosobowy o powierzchni 22 m² urządzony w ciepłych, naturalnych barwach. Łóżko z materacem ortopedycznym, wygodny fotel do czytania i biurko. Duże okno zapewnia dużo naturalnego światła i widok na okoliczny las.',
    features: [
      'Łóżko z materacem ortopedycznym',
      'Łazienka z uchwytami i brodzikiem bez progu',
      'Przycisk alarmowy przy łóżku',
      'Balkon lub loggia',
      'Telewizor i radio',
      'Czajnik i zestaw do herbaty',
    ],
  },
  {
    id: 'dwuosobowy',
    slug: 'pokoj-dwuosobowy',
    name: 'Pokój dwuosobowy',
    price: 500,
    capacity: '2 osoby',
    image: '/images/room-double.png',
    description:
      'Przestronny pokój dla dwóch osób z wygodną strefą wypoczynkową i widokiem na góry.',
    longDescription:
      'Pokój dwuosobowy o powierzchni 30 m² z dwoma łóżkami lub łóżkiem małżeńskim do wyboru. Oddzielna strefa wypoczynkowa z fotelami, duża łazienka przystosowana dla osób z ograniczoną mobilnością.',
    features: [
      'Dwa łóżka lub łóżko małżeńskie',
      'Łazienka z uchwytami i brodzikiem bez progu',
      'Przycisk alarmowy przy łóżku',
      'Strefa wypoczynkowa z fotelami',
      'Balkon z widokiem na las',
      'Telewizor, radio, sejf',
    ],
  },
  {
    id: 'apartament',
    slug: 'apartament',
    name: 'Apartament',
    price: 750,
    capacity: '2–3 osoby',
    image: '/images/room-apartment.png',
    description:
      'Apartament z osobnym salonem — najwięcej przestrzeni i komfortu, dla gości z opiekunem lub rodziną.',
    longDescription:
      'Apartament o powierzchni 45 m² z sypialnią oraz osobnym salonem. Dodatkowe miejsce do spania dla osoby towarzyszącej. Duża, w pełni dostępna łazienka oraz prywatny balkon z widokiem na górski krajobraz.',
    features: [
      'Sypialnia + osobny salon',
      'Dodatkowe miejsce do spania',
      'Łazienka w pełni dostępna, prysznic bez progu',
      'Przycisk alarmowy w sypialni i łazience',
      'Prywatny, przestronny balkon',
      'Minibar, sejf, telewizor',
    ],
  },
]

export type Treatment = {
  id: string
  category: 'Baseny termalne' | 'Zabiegi balneologiczne' | 'Masaże i fizykoterapia'
  name: string
  duration: string
  price: number
  description: string
  image?: string
}

export const treatments: Treatment[] = [
  {
    id: 'basen-32',
    category: 'Baseny termalne',
    name: 'Basen termalny 32°C',
    duration: 'bez limitu w godzinach otwarcia',
    price: 0,
    image: '/images/spa-pool.png',
    description:
      'Basen relaksacyjny o łagodnej temperaturze, dostępny dla wszystkich gości hotelowych bez dodatkowych opłat.',
  },
  {
    id: 'basen-34',
    category: 'Baseny termalne',
    name: 'Basen termalny 34°C',
    duration: 'bez limitu w godzinach otwarcia',
    price: 0,
    image: '/images/hero-pool.png',
    description:
      'Cieplejszy basen o właściwościach rozluźniających mięśnie, polecany szczególnie przy dolegliwościach reumatycznych.',
  },
  {
    id: 'kapiel-siarczkowa',
    category: 'Zabiegi balneologiczne',
    name: 'Kąpiel siarczkowa',
    duration: '20 min',
    price: 65,
    image: '/images/treatment-sulphur-bath.png',
    description:
      'Kąpiel w wodzie siarczkowej wspomagająca leczenie chorób stawów i skóry, wykonywana pod nadzorem personelu medycznego.',
  },
  {
    id: 'kapiel-borowinowa',
    category: 'Zabiegi balneologiczne',
    name: 'Kąpiel borowinowa',
    duration: '20 min',
    price: 70,
    image: '/images/treatment-mud-bath.png',
    description:
      'Zabieg z użyciem naturalnego torfu leczniczego, łagodzący bóle stawów i wspomagający krążenie.',
  },
  {
    id: 'jonoforeza',
    category: 'Zabiegi balneologiczne',
    name: 'Jonoforeza',
    duration: '15 min',
    price: 45,
    image: '/images/treatment-electrotherapy.png',
    description:
      'Zabieg fizykoterapeutyczny wykorzystujący prąd stały do wprowadzania leków przeciwbólowych przez skórę.',
  },
  {
    id: 'masaz-leczniczy',
    category: 'Masaże i fizykoterapia',
    name: 'Masaż leczniczy',
    duration: '30 min',
    price: 90,
    image: '/images/treatment-massage.png',
    description:
      'Masaż wykonywany przez wykwalifikowanego fizjoterapeutę, dopasowany indywidualnie do stanu zdrowia gościa.',
  },
  {
    id: 'gimnastyka-lecznicza',
    category: 'Masaże i fizykoterapia',
    name: 'Gimnastyka lecznicza (grupowa)',
    duration: '45 min',
    price: 30,
    image: '/images/treatment-gymnastics.png',
    description:
      'Zajęcia ruchowe prowadzone przez fizjoterapeutę, dostosowane do możliwości seniorów.',
  },
]

export type Diet = {
  id: string
  name: string
  description: string
}

export const diets: Diet[] = [
  {
    id: 'cukrzycowa',
    name: 'Dieta cukrzycowa',
    description:
      'Posiłki o kontrolowanej zawartości cukru i węglowodanów, przygotowywane pod nadzorem dietetyka.',
  },
  {
    id: 'lekkostrawna',
    name: 'Dieta lekkostrawna',
    description:
      'Łagodne dla żołądka posiłki, polecane po zabiegach oraz w okresie rekonwalescencji.',
  },
  {
    id: 'bezglutenowa',
    name: 'Dieta bezglutenowa',
    description:
      'Posiłki przygotowywane bez produktów zawierających gluten, z zachowaniem pełnej wartości odżywczej.',
  },
]

export const mealTimes = [
  { name: 'Śniadanie', hours: '7:30 – 9:30' },
  { name: 'Obiad', hours: '13:00 – 15:00' },
  { name: 'Kolacja', hours: '18:00 – 19:30' },
]

export const accessibilityFeatures = [
  {
    icon: 'door-open' as const,
    title: 'Brak progów w całym obiekcie',
    description: 'Wszystkie pokoje, korytarze i strefy wspólne są wolne od progów i barier architektonicznych.',
  },
  {
    icon: 'move-vertical' as const,
    title: '4 windy z komunikatami głosowymi',
    description: 'Windy obsługują wszystkie piętra i informują głosowo o każdym przystanku.',
  },
  {
    icon: 'car' as const,
    title: '10 miejsc parkingowych dla osób z niepełnosprawnościami',
    description: 'Szerokie miejsca parkingowe usytuowane najbliżej wejścia głównego.',
  },
  {
    icon: 'hand' as const,
    title: 'Poręcze na całej długości korytarzy',
    description: 'Poręcze zamontowane w korytarzach, łazienkach i na basenie termalnym.',
  },
  {
    icon: 'bath' as const,
    title: 'Brodziki bez progu i uchwyty w łazienkach',
    description: 'Każda łazienka jest przystosowana do potrzeb osób o ograniczonej mobilności.',
  },
  {
    icon: 'bus' as const,
    title: 'Transport meleksem po terenie ośrodka',
    description: 'Bezpłatny meleks dowozi gości między budynkiem głównym, SPA i parkingiem.',
  },
]

export const contactInfo = {
  address: 'ul. Zdrojowa 15, 33-380 Krynica-Zdrój',
  phone: '+48 18 123 45 67',
  phoneHref: 'tel:+48181234567',
  email: 'recepcja@bukowydwor.pl',
  receptionHours: 'Recepcja: całodobowo, 24 godziny na dobę',
}
