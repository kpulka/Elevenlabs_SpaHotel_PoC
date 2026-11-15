# GDPR documentation package (PoC)

> **Not legal advice.** This package is a technical and organisational working draft written by an engineer for a proof-of-concept. It is not reviewed by a lawyer or a data protection officer. Every legal basis, retention period and transfer statement below must be confirmed by the controller's legal counsel before any live use with real guests.

> **Fictional controller.** The business in these documents is the fictional spa from the PoC. No real company, person or contact is named.

## Documents

| Document | Purpose |
|---|---|
| [ropa.md](ropa.md) | Record of processing activities (Art. 30 template): activities, data categories, purposes, recipients and processors, transfers, retention pointer |
| [dpia-lite.md](dpia-lite.md) | Short data protection impact assessment for special-category health data (Art. 9) processed by the voice agent: risks, mitigations, residual risk, open decisions |
| [retention.md](retention.md) | Retention matrix per data class: what is kept, where, for how long, and how it is deleted |

## Status legend

Every statement uses one of these labels:

| Label | Meaning |
|---|---|
| **In repo** | Verified by reading the code or configuration in this repository. Points to the file. |
| **Platform (verify)** | Depends on the ElevenLabs platform, its plan or its contracts. Not verifiable from this repo. |
| **Design / Enterprise tier** | A feature the platform offers on a higher plan. The live agent runs on the Creator plan (`docs/pl/audyt_agenta_2026-08.md`, section 3), so this is **not active**. |
| **Design (not implemented)** | Proposed control, not in the code. |
| **Open** | A decision the controller has not made. |

## Key facts at a glance

| Topic | Status | Detail |
|---|---|---|
| Phone numbers in JSON logs are masked | In repo | `mock_backend/logs.py` (`mask_phone`), keeps only the last three digits |
| Guest names are kept out of JSON logs | In repo | `mock_backend/logs.py` module docstring |
| Phone numbers in free text are masked in logs | In repo | `redact_phones` in `mock_backend/logs.py` |
| Evaluation transcripts are redacted before they are saved | In repo | `mock_backend/tunnel/transcripts.py` (`save`, `redact_run`) |
| Guest name is sent in clear to the Telegram alert | In repo, **known gap** | `mock_backend/routers/comms.py` (`_tekst_sms_na_telegram`, `guest_name`); masking planned |
| Phone number of the recipient is returned unmasked in one API response | In repo, **known gap** | `mock_backend/routers/comms.py` (`delivered_to`) |
| Bookings are held in process memory | In repo | `mock_backend/config.py` (`db_path` default `:memory:`); a restart clears them |
| SMS is simulated; no SMS provider is connected | In repo | `send_sms_summary` prints the text and optionally relays to Telegram |
| Zero retention mode, PII redaction of transcripts, EU data residency, DPA | **Design / Enterprise tier** | not active on the Creator plan (audit section 3) |
| Privacy page `/polityka` | In repo, **content not reviewed here** | `frontend/app/polityka/`; the footer links to it. This package does not check its text. |
| Consent before a voice session starts | **Open** | no consent step is verified in this package; a design requirement, see `dpia-lite.md` |

## How to use this package

1. Controller reviews `ropa.md` and fills the bracketed items marked `[CONFIRM]`.
2. Counsel reviews the legal basis column in `ropa.md` and the consent text in `dpia-lite.md`.
3. Engineering checks the **In repo** rows against the code before each release.
4. Each **Known gap** has an owner before go-live.

## Related

- Agent-side health rules (flags, not diagnoses): `agent/system_prompt_v3.md` and `agent/verticals/dental_clinic/system_prompt.md`.
- Outbound events and personal data in them: `integrations/n8n/README.md` (GDPR note).
- Telephony design (recording and consent are the main open questions): `docs/telephony.md`.
