# Schichtwechsel — Demo Script

> The exact 90-second pitch demo around which the architecture is built.
> **This file is primarily for Christopher.** It lives in the repo so
> Claude treats the demo path as priority — features supporting this
> path get built first.
>
> Read before every major build block. Refresh before the pitch.

## Pitch structure (5 beats, ~90 seconds)

The pitch itself is delivered in German. The narration text below is
the German script Christopher delivers on stage; everything around it
(stage directions, success criteria, recovery lines) is in English.

### Beat 1 — Who + Pain (0:00–0:15)

**Spoken (in German):**

> "I'm Christopher, AI Lead at DRK Clinics Berlin. Doctors in Germany spend three hours a day on bureaucracy and documentation — a large part of which is shift handover. The handover of responsibility for 8 to 12 patients in 30 to 60 minutes. Often chaotic, often with forgotten details. I built the tool I would want to have on my own ward."

**On screen:** logo slide or empty Schichtwechsel screen with your name
in the lower left.

**Success criterion:** judges know after 15 seconds — who, what,
why-credible.

### Beat 2 — Magic moment (0:15–0:55)

**What you do:**

1. (0:15) Click bed 1 — Frau Schmidt appears with context card
2. (0:18) Click record button. Red dot pulses.
3. (0:20) You speak in German for ~30 seconds:

> "Mrs. Schmidt, Bed 1, 67 years old. Pneumonia Day 3. Antibiotic treatment is ongoing with Amoxiclav. She is significantly better today and has been fever-free since yesterday. Oxygen saturation is stable at 96 percent. Please check her CRP tomorrow. If it continues to be good, discharge on Thursday might be possible. Her daughter called and would like to accompany her to the ward round tomorrow."

4. (0:50) You click stop. Live transcript was visible while you spoke.
   Spinner for 2-3 seconds.
5. (0:53) SBAR card appears, cleanly structured. **One yellow
   inconsistency warning in the middle.**

**What must be on screen by the end of Beat 2:**

```
┌─────────────────────────────────────────────────┐
│ Frau Schmidt, Bed 1                             │
├─────────────────────────────────────────────────┤
│ S: Pneumonia Day 3,                             | 
|     Clinically significantly improved           │ 
│ B: Antibiotic treatment Amoxiclav (Day 3 of 7)  │
│ A: ⚠ "Fever-free since yesterday" — last        │
│ measured temperature 38.4°C 4 hours ago         │
│ Saturation 96% stable                           │
│ R: Follow-up CRP test tomorrow,                 |
|    possible discharge Thursday                  |
│ Coordinate visit with daughter tomorrow         │
│                                                 │
| Completeness: 87% Allergies not mentioned       │
└─────────────────────────────────────────────────┘
```

**Success criterion:** judges see the system isn't just transcribing,
it is **understanding**. The inconsistency warning is THE aha moment.
If it's on screen for less than 3 seconds, the demo failed.

### Beat 3 — How (0:55–1:10)

**Spoken:**

> "This runs on a finely tuned Pioneer GLiNER2 model. 200
> million parameters, runs on any hospital laptop without cloud storage.
> Voice structuring in under 100 milliseconds. For comparison:
> the same task via GPT-4 takes 1.5 seconds, costs
> a few cents per transfer, and patient data leaves the hospital. Not here."

**On screen:** you click a small "model comparison" toggle in the UI.
Side-by-side: fine-tuned GLiNER vs GPT-4o. Both F1 scores comparable
(~85% vs ~88%), but the latency bar for GLiNER is 10x shorter.

**Success criterion:** Pioneer judges hear the three numbers they want
to hear — F1 comparable, latency drastically better, cost approaching
zero. On-device as bonus for the DSGVO context.

### Beat 4 — Market + urgency (1:10–1:25)

**Spoken:**

> "There are 1,900 hospitals in Germany. Every ward physician spends
> over 30 minutes daily on handovers. That's millions of hours a
> year — facilitating change is a direct market need, not a
> nice-to-have. With the hospital reform and a 50-billion-euro
> transformation fund until 2035, the window of opportunity for tools like this
> is now open"

**On screen:** a simple metrics slide, or keep showing the SBAR demo.
No animations, no charts. You speak; the screen merely supports.

**Success criterion:** judges feel there is a real market without
buzzword bullshit. The Krankenhausreform is a date, not a marketing
slogan.

### Beat 5 — The ask (1:25–1:30)

**Spoken:**

> "I'm piloting shift changes starting Monday at DRK Clinics Berlin.
> If you're a pioneer: I'm using your model in the critical path
> and have beaten the latency and costs you're
> competing against. If you're an Aikido practitioner: here's my security report, before
> and after. I'm grateful for any connection that helps me bring this
> model from DRK to other German hospitals."

**On screen:** repo URL, GitHub QR code, your name.

**Success criterion:** concrete ask, not "thank you for your attention".
Sponsor reps in the jury know which prize fits this project.

## What technically MUST work for this (demo-path-critical)

In build priority order. If any of these fails, the pitch is dead.

1. **Patient list loads with three patients** — otherwise no selection.
2. **Patient detail card renders** — otherwise no context.
3. **Record button starts recording** — otherwise no voice input.
4. **Transcription returns German text** — otherwise no structuring.
5. **GLiNER2 produces an SBAR card** — otherwise no magic.
6. **VITAL_TREND detector finds the Frau Schmidt inconsistency** —
   otherwise no aha moment.
7. **Completeness score shows "allergies missing"** — otherwise no
   decision-support demonstration.
8. **Model toggle for the Pioneer comparison** — otherwise no sponsor hit.

Everything else (multi-patient flow, Entire approval, allergy collision,
FHIR Bundle export) is stretch. If anything on the list above is broken,
it is Day-2 repair priority #1.

## What you bring on pitch day

**Hardware:**
- Laptop with ShiftChange/Schichtwechsel running on `localhost:5173`
- External microphone if the pitch stage has loud background noise
- mobile phone as a backup second display in case the stage has no second monitor
- Adapter cables (HDMI/USB-C, depending on stage)

**Software backups:**
- Backup video recorded (Day 2 evening, OBS, 90 seconds, MP4)
- Aikido screenshots (baseline + final) as PNG/JPEG
- Repo public and live, in case a judge wants to look immediately
- README with quickstart command prominent

## Rehearsal checklist before the pitch

Day 2 afternoon, run through completely at least three times:

- [ ] Beat 1 under 18 seconds
- [ ] Voice recording in Beat 2 under 35 seconds
- [ ] SBAR card appears reliably (5/5 dry runs okay)
- [ ] Inconsistency warning is understood at first glance
- [ ] Model toggle in Beat 3 works without stutter
- [ ] Beats 4 + 5 together under 25 seconds
- [ ] Total under 95 seconds
- [ ] Backup video reachable in 2 clicks in the browser
