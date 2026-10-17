# Challenge brief: "The Estimator" (Anduin Cybernetics · Agent in the Shell hackathon, October 2026)

> Research date: 17 Oct 2026. The challenge **was found**. The main source is the official event page, https://cybernetics.anduin.tech/agent-in-the-shell (read 17 Oct 2026). That page is a static site that contains both the "Applications open" and "Sign-ups closed" panels, so the "closed" text may just be a template that switches on after the deadline and does not mean sign-ups were already closed on 17 Oct. Note on method: the web-search tool kept failing, so sources were found through Bing RSS, the GitHub API, and by fetching pages directly.

## Who is Anduin Cybernetics, and what is "The Estimator" challenge (problem statement, deliverables, constraints, deadline, prize)?

### Takeaway
Anduin Cybernetics is a new "business-centric AI Task Force" in Ho Chi Minh City, set up by Anduin (Anduin Transactions), a technology company for private markets. "Agent in the Shell" is its invitation-only hiring hackathon, and it offers six challenges. "The Estimator" is challenge 02 (Sales & delivery): build a working tool that scopes incoming client requests faster and more consistently, and gets more accurate over time. Two things must be submitted: a live app and a public GitHub repo. Submissions close Mon 19 Oct 2026 at 11:59 pm (Ho Chi Minh City time). Finalists give a 10-minute demo on 22 Oct. Total prizes are $1,000+.

