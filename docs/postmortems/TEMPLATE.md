# Postmortem: <short title that names the symptom>

| Field | Value |
|---|---|
| Status | draft / reviewed / closed |
| Severity | SEV1 (guests harmed or wrong safety info) · SEV2 (wrong business info or a broken path) · SEV3 (no guest impact, internal) |
| Environment | production / PoC / test |
| Detected | date and how it was found (monitoring, test call, guest, reviewer) |
| Duration | from first wrong behaviour to fix, if known |
| Author(s) | role names, not personal data |
| Source | links to commits, logs or tickets |

Rules for writing one:

- **Blameless.** Describe what the system allowed, not who should have known better.
- **Facts first.** Mark every time or number you cannot verify as `unknown`. Do not reconstruct a timeline from memory and present it as a log.
- **Separate what the code does from what the docs say.** If a documented procedure differs from the code, write both.
- **No guest data.** Mask names, phone numbers and transcripts. Quote only the agent's words needed to show the failure.

## 1. Summary

Two to four sentences: what the user or guest saw, how long, and how it was fixed.

## 2. Impact

| Area | Impact |
|---|---|
| Guests or callers | number, or `unknown` |
| Business | wrong prices, bookings, refunds, or none |
| Safety | any health or emergency information affected |
| Data | any personal data exposed or retained longer than intended |

## 3. Timeline

Ordinal steps are fine when timestamps were not recorded. Use times (UTC) when they are.

| # | Time (UTC) or order | Event | Source |
|---|---|---|---|
| 1 | | | |
| 2 | | | |

## 4. Root cause

- **Direct cause:** the immediate failure.
- **Underlying cause:** the condition that let it happen (process, interface, missing check).
- **Contributing factors:** anything that made it worse or harder to notice.

Use the "five whys" only if it leads to a process or design fact, not a person.

## 5. Detection

- How was it detected, and how long after the change?
- What signal was misleading (for example a success status code)?
- What would have detected it earlier?

## 6. Fix

- What changed now (commit, configuration, data).
- What is still manual.
- What was verified after the fix, and how. A passing deploy is not verification; read the state back.

## 7. Prevention and follow-ups

| # | Action | Type (detect / prevent / mitigate) | Owner (role) | Status |
|---|---|---|---|---|
| 1 | | | | open |

Status values: `done` (in the repository, with a link), `open`, `design only`. Do not mark an item `done` unless a test, script or check exists.

## 8. What went well

Short list. Keep it honest; it is not a place for praise.
