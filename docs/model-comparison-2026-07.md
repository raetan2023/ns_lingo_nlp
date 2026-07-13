# Model comparison — July 2026

Zero-shot eval on 8 NS prompts. No glossary / RAG. System prompt: NS expert, Singapore context only.

**Models:** `gemini-3.1-flash-lite` vs `aisingapore/Llama-SEA-LION-v3-8B` (4-bit, local GPU)

**Verdict:** Gemini clearly stronger. SEA-LION often refused or hallucinated. Gemini still wrong on **stand by area** (confused with area cleaning / bunk inspection).

---

## [1] What does rabak mean in NS?

### Gemini
In an NS context, **rabak** describes a state of being completely disorganized, broken, shattered, or physically/mentally exhausted. Often: a disheveled person, a chaotic situation, or extreme fatigue after strenuous activity. Equivalent to "wrecked" or "a total mess."

### SEA-LION
I don't know. I don't know.

---

## [2] Explain pes b4 to someone who never served NS.

### Gemini
**PES B4** — Physical Employment Standard B4. Combat-fit but medically downgraded; modified BMT; duties restricted to avoid aggravating medical conditions.

### SEA-LION
Wrong — described PES as 3 categories (1/2/3).

---

## [3] What is bookout in National Service?

### Gemini
Leaving camp at end of week/duty to return home; start of time off after final check.

### SEA-LION
Vague — "released from NS."

---

## [4] Translate: Sgt say mono intake very jialat.

### Gemini
The Sergeant said that being in a mono-intake unit is very tough/difficult.

### SEA-LION
No translation — echoed input.

---

## [5] What does ORD mean in Singapore NS?

### Gemini
**Operationally Ready Date** — end of full-time NS, transition to ORNS.

### SEA-LION
Wrong — "Out of Regular Duties."

---

## [6] Explain what PES A means for enlistment.

### Gemini
Highest fitness classification; eligible for all combat vocations; standard BMT at Tekong.

### SEA-LION
Thin but directionally OK.

---

## [7] What is remedial training in NS?

### Gemini
Mandatory IPPT remediation sessions; FCC/camp training; disciplinary consequences if not completed.

### SEA-LION
Wrong tone — "form of punishment."

---

## [8] What does stand by area mean in army camp?

### Gemini
**Wrong** — described as cleanliness inspection / area cleaning (SBA conflated with bunk inspection).

### SEA-LION
I don't know.

---

## Decision

Dropped local fine-tuning (Danube2, SEA-LION as bot backend). **Next:** Gemini + RAG over `seed.json` + `curated.json`.
