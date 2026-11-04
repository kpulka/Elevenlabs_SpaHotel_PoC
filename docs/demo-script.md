# Demo Walkthrough: Three Scenario Paths

> Script for the presenter running the stakeholder demonstration.
> Each path contains: setup, the conversation to run, and the points to draw out with the audience.

---

## Setup before the demo

1. Start the mock backend: `cd mock_backend && uvicorn main:app --reload --port 8000`
2. Open the ElevenLabs console with the Anna agent, or open the web widget.
3. If demonstrating Telegram delivery: place a second monitor with the Telegram channel visible.
4. Open the Swagger UI (`localhost:8000/docs`) in a third window to show the integration layer.

---

## PATH A: Spa treatment booking (main path)

**What it shows:** tool calling, step-by-step data collection, SMS confirmation, latency.

**Before you begin, say to the audience:**
> "I am now going to call Anna. Please notice three things: the pace of her speech, the way she collects information one step at a time, and the moment a message appears in Telegram on this screen."

**Conversation (presenter as the guest):**
```
You:   "Good day, I would like to book a massage."
Anna:  "Good day, I am happy to help. We have a therapeutic back massage and a
        classic relaxing massage. Which of these interests you?"
You:   "The back massage, please."
Anna:  "Of course. Which day would you like to book?"
You:   "Um... Wednesday."
Anna:  [calls check_spa_availability in the background]
        "Let me check... On Wednesday 27 August I have the following times: 10:00, 2:00 PM
        and 2:30 PM. Which time suits you?"
You:   "2:30."
Anna:  "Thank you. May I have your name?"
You:   "Kowalski, Jan Kowalski."
Anna:  "Let me confirm: I am booking a therapeutic back massage on Wednesday 27 August
        at 2:30 PM for Mr. Jan Kowalski. Is that correct?"
You:   "Yes, that is correct."
Anna:  [calls book_spa_appointment]
        "Your booking is confirmed, number SPA-4821. Which telephone number should I
        send the confirmation to? We can also send it to your daughter or son, if you prefer."
You:   "To mine: 48 123 456 789."
Anna:  [calls send_sms_summary]
        "I have just sent the confirmation to your phone. Is there anything else I can help with?"
You:   "No, thank you very much."
Anna:  "Thank you for calling. Have a pleasant day, and goodbye!"
```

**Points to draw out after the demo:**
> "Notice a few things. Anna asked one question at a time. That is a deliberate design decision for older callers. She paraphrased the booking before confirming it, which prevents booking errors. Two webhooks ran in the background: the booking and the SMS. The message appeared here [point to Telegram] before the call ended. The total response latency is around 430 milliseconds."

---

## PATH B: Knowledge base information (RAG)

**What it shows:** strict grounding, retrieval without hallucination, natural conversation.

**Before you begin, say to the audience:**
> "Now I will show how Anna answers information questions. The agent may not invent information: every answer must come from the knowledge base."

**Conversation (presenter as the guest):**
```
You:   "What time is breakfast?"
Anna:  "Breakfast is served as a Swedish buffet from 7:30 to 10:00 AM. Can I help with anything else?"

You:   "Does the swimming pool require a swimming cap?"
Anna:  "Our thermal pools have gentle steps and sturdy handrails.
        For the rules on swimming caps, I will connect you with reception,
        where you will get an exact answer."
        [calls transfer_to_human]
```

**Points to draw out after the demo:**
> "Do you see the difference? For the first question, Anna answered directly, because the information is in the knowledge base. For the second, the knowledge base does not contain the answer about swimming caps, so instead of guessing, she escalates immediately. That is strict grounding. In a health resort, where a guest may have a heart condition, a made-up answer is a legal liability for the hotel."

**Variant: a question at the boundary:**
```
You:   "Can I bring my dog?"
Anna:  "Certainly. We accept small dogs and cats up to 10 kilograms, at a charge
        of 50 zloty per night. Guide dogs are free of charge and may enter
        all areas, including the restaurant."
```
> "Here the retrieval worked as intended: the information is in the procedures knowledge base, so Anna did not need to escalate."

---

## PATH C: Escalation and human handoff

**What it shows:** safety, handling of edge cases, live transfer to a person.

**Before you begin, say to the audience:**
> "Now I will show the most important safety feature. My phone is configured as the medical duty line. In a moment, it will ring."

**Conversation (presenter as the guest):**
```
You:   "Good day, I would like to book a mud bath,
        but I have a pacemaker."
Anna:  "I understand. Before I book this treatment, I need to ask about a health
        matter. A mud bath with a pacemaker requires a prior consultation with
        our resort physician. I am connecting you to our medical duty line now.
        One moment, please."
        [calls transfer_to_number -> the presenter's phone rings]
```

**Points to draw out after the demo:**
> "This is the key moment. The guest mentioned a pacemaker, and the agent recognised it as a contraindication for this specific treatment and did not take the risk. The call reached my phone immediately. In production, it would ring the nursing duty desk. Importantly, Anna did not simply say 'I don't know'. She explained why she was escalating and what happens next. For an older guest, that is the difference between feeling safe and feeling frustrated."

---

## WHAT TO SHOW "UNDER THE HOOD" (for technical reviewers)

After the demo, open two or three of the following:

**1. ElevenLabs console: agent configuration**
> Show the system prompt, the list of tools with their JSON Schemas, the voice parameters (stability, speed), and the knowledge base configuration (prompt and auto modes).

**2. Swagger UI (localhost:8000/docs)**
> Show the endpoints, and run a live `POST /check_spa_availability` request from the Swagger window. Show the JSON response.

**3. Mock backend console logs**
> Show the readable logs with separators for each call: "here you can see each tool Anna called and what she received in response."

---

## FALLBACK: if something does not work

**Mock backend does not respond:**
> "Normally, the webhook to the backend would run at this point. Instead, I will show you the JSON response the agent receives when it checks availability: [open `mock_backend/data/spa_schedule.json`]. This is exactly what Anna sees when she checks appointment times."

**ElevenLabs agent does not respond:**
> "Instead, I will show the sequence diagram and walk through the architecture step by step. In my view, that is equally valuable from a system design perspective."

**Poor transcription:**
> "This is a good example of a real-world challenge. Scribe v2 handles Polish well, but regional accents are an area for improvement. In production, we would add fine-tuning examples and a pronunciation dictionary for specific place names."
