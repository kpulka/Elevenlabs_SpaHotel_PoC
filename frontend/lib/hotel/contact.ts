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
