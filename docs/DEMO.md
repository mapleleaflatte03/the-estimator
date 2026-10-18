# 10-minute demo script (finalist night, English)

Live app: https://the-estimator-9m6a.onrender.com · Repo: https://github.com/mapleleaflatte03/the-estimator

**Before going on stage:**
- Open the live URL 2 minutes early: the free instance sleeps and takes up to ~50 s to wake.
- Keep a second tab on the repo README.
- Pre-type the car-wash brief (step 4) into a text file.
- The app opens in English. **VI** in the header switches every label, and the downloaded quote follows that choice.

## 0:00 – 0:45 · The problem (no slides needed)

> "Every software agency quotes from a client brief. A senior person reads it line by line, guesses hours, misses the
> things the client hasn't actually committed to, and nobody checks the guess against what really happened. The
> challenge asked for three things: work out what's being asked, what's missing, and how long it takes, then get more
> accurate from actual hours. That's exactly the loop we built, and every claim I'll show was measured on data the
> system never saw."

## 0:45 – 3:00 · A brief from your world

1. Open **New project** and pick the sample *Investor onboarding portal for a private equity fund*. Press **Estimate**.
   It answers in under a second because the AI's readings are cached.
2. **Estimate:**
   > "The first number covers the work the client has actually committed to. Tentative items are listed separately, with the hours they would add if confirmed. The range shows uncertainty in the included work."

   Move the confidence slider to 80% and point at the budget and timeline, which respect the critical path.
3. **Work:** open any requirement.
   > "Every line is tied to the exact sentence in the brief. Here the keyword rules thought 'subscription' meant
   > payments; the AI read the sentence, said no, and removed it. It didn't vanish: it became a question for the
   > client."
4. **Questions:**
   > "Questions are ranked by how many hours depend on the answer. 'Possibly an AI assistant… if the budget allows' is
   > uncommitted scope worth 105 hours."

   Click **Yes** to include it and watch the estimate rise. Every answer creates a new, immutable version.

## 3:00 – 4:30 · Live: a brief nobody has seen

Paste the car-wash brief into **New project**:

```
Project: booking platform for a chain of 12 car-wash stations.
- Customers book a wash slot online and pick the station and service package.
- Customers pay by card when booking; refunds if cancelled 2 hours ahead.
- Send a reminder by SMS one hour before the slot.
- Station managers see only their station's bookings; head office sees all.
- Monthly revenue report per station and per package.
- Maybe later a loyalty programme with points, still being discussed.
```

> "The AI, Jev by TypeSafe, reads every clause with three questions: what kind of work, has the client committed,
> and will it take longer than it looks. About 1.5 seconds, a fraction of a cent. It caught 'maybe later… still
> being discussed' as uncommitted."

The key icon in the header lets anyone use their own AI key.

## 4:30 – 6:00 · It learns from actual hours

Open **Actual hours** on the sample project. Enter a clearly labelled *simulated demo outcome*, expand *per requirement*,
and enter a couple of values. Save. The original estimate is frozen.

> "A completed project's result can change only future estimates. This input is simulated for the demo; it does not
> validate the estimate's accuracy. The model partially pools by project type and work kind, so one outcome cannot
> swing it completely."

Click **Estimate a new project to test the learning**. Reuse the sample brief as a second project and compare its
calibration multiplier with the frozen first estimate. Do not present this as a measured accuracy gain.

## 6:00 – 8:30 · Why you can trust it (Evidence tab)

Point at the four cards at the top, then the charts:
- **Learning from real actual hours.** 10,022 real tasks (SiP).
  - Fitted on 2004–2010 and tested on 2,248 later tasks: error **−10.4%** vs the developers' own estimates, SA
    48.6 → 54.0%, Wilcoxon p = 3×10⁻⁶.
  - Replayed day by day as if in production, using only work already finished: SA 56.3 → **61.1%** versus human estimates. A frozen calibrated model scored 61.4%, so continuous updating did not win that comparison.
- **The AI catches uncommitted scope.** 8 rounds of new clauses, labels committed before every run: **30/31** caught
  vs 14/31 with keyword rules, zero false alarms.
- **AI verification stops rules adding work nobody asked for.** Precision 73 → 83% and 85 → 96% on two fresh rounds.
- **What didn't work.**
  > "We had the AI judge 'will this take longer than it looks' on 798 real tasks. It ranks risk, but it did not make
  > hour estimates more accurate, and on 2,032 issues from 37 other organisations the effect was weak. So the app
  > flags those clauses for review instead of inflating hours. We publish the failures too: the journal has 48 runs."

## 8:30 – 10:00 · Architecture and close

> "FastAPI plus React in one container.
> - The AI is a pool of keys with failover, 5 to 20 questions per call, every answer cached per question version, a
>   pinned model, and a circuit breaker that stops spending if a paid call returns nothing usable.
> - The estimates come from a Monte Carlo with a shared 'everything ran over' shock resampled from 56 real work
>   packages, not an assumed curve.
> - Automated tests and CI. Every number in the README has a one-line command to reproduce it.
>
> It reads like a senior estimator, shows its evidence, asks before it guesses, and gets better with every project
> you close."

## Likely questions

| Question | Answer |
| --- | --- |
| Isn't SiP old and from one company? | Yes. It's the only public dataset with task text, estimate and actual together, and we say so. That's why we replicated on Itemlet (37 projects) and why the app learns from *your* actuals. |
| What if the AI is down? | You get a clear message instead of a weaker estimate; cached briefs still work, and you can paste your own key. |
| Confidential briefs? | Use TypeSafe directly (no training on data, DPA); the reseller route is for demos. Self-hosting is a Docker image. |
| Cost? | About $0.04 per million input tokens: a 12-clause brief costs ~$0.0002. |
| Why not just ask an LLM for hours? | Hours, simulation and learning stay in code so they can be measured and calibrated; the AI does the judgements it is good at, each validated on held-out data. |
| Can a team sign this quote? | It is an internal draft. The work-type hour templates and SiP spread have not been validated against complete client briefs and actual outcomes for this team. A delivery lead must review it before commitment. |
