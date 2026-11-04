# UX Design: Virtual Receptionist Anna

Two channels, two user experiences. This document covers both.

> Note on language: the agent speaks Polish with guests in production. Dialogue examples below are shown in English for readability; the Polish wording is maintained in the agent configuration (`agent/system_prompt.md`).

---

## Channel 1: Telephone (SIP / hotel phone line)

This channel has no user interface. The UX is the conversation design itself.

---

### User Journey Map: Telephone

#### Phase 0: Before the call

| Stage | What the guest does | Emotional state | Touchpoint |
|---|---|---|---|
| Deciding to call | Looks for the number in a brochure or on the card by the room phone | Neutral, slightly unsure of technology | Hotel number on printed material |
| Dialling | Calls reception | Waiting: will someone answer? | Ringing tone |

**UX risk:** if the guest waits longer than four rings, they hang up. Anna must answer immediately.

---

#### Phase 1: First seconds (critical)

| Stage | Anna says | UX goal | What to avoid |
|---|---|---|---|
| Answering | "Good day, this is Anna at Bukowy Dwór reception. How may I help you?" | Warm greeting, clear identity | Long introductions, reading out opening hours, IVR-style tone |
| Identifying the need | Listens. Does not interrupt. | The guest must feel heard | Asking a follow-up before the guest has finished |

**Technical parameters that deliver this experience:**
- `turn_timeout: 3.0s`: Anna waits three seconds of silence before responding.
- `turn_eagerness: Patient`: does not talk over natural pauses.
- `first_message` is delivered calmly, at `speed: 0.85x`.

---

#### Phase 2: Service (happy path: treatment booking)

```
Guest:  "I would like to book a massage."
          |
Anna:   "Certainly. Which kind of massage are you interested in?"          <- one question
          |
Guest:  "The... for my back."
          |
Anna:   "I understand, a therapeutic back massage. Which day?"             <- paraphrase + one question
          |
Guest:  [2-second pause] "Well... maybe Wednesday."
          |                  ^
          |                  turn_timeout: 3s; Anna waits and does not interrupt
Anna:   [calls tool] "Let me check... I have 10:00, 2:30 PM and 3:00 PM. Which time?"
          |
Guest:  "2:30."
          |
Anna:   "May I have your name?"
          |
Guest:  "Kowalski, Jan."
          |
Anna:   "Thank you. I am booking a therapeutic back massage
         for Wednesday 27 August at 2:30 PM for Mr. Jan Kowalski.
         Is that correct?"                                                   <- paraphrase before confirming
          |
Guest:  "Yes."
          |
Anna:   [book()] "Done! Your booking number is SPA-4821.
         Which number should I send the confirmation to?
         We can also send it to your daughter or son."                       <- option for a family member
```

**Conversation principles (telephone):**
- **One step, one question.** Never ask "When, and for which treatment?" in a single turn.
- **Always paraphrase** before confirming an action. This prevents errors and builds trust.
- **Give the booking number aloud.** A senior guest may not write it down, but hearing it provides reassurance.
- **Offer an SMS to a family member or carer.** Many older guests prefer that a son or daughter also receives the confirmation.

---

#### Phase 3: Error states and edge cases

**Error 1: Anna does not understand (first time)**
```
Anna: "I am sorry, I did not catch that. Could you please repeat?"
```
Calm wording. The words "error" and "problem" are not used.

**Error 2: Anna does not understand (twice in a row)**
```
Anna: "I am sorry for the trouble. To make this easier: is it about a spa treatment,
       information about the hotel, or something else?"
```
Simplifies the question and offers options instead of an open question.

**Error 3: Anna does not understand (three times in a row)**
```
Anna: "I apologise for the inconvenience. I will connect you with our reception
       now, where you will certainly get help."
       -> transfer_to_human()
```
After three failed attempts, the call is always escalated. No further attempts are made.

**Error 4: Webhook does not respond (PMS timeout)**
```
Anna: "One moment, I am checking availability..."
      [if no response after 5 seconds]
      "I am sorry, the connection to the booking system has briefly dropped.
       I will connect you with reception, who can check this directly."
      -> transfer_to_human()
```

**Error 5: No availability**
```
Anna: "Unfortunately there is no free slot at 2:30 PM.
       I have 10:00 AM or 4:00 PM available. Which time suits you better?"
```
Anna always offers an alternative and never ends on "not available".

---

#### Phase 4: Ending the call

