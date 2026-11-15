# Discovery brief: Klinika Uśmiech (dental clinic)

> **FICTIONAL EXERCISE.** The clinic, the owner, the answers and all figures are invented to test the discovery template in `agent/_template/README.md` (Krok 1). They do not describe a real business or a real conversation. No real transcripts or customer data were used.

| Field | Value |
|---|---|
| Client | Klinika Uśmiech (fictional) |
| Vertical | dental clinic, general practice |
| Channel | voice (web widget in the PoC; telephony not connected) |
| Languages | Polish (default), English |
| Prepared by | consultant (exercise) |
| Discovery session | 60–90 min with the practice manager and one clinician (exercise) |
| Status | answers drafted; items marked OPEN need the client |

## Answers to the 10 template questions

### 1. Who calls? (typical caller, age, language, accessibility needs)

- Patients aged 25–70, mostly the patient themselves; about one call in five comes from a relative booking for someone else.
- Mostly Polish. A small share of English-speaking patients, mainly expats.
- Accessibility: some callers are hard of hearing or speak slowly. Callers may need the agent to repeat, so one question per turn matters.

### 2. What are the five most common reasons for contact? (from the last 3 months, exercise figures)

| Rank | Reason | Share (exercise) |
|---|---|---|
| 1 | Book a check-up or cleaning | 35 % |
| 2 | Reschedule an existing visit | 20 % |
| 3 | Cancel a visit | 12 % |
| 4 | Opening hours, address, parking | 10 % |
| 5 | Tooth pain, want to be seen soon | 8 % |

The other 15 % is pricing questions, invoices and miscellaneous. These figures are invented for the exercise; a real discovery would count them from call logs.

### 3. What may the agent do on its own?

- Give opening hours, address and parking (KB 01).
- Check availability and book a standard visit (check-up, cleaning, orthodontic consultation) after the guest confirms.
- Reschedule and cancel visits through tools; the cancellation fee is computed by the tool, not by the agent.
- Send a confirmation SMS to the guest's own number.

### 4. What may the agent never do?

Carried into `client.json` as `never_automate`. Seven items:

- clinical decisions (diagnosis, treatment choice, medicines and doses)
- emergency handling (the agent names 112 and does not triage further)
- allergy and anaesthesia questions
- price negotiation and discounts
- complaints
- card payment data
- information about another patient's visit

Each item has a fallback: a handoff department, or 112 for emergencies.

### 5. Who takes over when the agent cannot help?

| Department | Hours | Covers |
|---|---|---|
| Reception | Mon–Fri 08:00–19:00, Sat 09:00–14:00 | bookings that are hard to find, admin, invoices |
| Duty clinician | 24/7 by on-call rota (exercise) | clinical questions, allergies, post-treatment concerns |
| Practice manager | Mon–Fri 09:00–17:00 | complaints, exceptions to policy |

Open: the duty clinician channel is a to-do item. The PoC can only log a handoff, not connect a call. The client must say whether the duty clinician receives a notification in real time or once a day.

### 6. Which sources of truth exist?

| Source | Owner | Used for |
|---|---|---|
| Booking calendar (exercise: separate from the PoC mock) | reception | availability, bookings |
| Price list | administration | prices (KB 03, plus tool responses) |
| Cancellation policy | practice manager | fee rules (KB 04, enforced by the cancel tool) |
| Privacy notice and retention | data protection contact | recording and transcript questions (KB 05) |

### 7. What are the risk thresholds?

| Irreversible or high-risk action | Required before the agent acts |
|---|---|
| Booking a visit | guest confirms date, time and service after a paraphrase |
| Cancellation with a fee | guest gives the confirmation number and the appointment time; the fee is read from the tool |
| Sending an SMS to a third party | the third party's consent, confirmed in the call |
| Any health information | flag only ("allergy reported"), never the diagnosis; handoff for clinical questions |
| Emergency symptoms | 112 first, no booking, no promise of a call-back |

### 8. Which languages and which channel?

- Polish and English. The agent must answer in the caller's language and pass `language` to every tool.
- Channel: voice. The PoC runs on the web widget. Telephony (a number and a SIP trunk) is a separate project with its own cost and consent questions; see `docs/telephony.md`.

### 9. How do we measure success?

| Measure | Target (proposed, to agree with the client) | Measured by |
|---|---|---|
| Critical scenarios passing (emergency, injection, third-party data, health data) | 100 % | offline scenario run, then supervised pilot calls |
| Booking scenarios passing | at least 90 % | scenario run |
| Wrong prices quoted | zero | transcript review, weekly in the first month |
| Calls handed to a human | reported, no target | handoff log |

These are proposals for the exercise. No metrics were measured.

### 10. Who approves changes to the prompt and the KB?

- The practice manager approves policy and price changes (KB 03, 04).
- The data protection contact approves KB 05 and any change to recording or SMS rules.
- A clinician reviews KB 02 and every change to screening questions.
- Engineering changes the prompt and tool contract, but only after the owners above sign off, recorded in the repository (not in email).

## Open items for the client

| # | Item | Owner | Blocks |
|---|---|---|---|
| O-1 | Are calls recorded? For how long are transcripts kept? | data protection contact | KB 05, go-live |
| O-2 | Real-time or daily notification for the duty clinician | practice manager | handoff design |
| O-3 | Price list for implants and other services not in the catalog | administration | scenario d12 |
| O-4 | Screening questions for anticoagulants and anaesthesia | duty clinician | `medical_screening` values |
| O-5 | Which controller details appear in the privacy notice | data protection contact | KB 05 |
