# KB outline: Klinika Uśmiech (FIKCYJNA)

> Status: **outline only, fictional exercise.** No KB file is written for this vertical yet. The outline fixes which facts go where and which `usage_mode` each document gets. It matches `client.json` (`kb_documents`).

| Nr | Document | Contents | `usage_mode` | Owner (role) |
|---|---|---|---|---|
| 01 | `01_informacje_ogolne` | address (placeholder), opening hours, parking, accessibility, how to reach the clinic | `auto` (RAG) | recepcja |
| 02 | `02_uslugi_i_wskazania` | services with duration, what happens at each visit, screening questions (allergies, medicines), notes for the agent | `auto` (RAG) | lekarz koordynator |
| 03 | `03_cennik_i_platnosci` | price list, payment methods (no card data in the call), what is included | `prompt` (full context) | administracja |
| 04 | `04_polityka_odwolan` | cancellation and reschedule windows, fee rules (the backend computes the fee), late arrivals | `prompt` (full context) | kierownik |
| 05 | `05_prywatnosc_i_procedury` | recording and transcript notice (to be confirmed by the client), data kept and for how long, SMS to third parties (consent), when to pass to a human | `prompt` (full context) | inspektor ochrony danych klienta |

## Rules

1. **One fact, one place.** Prices live in 03 or in a tool response, not in the prompt.
2. **Pricing and policy are `prompt`.** A wrong fee is expensive, so these documents are always in context.
3. **No medical advice.** 02 describes services and screening questions only. Clinical content needs a named owner and a review date.
4. **Unknowns are written down.** Anything the client has not confirmed (recording retention, controller details, address) is marked `TODO-CONFIRM` in the document. The agent is told to hand such questions to reception (prompt guardrail 5).
5. **Parity.** `.md` source and `.txt` deployed copy must match, as in the PoC (`scripts/check_kb_parity.py` adaptation).

## Open items before go-live

- [ ] Recording and transcript retention confirmed by the client (05).
- [ ] Controller and processor list confirmed (05, plus `docs/gdpr/ropa.md` as the model).
- [ ] Price list signed off by the owner (03).
- [ ] Screening questions reviewed by a clinician (02).