| Situation | Anna says |
|---|---|
| Successful booking | "Thank you for calling. We look forward to seeing you on Wednesday. Have a pleasant day." |
| Information only | "I am glad I could help. If you have any further questions, please call again. Goodbye!" |
| After escalation | "I am connecting you to reception. One moment, please." [silence / hold music until reception takes over] |
| Guest says goodbye | "Goodbye, and enjoy your stay!" |

---

#### Phase 5: After the call (SMS)

```
SMS / Telegram:

Bukowy Dwór: Confirmation

Dear Mr. Kowalski,
your booking is confirmed.

Therapeutic back massage
Wednesday, 27 August 2026
2:30 PM
Booking no.: SPA-4821

Spa Centre: ground floor, right-hand side from reception.
Please arrive 5 minutes early.

Questions? Tel. +48 18 123 45 67
```

**SMS UX principles:**
- Short text. Simple visual markers (such as a tick or a calendar symbol) help the guest scan the message quickly.
- The booking number appears at the top.
- Clear directions to the location, because older guests often do not remember them.
- A phone number for questions.

---

---

## Channel 2: Web widget (hotel website)

This channel has a full user interface, designed from scratch.

---

### Context of use

The guest browses the hotel website, often on a computer and sometimes on a tablet. They see the page, a discreet option to talk appears, they click it and start a conversation with Anna.

**Key difference from the telephone:**
- The guest has a screen and can read and listen at the same time.
- We can show a live transcript.
- We can display the confirmation on screen, not only send an SMS.
- The guest can click instead of speaking, which suits those who do not want to talk.

---

### Trigger: how the widget appears

**Option A (recommended): floating button**

Always visible in the lower-right corner of the page:

```
+----------------------------------+
|                                  |
|         [page content]           |
|                                  |
|                  +-------------+ |
|                  | Talk to     | |
|                  | Anna        | |
|                  +-------------+ |
+----------------------------------+
```

- Colour: warm and contrasting, not aggressive red.
- Label: "Talk to Anna". Not "Chatbot" or "AI Assistant".
- After 45 seconds on the page, the button pulses once, gently.

**Option B: inline banner on the booking page**

On the "Bookings" or "Spa" page, above the form:

```
+----------------------------------------------+
| Would you prefer to ask by voice?            |
| Anna can help you book a treatment. [Call]   |
+----------------------------------------------+
```

---

### Widget UI: conversation panel anatomy

When the button is clicked, the conversation panel opens. Full specification:

```
+---------------------------------------+
|  Anna, Bukowy Dwor reception      X   |  <- HEADER
+---------------------------------------+
|                                       |
|         +-----------------+           |
|         |   ANNA AVATAR   |           |  <- AVATAR ZONE
|         |  (animated      |           |
|         |   while speaking)|          |
|         +-----------------+           |
|         Anna is listening...          |  <- STATUS
|                                       |
+---------------------------------------+
|  TRANSCRIPT (live):                   |  <- TRANSCRIPT ZONE
|  +---------------------------------+  |
|  | Anna: Good day! How may I help  |  |
|  |       you?                      |  |
|  |                                 |  |
|  | You: I would like to book...    |  |  <- live, appears
|  |                                 |  |     while speaking
|  +---------------------------------+  |
+---------------------------------------+
|  [Speak]   [Type]   [Call]            |  <- ACTION BAR
+---------------------------------------+
```

---

### Detailed UI element specification

#### HEADER
- Left: Anna's avatar (small circle, warm photo or illustration) and the label "Anna · Reception".
- Right: close button (X), always visible.
- Background: dark navy or white, consistent with the hotel brand.
- Height: 56 px.

#### AVATAR ZONE
- Centre of the panel, the dominant element.
- Animation states:
  - **Idle (waiting):** subtle breathing or a gentle pulse of the outline.
  - **Listening (guest speaking):** sound waves around the avatar, green.
  - **Speaking (Anna responding):** the mouth moves (if illustrated), or stronger wave animation, blue.
  - **Thinking (tool call in progress):** spinner or slow rotation, grey.
- Implementation options: animated SVG illustration (simplest), Lottie animation (richer), or a video avatar such as D-ID or HeyGen (premium).
- Size: 120 × 120 px on desktop, 80 × 80 px on mobile.

#### STATUS BAR (below the avatar)
A single line of dynamic text:
- `Anna is listening...`: while the guest speaks.
- `Anna is responding...`: while speech audio plays.
- `Anna is checking availability...`: while a tool call is in progress.
- `Connecting you to reception...`: during a transfer.

#### TRANSCRIPT ZONE
- Scrollable, at most 40% of the panel height.
- Chat bubbles: guest on the right, Anna on the left.
- The guest's words appear live, streaming word by word.
- Anna's words appear once she finishes speaking, not while the speech is playing.
- Can be hidden. A "Show transcript" checkbox serves guests who do not want to read.
- Font: minimum 16 px (for senior readability), line height 1.6.

