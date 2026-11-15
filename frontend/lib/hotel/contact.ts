// ---------------------------------------------------------------------------
// Contact
// ---------------------------------------------------------------------------

const phoneNumber = "+48 18 123 45 67"
const city = "Krynica-Zdrój"

export const contactInfo = {
  address: `ul. Zdrojowa 15, 33-380 ${city}`,
  /** Town of the resort, also passed to the voice agent as the `location` dynamic variable. */
  city,
  phone: phoneNumber,
  // tel: link derived from the displayed number, a single source of truth.
  phoneHref: `tel:+${phoneNumber.replace(/\D/g, "")}`,
  email: "recepcja@bukowydwor.example",
  receptionHours: "Recepcja: całodobowo, 24 godziny na dobę",
}
