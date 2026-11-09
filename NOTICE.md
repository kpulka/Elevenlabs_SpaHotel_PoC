# NOTICE

## What this repository is

This is a **portfolio proof of concept / technical case study**, built by kpulka as part of an
application for the **ElevenLabs Deployment Strategist** role. It demonstrates an end-to-end
voice-agent deployment: a Next.js marketing site with the ElevenLabs Convai widget, a FastAPI
mock backend implementing the agent's tools (availability, booking, SMS summary, handoff),
ElevenLabs workflows/procedures, and a Podman + Cloudflare quick-tunnel local demo setup.
Nothing here is a production system or a deliverable for a paying client.

## The hotel is fictional

"Uzdrowisko Termalne Bukowy Dwór" does **not** exist. The property, its rooms, spa treatments,
prices, phone number, e-mail address, street address, opening hours and the staff members
(or the names used by the agent, e.g. "Anna") are **invented for the demo**. Any resemblance
to a real business is coincidental. Do not treat any data in this repository as a real offer,
quote, or contact channel.

## Assets are AI-generated placeholders

All photography and illustrations in the frontend (`frontend/public/images/`, icons) and in the
presentation (`presentation/assets/`) are **AI-generated placeholder assets**, not photographs of
a real property and not licensed stock imagery of a real venue. The ElevenLabs embed script in
`frontend/public/widget/convai-widget-embed.js` is third-party vendor code, included unmodified
and marked as vendored in `.gitattributes`.

## No personal data

The backend is a **mock**: all state (rooms, appointments, conversations) is kept **in memory**
and disappears on restart. No guest data, no CRM, no telephony records and no real customer
information are stored, processed or transmitted by this repository. The only secrets involved
are the author's own API keys, kept in local `.env` files that are gitignored and never committed.

---

## PL — nota prawna (skrót)

To repozytorium to **portfolio / studium przypadku** przygotowane na potrzeby aplikacji na
stanowisko Deployment Strategist w ElevenLabs — nie jest to wdrożenie produkcyjne ani materiał
dla klienta. „Uzdrowisko Termalne Bukowy Dwór" jest **fikcyjne**: nazwa obiektu, ceny, numer
telefonu, adres, godziny i personel (w tym „Anna") zostały wymyślone na potrzeby demonstracji.
Wszystkie zdjęcia i ilustracje w froncie i prezentacji są **wygenerowane przez AI** jako
placeholdery — nie przedstawiają realnego obiektu. Backend jest atrapą trzymającą stan
**w pamięci**, więc repozytorium nie przetwarza żadnych danych gości ani danych osobowych.