#### ACTION BAR (bottom bar)
Three buttons:

**[Speak]**: the primary call to action, the largest button.
- Active by default: the microphone switches on automatically when the widget opens.
- Active state: highlighted, with a wave animation.
- Muted state: grey, with a crossed-out microphone icon.
- Click: toggles the microphone (for guests who want to pause).

**[Type]**: fallback for guests who prefer not to speak.
- Click: the transcript zone turns into a text field with a "Send" button.
- Anna responds by voice (TTS) to the typed text.
- Reason for existing: guests in noisy places, guests with speech difficulties, personal preference.

**[Call]**: optional, for guests who prefer an ordinary phone call.
- Click: opens `tel:` to the hotel reception number (on mobile this dials directly).
- Reason for existing: always offer a way out to a conventional phone call.

---

### Widget screen states

**State 1: Initialising (first 1-2 seconds)**
```
+-----------------------+
|  Anna, Bukowy...      |
+-----------------------+
|     [loading...]      |
|    Connecting to Anna |
+-----------------------+
```

**State 2: Active conversation:** (described above; the main view)

**State 3: Booking confirmation (after book())**
```
+---------------------------------------+
|  Anna, Bukowy Dwor                X   |
+---------------------------------------+
|                                       |
|         Booking confirmed!            |
|                                       |
|  Therapeutic back massage             |
|  Wednesday, 27 August · 2:30 PM       |
|  SPA-4821                             |
|                                       |
|  [Send confirmation by SMS]           |
|  [Ask another question]               |
|  [Close]                              |
+---------------------------------------+
```
- Green background for the confirmation: a clear signal of success.
- Three actions: SMS, keep talking, close.

**State 4: Transfer to a person**
```
+---------------------------------------+
|  Anna, Bukowy Dwor                X   |
+---------------------------------------+
|                                       |
|    Connecting you to reception...     |
|    Please stay on the line.           |
|                                       |
|    Or call directly:                  |
|    +48 18 123 45 67                   |
|                                       |
+---------------------------------------+
```

**State 5: Connection error**
```
+---------------------------------------+
|  Anna, Bukowy Dwor                X   |
+---------------------------------------+
|                                       |
|    Connection problem                 |
|                                       |
|    [Try again]                        |
|    [Call: +48 18 123 45 67]           |
|                                       |
+---------------------------------------+
```
Always offer the phone number as a fallback. Never leave the guest without a way out.

---

### Responsive behaviour

| Device | Widget behaviour |
|---|---|
| Desktop | Floating panel, 380 × 560 px, lower-right corner |
| Tablet | Floating panel, 340 × 500 px, or full-screen modal |
| Mobile | Full screen (100vw × 100vh), button bar at the bottom |

---

### Accessibility (important for the 60+ audience)

- **Font size at least 16 px**, headings 20 px and larger. Do not reduce for aesthetic reasons.
- **Contrast at least WCAG AA (4.5:1)**: dark text on light backgrounds or the reverse.
- **Touch targets at least 48 × 48 px**: older guests have less touch precision.
- **Aria labels** on all interactive elements.
- **No audio autoplay without consent.** Request microphone access on the first open. The Web Audio API requires a user gesture.
- **Visible focus indicator** for keyboard and screen-reader users.

---

## COMPARISON: TELEPHONE vs WIDGET

| Aspect | Telephone | Web widget |
|---|---|---|
| UI | None (voice only) | Full UI (avatar, transcript) |
| Access | Number on hotel materials | Floating button on the website |
| Guest profile | Senior, comfort zone | All ages, actively browsing |
| Transcript | Not available | Live, scrollable |
| Confirmation | SMS after the call | On screen, plus optional SMS |
| Fallback on error | Transfer to a person | Transfer, plus phone number on screen |
| Implementation | ElevenLabs SIP trunk + PBX | ElevenLabs SDK (WebSocket) + signed URL |
| Implementation time (PoC) | 1 day (native integration) | 2-3 days (frontend + signed URL backend) |

---

## CONTENT FOR THE PRESENTATION

On the UX slide, after the persona slide:

**Slide "Two channels, one voice":**
- Left column: telephone icon, "Telephone (SIP)", and three key UX principles as bullets.
- Right column: mockup of the web widget (active conversation state).
- Below: "Same agent, same Anna: different interface, same quality of service."

Optional: a widget wireframe (sketch 4) for design review, if the client asks for more detail on the web UX.
