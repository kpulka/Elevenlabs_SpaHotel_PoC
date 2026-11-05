# Client Discovery Workshop: Question Bank

> **How the workshop runs:**
> The facilitator opens with a deliberately broad brief, for example "Design a voice assistant for the hotel."
> The task is to ask questions and shape the solution **together with the client**.
> Do not search for information online during the session, and do not present a monologue. The session is a discussion.
>
> **What the facilitator listens for:**
> - Are questions asked before solutions are proposed?
> - Are the questions relevant to the decision at hand, rather than trivial?
> - Are the answers listened to and built upon?
> - Is the scope narrowed deliberately, rather than designing everything at once?

---

## QUESTION STRUCTURE: 5 areas

Work through the areas in this order. Each area has two to three questions. Then check whether there is enough information to move on.

---

### AREA 1: End user (who they are, what they need)

> *Principle: never design without a persona. Establish who uses the assistant before discussing architecture.*

**Questions:**
1. "Who is the main user of this assistant: hotel guests, reception staff, or both?"
2. "What is the typical age and profile of a guest? Are we mainly serving senior guests, business travellers, or tourists?"
3. "Should the guest contact the assistant on their own initiative, or should the assistant *initiate* contact (for example, calling before arrival)?"

**What to listen for:**
- If the answer is *"seniors, telephone"*: "In that case, latency and voice tone become critical. A fast, robotic voice would discourage the caller."
- If the answer is *"business guests, app"*: "That changes the channel. A WebSocket widget instead of a SIP trunk, and we can keep responses shorter."

---

### AREA 2: Channel and infrastructure (where it runs)

> *Principle: "voice AI" can mean five different technical things. Make sure you are discussing the same one.*

**Questions:**
1. "Through which channel should the assistant operate: a traditional telephone line, a website widget, a mobile app, or a terminal at reception?"
2. "Does the hotel already have a telephone exchange (PBX)? Can we connect to it through a SIP trunk?"
3. "Are we dealing with a single property or a network of hotels? This changes how the configuration is designed."

**What to listen for:**
- *"A network of 10 hotels"*: "The key question is whether we use one central agent with dynamic variables, or a separate instance per hotel. I would recommend a central agent, because it is easier to maintain."
- *"A widget on the website"*: "We need to discuss signed URLs. The agent must not expose an API key in the front end."

---

### AREA 3: Functional scope (what it must be able to do)

> *Principle: narrow the scope actively. Do not wait for the client to say what to cut; propose it yourself.*

**Questions:**
1. "What are the three most common reasons a guest calls reception right now? I would like to start with those."
2. "Should the assistant only *inform* (FAQ, opening hours), or should it also *act* (book, cancel, transfer the call)?"
3. "What happens when the assistant does not know the answer or the situation is difficult? Must there be an option to hand over to a person?"

**Typical answers and suggested responses:**
- *"Bookings and information"*: "Good. That means two layers: a knowledge base (RAG) for static questions, and tool calling for dynamic actions. I suggest starting the MVP with the knowledge base, because it is cheaper and faster to deploy."
- *"Information only (FAQ)"*: "In that case we can simplify the architecture. We do not need a PMS webhook at the MVP stage."

---

### AREA 4: Data and external systems (integrations)

> *Principle: integrations are always the largest delivery risk. Ask about them early.*

**Questions:**
1. "Which hotel systems are already in use? A PMS (for example Opera or KWHotel), a CRM, a spa booking system?"
2. "Do we have API access to these systems, or will we need to work through files or manual exports?"
3. "Who on the hotel side will be the technical owner of this deployment? Is there someone who manages the integrations?"

**What to listen for:**
- *"We have an API for Opera"*: "That changes the timeline. We could move from mock to production in two to three weeks."
- *"We do not have an API"*: "In that case, the MVP runs on a static knowledge base and mock services. That is sufficient for validation."

---

### AREA 5: Success and constraints (how we measure, what blocks us)

> *Principle: the definition of success must come before the architecture, not after. Otherwise the design is made in a vacuum.*

**Questions:**
1. "How will we know in three months that the deployment has succeeded? Which KPIs matter to the client?"
2. "Are there regulatory, compliance or GDPR constraints that must be considered from the start?"
3. "What is the realistic budget and timeline? Are we talking about a one-hotel pilot over four weeks, or a full rollout?"

**Typical answers:**
- *"KPI: percentage of calls handled without a person"*: "A good KPI. I would also add CSAT. An assistant that handles 90% of calls but irritates guests is not a success."
- *"Medical data, health resort"*: "That requires Zero Retention Mode and conversation history redaction, which are part of the ElevenLabs Enterprise plan. We need to include this in the costs from the outset."

---

## HOW TO RUN IT IN PRACTICE

### Pace and posture
- Ask in groups of one or two questions, not a list of ten at once.
- After each answer, **paraphrase** what you heard and **state what it changes** in the design.
- If the client says *"decide for yourself"*: decide, and say why: "I am assuming X because Y. If that is the wrong assumption, please let me know."

### Signal that it is time to close questions and move to sketching
You have enough when you know:
- Who the user is (persona).
- Through which channel (telephone / widget).
- What it must do (at least two or three functions).
- What is out of scope for the MVP.
- What success looks like.

Then say: *"I believe I have enough context to start sketching. I will begin with a high-level architecture."*

---

## QUESTIONS TO AVOID

- "What should the assistant be called?" Trivial, and does not move the design forward.
- "Which LLM do you use?" Too technical for this stage.
- "Do you have logo colours we should use?" UI design, not relevant at this stage.
- A run of ten questions without listening to the answers. That is an interrogation, not a discussion.