### Cited Findings
**Organiser**
- Anduin calls itself "the technology partner for private markets". It says many of the world's largest investment firms raise funds on its platform, from more than 76,000 investors, with "$265B+ raised on Anduin worldwide". The product is built in Vietnam, and the team "uses AI in every function, every day". — [Agent in the Shell event page](https://cybernetics.anduin.tech/agent-in-the-shell)
- Anduin Cybernetics is described as "Our business-centric AI Task Force in Ho Chi Minh City: AI transformation for operations and digitization". The site footer says Anduin has "120+ people in Vietnam". — [Event page](https://cybernetics.anduin.tech/agent-in-the-shell)
- The LinkedIn announcement says Anduin is "forming a new AI Operational Task Force called Cybernetics, and we're recruiting its founding members". It calls Agent in the Shell "an invitation-only hackathon where you'll have 10 days to build a solution to a real business challenge". — [Huynh-Anh Vo, LinkedIn post (~10 Oct 2026)](https://www.linkedin.com/posts/vharmnc_anduintransactions-agentintheshell-hackathon2026-activity-7514222665813905408-1S3I)
- An Anduin Transactions Talent Acquisition Coordinator posted that participants "compete for a spot in Anduin Cybernetics, our brand-new AI operations unit". — [Bùi Phương Nguyên, LinkedIn (indexed ~14 Oct 2026)](https://www.linkedin.com/posts/buiphuongnguyen_anduintransactions-hackathon-ai-activity-7516083814524264448-BD18). Only the search snippet was readable; the full post was blocked.

**The Estimator problem statement (official text)**
- Challenge: "Can you build a tool to scope incoming work faster and more consistently, and become more accurate over time?" — [Event page, challenge modal "Sales & delivery / The Estimator"](https://cybernetics.anduin.tech/agent-in-the-shell)
- Problem: "Before a team can commit to a client, someone has to read what the client sent and work out what's actually being asked, what's missing, and how much effort it will take. That read is slow, and may vary depending on whoever happens to do it. Estimates are often gut feel, and nobody checks them against how long the work really took, so they never get better." — [Event page](https://cybernetics.anduin.tech/agent-in-the-shell)
- Short card summary: "Scope incoming client requests faster and more consistently, and get more accurate over time." — [Event page](https://cybernetics.anduin.tech/agent-in-the-shell)
- The other five challenges are The Slot Finder (Operations), The Memory Bank (Knowledge), The Legal Reviewer (Legal), The Early Warning System (Project management) and The Investigator (Customer success). — [Event page](https://cybernetics.anduin.tech/agent-in-the-shell)
- "The challenges are hypothetical, with made-up data. You own what you build." — [Event page](https://cybernetics.anduin.tech/agent-in-the-shell)

**Deliverables and constraints**
- "Small and working beats big and imagined. If it doesn't run, it doesn't count. We'd rather you ship an MVP." — [Event page](https://cybernetics.anduin.tech/agent-in-the-shell)
- What to hand in: "01 A live app — A link judges can open. Any host." and "02 Its GitHub repo — Full source, public on GitHub." Not accepted: "Slides, mockups, chat or AI artifact pages." — [Event page](https://cybernetics.anduin.tech/agent-in-the-shell)
- Process: "Pick a challenge · Open a repo, send the link · Submit by Mon 19 Oct, 11:59 pm". Also: "Submit early, so we have more time to review your work properly." Submissions go through a builder portal at cybernetics.anduin.tech/portal (Google sign-in). — [Event page](https://cybernetics.anduin.tech/agent-in-the-shell)

**Timeline**
- Sign-up from 8 Oct to Mon 19 Oct. Builds are due on 19 Oct, 11:59 pm. Finalists are chosen by Tue 20 Oct ("We review every build. Maybe a short call."). Fest night is 22 Oct, 4–9 pm, in Ho Chi Minh City: "Dinner and a 10-minute demo." — [Event page](https://cybernetics.anduin.tech/agent-in-the-shell)
- "Finalists demo in English." "Any background welcome." There are 5–10 finalist seats. — [Event page](https://cybernetics.anduin.tech/agent-in-the-shell)
- **Conflict:** the LinkedIn announcement gave "Application deadline: October 16, 2026, at 11:59 PM" ([LinkedIn](https://www.linkedin.com/posts/vharmnc_anduintransactions-agentintheshell-hackathon2026-activity-7514222665813905408-1S3I)), but the event page says sign-ups and builds close Mon 19 Oct, 11:59 pm ([Event page](https://cybernetics.anduin.tech/agent-in-the-shell)). The 19 Oct date on the official page is the later one and probably the one in force.
- The project's own dev log records the challenge window as "15–19/10/2026". — `docs/dev_log.md` in this repo

**Prize**
- "$1,000+ in prizes". Finalists get an exclusive dinner with the Anduin team, and there is a chance to "join the founding of Anduin Cybernetics" (hiring). — [Event page](https://cybernetics.anduin.tech/agent-in-the-shell); [LinkedIn](https://www.linkedin.com/posts/vharmnc_anduintransactions-agentintheshell-hackathon2026-activity-7514222665813905408-1S3I)

### Inferences
- This is a **hiring hackathon**. Judges will be looking at the builder as much as the product: business sense, engineering judgement, and how clearly they explain things in an English demo.
- The problem statement has three explicit parts, and judges will probably check each one: (1) **speed**, reading the brief quickly; (2) **consistency**, giving the same result whoever runs it, and finding "what's actually being asked, what's missing"; (3) **getting more accurate over time**, comparing estimates with actual hours and feeding that back. A winning entry should show all three working end to end in the live app.
- The brief says "made-up data". That means no dataset is required, and inventing realistic sample briefs is allowed. Using a real public dataset, as PARALLAX does with SiP, would set an entry apart, but the rules do not ask for it.

### Gaps
- The full brief for each challenge (behind "Read the brief →" and possibly with more detail or sample data in the builder portal) could not be read. The public modal text may be shorter than the full brief.
- How the $1,000+ is split (first, second, per challenge, etc.) is not published.
- Who the judges are is not published.

## What are the judging criteria and their weights?

### Takeaway
The weights are published: **Depth of the solution 30%, Architecture 20%, Product quality 20%, Challenge complexity 15%, Use of AI 15%.** No sub-criteria are published. Accuracy, evidence, UX, demo quality and code quality are not listed separately. They count only through these five headings.

### Cited Findings
- "How we judge: 30% Depth of the solution · 20% Architecture · 20% Product quality · 15% Challenge complexity · 15% Use of AI." — [Event page](https://cybernetics.anduin.tech/agent-in-the-shell)
- "If it doesn't run, it doesn't count." Slides, mockups, chat or AI artifact pages do not count. — [Event page](https://cybernetics.anduin.tech/agent-in-the-shell)
- Finalists are picked from a review of every build, possibly with a short call, and then give a 10-minute demo on 22 Oct. — [Event page](https://cybernetics.anduin.tech/agent-in-the-shell)

### Inferences
These map the headings onto the Estimator; they are interpretation, not published rules.
- **Depth (30%)**: the full loop actually works (brief → scope, gaps and questions → estimate with ranges → record actuals → better estimates later), not just one LLM call. This is where a measured, real accuracy improvement (holdout benchmark, calibration) would score.
- **Architecture (20%)**: a clear split between AI judgement and deterministic maths, clean data contracts, versioning, tests, and the ability to deploy. The public repo is how judges will check this.
- **Product quality (20%)**: the live app is reliable and polished, and a judge with no setup can complete the main flow. Failures that block the flow (for example a 503 when no AI key is available) would probably hurt this score.
- **Challenge complexity (15%)**: the Estimator is one of six challenges. This weight may partly reflect which challenge was picked. Within the Estimator, taking on harder parts (multiple languages, uncertainty, learning over time) probably helps.
- **Use of AI (15%)**: the AI should be purposeful and visible, and ideally its value should be measured. "Use of AI" is a fairly small share, so an AI-heavy entry that is shallow or does not run would lose more under Depth and Product quality than it gains here.
- A 10-minute English demo means the story needs to fit into about 3–4 screens. Clear before-and-after accuracy numbers will help.

### Gaps
- There is no published rubric text for each heading and no scoring scale.
- It is not known whether the finalist demo is scored on the same weights or judged separately.

## Is there a required dataset, benchmark, evaluation harness, or required tech (e.g. TypeSafe Jev / System One)?

### Takeaway
No. The event page does not mention any dataset, benchmark, harness, or required model or vendor. The challenges use "made-up data", and any hosting is allowed. **TypeSafe/Jev (System One) is not required by the challenge.** It is a choice the PARALLAX team made.

### Cited Findings
- "The challenges are hypothetical, with made-up data." "A link judges can open. Any host." The page names no required model, API, or dataset. — [Event page](https://cybernetics.anduin.tech/agent-in-the-shell)
- TypeSafe describes Jev as "TypeSafe's flagship model and the first System One model". It takes a state plus typed questions (Choice, Score, Noul) and returns typed answers with probabilities and sometimes confidence, with "no text generation, no parsing". — [TypeSafe docs](https://docs.typesafe.ai)
- PARALLAX makes Jev mandatory by its own design: "The AI reader (Jev) is required: every clause of a new brief is read by Jev before an estimate is produced… If Jev cannot read every clause (no key, credits exhausted, hourly cap), the API answers 503." — [the-estimator README](https://github.com/mapleleaflatte03/the-estimator)
- A competing Estimator entry (EstimateOS) uses Google Gemini 2.0 Flash, with Groq Llama-3.3-70B as a fallback and an offline heuristic or mock extractor. This shows that other models are acceptable. — [EstimateOS Tools manifest](https://raw.githubusercontent.com/Thomas-DataLab/estimate-os/main/docs/06_TOOLS_AND_SKILLS_MANIFEST.md)

### Inferences
- Since no model is required, using Jev only matters if it improves "Use of AI" and "Depth". PARALLAX's measured held-out gains from Jev (for example, uncommitted-requirement detection of 20/21 with Jev against 6/21 with rules alone) are good evidence for the "Use of AI" heading.
- No benchmark is set, so a team that brings its own honest evaluation (temporal holdout, held-out labelled clauses, journal of runs) is doing more than the brief asks. This could stand out under "Depth".

### Gaps
- It is not known whether the full brief in the builder portal includes sample client requests or a starter dataset. Nothing public suggests it does.
- No information was found on whether TypeSafe or JevStation has any link with Anduin or this hackathon (sponsorship, credits). It looks unrelated, but this was not verified.

## Any published rules about live demos, API keys, or bring-your-own-key for judges?

### Takeaway
The only published rule is that the live app must be "a link judges can open" on any host, and that it must actually run. Nothing is published about API keys, bring-your-own-key, cost limits, or uptime. The safest reading is that judges must be able to use the main flow without supplying their own keys.

### Cited Findings
- "A live app — A link judges can open. Any host." "If it doesn't run, it doesn't count." — [Event page](https://cybernetics.anduin.tech/agent-in-the-shell)
- The event site's AI agent "Answers come only from our published event guide and are not an offer, contract or official terms". This suggests there is a separate published "event guide" that was not found publicly. — [Event page](https://cybernetics.anduin.tech/agent-in-the-shell)
- PARALLAX's current behaviour: the sample briefs work without a key because answers are cached. New briefs need a JevStation or TypeSafe key, otherwise the API returns 503. The README tells users to bring their own keys. The Render free plan has no persistent disk, so projects reset when the service restarts. — [the-estimator README](https://github.com/mapleleaflatte03/the-estimator)
- EstimateOS deployed a public Streamlit Community Cloud app and ships an offline heuristic or mock extractor that works without tokens. — [EstimateOS README](https://raw.githubusercontent.com/Thomas-DataLab/estimate-os/main/README.md); [Tools manifest](https://raw.githubusercontent.com/Thomas-DataLab/estimate-os/main/docs/06_TOOLS_AND_SKILLS_MANIFEST.md)

### Inferences
- **Risk for PARALLAX:** a judge who pastes a new brief into the live app with no key, or after the pooled credits run out, gets a 503. That could read as "doesn't run" and would also cost points under Product quality. Ways to reduce this: a server-side key with enough credits for the review window (19–22 Oct) plus rate limits; or a clearly labelled reduced mode that uses rules only; or at least a clear in-app message and preloaded sample briefs that show the full loop.
- Review happens between 19 Oct and 20 Oct, and the demo is on 22 Oct. The app must stay up, and its stored state should survive restarts during that time. The Render free plan's lack of persistence and its cold starts are a risk to the "learning over time" demo.

### Gaps
- The "published event guide" mentioned by the site's agent was not found, so any rules about keys or demos it contains are unknown.
- It is not known whether judges review entries alone (asynchronously) or watch builders run the app.

## Any public information on other submissions, leaderboards, or past winners?

### Takeaway
This is the first edition ("No. 01 · October 2026"), so there are no past winners. There is no public leaderboard. One competing Estimator submission is public: **EstimateOS** by Pham Nguyen Minh Tu (Thomas-DataLab). It has a live Streamlit app and is tailored to Anduin's private-markets domain.

### Cited Findings
- The event page labels the event "No. 01 · October 2026" and "An Anduin build fest", which makes it the first edition. — [Event page](https://cybernetics.anduin.tech/agent-in-the-shell)
- EstimateOS: "Built for the Agent in the Shell Hackathon (Anduin Cybernetics) · Challenge: The Estimator (Sales & Delivery)". Live demo: https://estimate-os-rbaaveipfjfeqnlstxznow.streamlit.app/. Stack: Python, Streamlit, SQLite/DuckDB, Pydantic, 11 pytest tests, MIT license. Indexed by Bing around 13 Oct 2026. — [EstimateOS README](https://raw.githubusercontent.com/Thomas-DataLab/estimate-os/main/README.md); [Bing RSS](https://www.bing.com/search?format=rss&q=%22Anduin+Cybernetics%22)
- EstimateOS approach: "LLM interprets ambiguity; the deterministic data system owns the numbers". It has a "Completeness Gate" (CRITICAL/HIGH/MEDIUM/LOW gaps with clarification questions that block commitment), 3-point PERT, an "Evidence Ledger", matching against similar historical cases, Bayesian calibration of segment multipliers from actuals, and MMRE/Pred(25) telemetry. — [EstimateOS README](https://raw.githubusercontent.com/Thomas-DataLab/estimate-os/main/README.md)
- EstimateOS sets its scenarios in Anduin's own domain (VC/PE fund onboarding, LPA/Side Letter digitization, fund-admin SFTP/API integration). It uses **14 seeded historical projects** that it describes as reflecting "real-world Anduin transactions" but which are invented. Its PRD aims for completion by 18 Oct 2026, 23:59 GMT+7, and it has three personas (Solutions Architect, Delivery Manager, Head of Cybernetics). — [EstimateOS PRD](https://raw.githubusercontent.com/Thomas-DataLab/estimate-os/main/docs/01_PRODUCT_REQUIREMENTS_DOCUMENT.md)
- A GitHub repository search for "agent in the shell" or "anduin estimator" found no other clearly related public repos. The results were dominated by unrelated "estimator" projects. — [GitHub API search](https://api.github.com/search/repositories?q=%22agent+in+the+shell%22+OR+anduin+estimator&per_page=50)

### Inferences
- The typical competing design (LLM extraction, then deterministic PERT, then calibration from actuals) is the same core idea as PARALLAX. PARALLAX could stand out on: (a) a **real public dataset with temporal holdout** (SiP, 10,022 tasks, MAE −10.4%, 82% P10–P90 coverage), where EstimateOS uses 14 seeded cases; (b) **measured** AI value on held-out labels; (c) checking that every quoted piece of evidence actually appears in the brief; (d) briefs in Vietnamese and English.
- What EstimateOS has that PARALLAX should match or beat: a working public app that needs no key, an executive dashboard showing error falling over time, and framing in Anduin's own domain (private markets). The rules say "made-up data", so domain framing is optional, but a sample brief in Anduin's domain could make the product feel more relevant to these judges.
- There are only 5–10 finalist seats across six challenges, so the Estimator may get only about one or two finalists. Standing out against the other Estimator entries matters.

### Gaps
- There is no list of participants or submissions, and no count of Estimator entrants.
- No information exists yet on results or winners, which are expected around 20–22 Oct 2026.
- The EstimateOS live app was not opened or tested in this research.
