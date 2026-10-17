# Market & Adoption: How Software Estimation Is Done in Practice, Existing Tools, and What Drives Adoption (focus: agencies / IT outsourcing incl. Vietnam)

> Research note, compiled 2026-10-17. **Method caveat:** The built-in web search did not work during this session. Searching was done through DuckDuckGo's HTML endpoint, which hit rate limits after about 3–5 queries per window. Because of that, coverage is narrower than planned, especially for Vietnam-specific presales practice and for Jira-plugin pricing. Every claim below comes from a fetched page or a search-result snippet; the snippet-only ones are marked "(snippet)". Many tool sources are vendor-written and biased; they are flagged as such.

## 1. Typical presales estimation workflow in agencies / IT outsourcing (who, how long, methods, contract types)

### Takeaway
At agencies, presales estimation is usually a hand-off chain. An account manager runs discovery, then a BA or senior engineer breaks the work down (epics → stories/tasks) in a spreadsheet template, a senior reviews it, and a proposal is built. The spreadsheet → document → Jira re-entry at each step is the main inefficiency vendors now target. Fixed-price bids add a 15–40% risk buffer on top of the estimate. Many vendors, including Vietnamese ones, push clients toward T&M, T&M with a cap, or dedicated teams/ODC when scope is unclear.

### Cited Findings
**Workflow and roles (practitioner accounts)**
- At Purrweb (a mobile/web agency), presales starts with a ticket. The account manager runs video calls about client goals, then writes a standardized "presale summary": client background, desired functionality, competitor references, budget expectations, attached materials. A business analyst then estimates. Presales tickets have their own Slack channel and due dates. (Published 12 Mar 2021, updated 20 Nov 2025) — [Purrweb](https://www.purrweb.com/blog/presales-and-project-estimation-process-how-to-avoid-mistakes/)
- Purrweb's old spreadsheet process had several problems. It kept no work history: a client returning 6 months later found that nobody remembered what had been estimated. Each person filled the spreadsheet differently. It also routinely left out project initiation, integrations, code review, design iterations, QA and PM hours. They switched to one unified template and decompose from general to specific: epics → user stories ("As a <user>, I can <action>"), with roughly one story per estimable task. — [Purrweb](https://www.purrweb.com/blog/presales-and-project-estimation-process-how-to-avoid-mistakes/)
- Apropo (a vendor) describes the usual agency stack as fragmented: "Discovery lives in notes, estimation in a spreadsheet, the proposal in a document and delivery in Jira. Every rewrite costs time and creates room for commercial promises to drift." Its pitched workflow is Client brief → Scope & estimate (team review) → Interactive proposal (client) → Jira handoff (delivery) → compare estimate with delivery. (vendor page, 2026) — [Apropo presales](https://apropo.io/software-agency-presales)
- Testimonials on the Apropo page from named agency leaders (vendor-curated): "move from shared Excel files that always go missing to one centralized and structured place for estimation" (Łukasz Gawroński, Managing Director, Spyrosoft eCommerce); "estimate projects 3x faster… a single centralized source of truth about every estimate ever done" (Adam Polak, VP Technology, The Software House). — [Apropo presales](https://apropo.io/software-agency-presales)
- devtimate (a vendor) frames the before-state like this: "most agencies still estimated projects in spreadsheets. Senior developers spent hours guessing hours. Proposals took days." (10 Mar 2026, vendor blog) — [devtimate blog](https://devtimate.com/blog/best-ai-software-estimation-tools-compared/)
- Vendor-reported turnaround: a ScopeDesk testimonial attributed to GeekyAnts says the tool "cut our proposal turnaround from 5 days to 4 hours. Our close rate went up 30%" (vendor testimonial, unverified). — [ScopeDesk.ai](https://scopedesk.ai/)
- Galorath claims SEER + SEERai saves cost/estimation professionals 11 days per project on average and produces an initial cost-and-schedule baseline 63% faster (vendor marketing; the footnoted methodology was not visible). — [Galorath](https://galorath.com/)

**Methods**
- Practitioner guides list five main methods: analogous, bottom-up (WBS), parametric, three-point (PERT), and expert/agile techniques such as Planning Poker (snippet). — [Decode agency guide 2026](https://decode.agency/article/software-development-time-estimation/)
- An IT estimation guide describes the job as turning scope into person-days and budget using WBS, PERT and Planning Poker, and warns that without capacity planning (real availability) the estimate "stays theoretical" (snippet). — [SimpleWorkload 2026](https://www.simpleworkload.com/en/blog/project-estimation-workload-planning-guide)
- Another guide aimed at $120k–$500k engineering projects formats estimates as WBS + PERT math + risk multipliers (snippet). — [NextGen Coding Co.](https://www.nextgencodingcompany.com/insights/work-estimate-format-software-development)
- Function-point sizing is automated in ScopeMaster, which is certified by COSMIC and IFPUG for automated sizing from user stories (snippet). — [F6S listing](https://www.f6s.com/software/scopemaster); [ScopeMaster](https://www.scopemaster.com/)

**Estimates → contract types**
- MONA (a Vietnam-based outsourcing firm): "Fixed price… works only when scope is genuinely locked. The vendor absorbs the estimation risk by pricing in a 15–30% buffer." Their worked example: 1,000 estimated hours + 20% buffer → $36,000 flat quote. If the job overruns to 1,300 hours because the spec was incomplete, the client still owes $36,000 unless the work counts as a change request. MONA recommends T&M with a cap, or a dedicated retainer, for most outsourcing. It cites Vietnam outsourcing rates of $15–45+/hr by seniority. — [MONA / themona.global](https://themona.global/blog/fixed-price-vs-time-and-material/)
- "Agencies typically bake in a 20 to 40 percent risk buffer on fixed-price work" (snippet, 2026). — [ZTABS](https://ztabs.co/blog/fixed-price-vs-time-and-materials)
- "Fixed-price bids hide a 15% to 30% risk buffer you pay even when nothing goes wrong" (snippet). — [GMware](https://gmware.com/blog/fixed-price-vs-time-and-materials/)
- Ken Research's Vietnam IT outsourcing report breaks the market down by business model (T&M, Fixed Price, Staff Augmentation, Outcome-Based, Hybrid) and delivery model (ODC, Dedicated Teams, Project-Based, Managed Services, BOT). The actual shares are paywalled. It expects profit pools to move "from basic staff augmentation and fixed-scope coding toward managed cloud operations, cybersecurity, AI-enabled modernization…". (Jul 2026) — [Ken Research](https://www.kenresearch.com/industry-reports/vietnam-it-outsourcing-market)

**Vietnam market context**
- Ken Research: Vietnam IT outsourcing market was USD 810M in 2025, forecast to reach USD 1,679M by 2031 (12.92% CAGR). Named major players: FPT Software, CMC Global, TMA Solutions, NashTech, KMS Technology. "Japanese-language capability" and "AI-enabled productivity" are listed as differentiators. — [Ken Research](https://www.kenresearch.com/industry-reports/vietnam-it-outsourcing-market)
- Dirox, citing Statista-type figures: Vietnam IT outsourcing revenue was US$0.7B in 2024, projected at US$1.28B by 2028 (17% CAGR). Main demand comes from Europe, North America, Japan and South Korea. Japan is cited as facing a 600,000 IT-engineer shortfall by 2030. — [Dirox 2025](https://dirox.com/blog/vietnam-it-outsourcing-2025-market-reports-trends)
- Mordor Intelligence: IT outsourcing was 39.05% of the Vietnam IT services market in 2025, mostly application maintenance and product engineering for Japanese and other clients (snippet). — [Mordor Intelligence](https://www.mordorintelligence.com/industry-reports/vietnam-it-services-market)
- Note the conflicting market-size figures (US$0.7B in 2024 vs US$810M in 2025). They come from different analyst definitions.
- TopDev publishes a "Vietnam IT Market Report 2024–2025" (salary and talent landscape). — [TopDev reports page](https://topdev.vn/page/bao-cao-it-viet-nam); [PDF mirror](https://employerbranding.vn/wp-content/uploads/2025/01/VIETNAM-IT-TECH-TALENT-LANDSCAPE-2024-2025.pdf)

### Inferences
- The decision-makers who buy an estimation tool at agencies are the presales or BA lead, the delivery director and the CEO/COO. The everyday users are BAs and senior engineers. The product has to fit a "ticket → summary → breakdown → senior review → proposal" chain and keep the full history.
- The workflow already uses a "presale summary" and an epics → stories breakdown. An AI that turns a brief into a WBS with evidence quotes and clarification questions maps directly onto the BA's main manual task.
- Since buffers of 15–40% are applied to fixed-price bids by rule of thumb, a calibrated Monte Carlo range (P50/P80/P90) gives a defensible, data-backed way to size that buffer. That is a strong commercial selling point for agencies that bid fixed-price.
- Vietnamese vendors serve Japan, US/EU, Korea and Australia. Bilingual (VI/EN) briefs plus Japanese-market conventions (detailed specs and change-request discipline) are likely to matter. This is an inference; no source confirms Japanese estimation norms for Vietnamese firms.

### Gaps
- I found no public, citable description of the internal presales estimation process at FPT Software, NashTech, KMS, CMC or TMA: who estimates, SLA for turnaround, or methods used. Searches were rate-limited. This needs interviews or job-description analysis (e.g. "Presales Engineer" / "Solution Architect" postings on ITviec/TopDev).
- I found no survey-grade statistic on how long agency presales estimates take (hours per RFP). The only figures are vendor testimonials ("5 days → 4 hours", "3x faster", "11 days saved").
- I found no source on the split of fixed-price vs T&M contracts in Vietnam; Ken Research has the segmentation but it is paywalled.
- Usage rates of function points or COSMIC in Vietnamese or Japanese offshore contracts were not found.

## 2. Pain points and the cost of bad estimates

### Takeaway
Bad estimation and unclear requirements are well documented as main causes of overrun. The most-cited figures are Standish CHAOS 2020 (31% successful / 50% challenged / 19% failed) and McKinsey–Oxford (large IT projects run 45% over budget on average). Both are old: 2020 and 2012. Smaller projects do much better, and agency projects are mostly small or medium.

### Cited Findings
- Standish CHAOS 2020 ("Beyond Infinity"): about 31% successful, 50% challenged (late, over budget, or reduced scope), 19% failed. Successful means on time, on budget, with the agreed features. No CHAOS report was published for 2021–2026, so 2020 is still the latest. The full report is paywalled; the figures come from secondary sources. — [BudgetOverrun.com – CHAOS](https://budgetoverrun.com/studies/standish-chaos-report); [CHAOS by year](https://budgetoverrun.com/studies/chaos-report-by-year)
- CHAOS 2015 results by project size (FY2011–2015): Grand 6% successful / 43% failed; Large 11% / 30%; Medium 12% / 26%; Moderate 24% / 12%; Small 61% / 7%. Agile beats waterfall at 39% vs 11% success. — [BudgetOverrun.com – CHAOS](https://budgetoverrun.com/studies/standish-chaos-report)
- McKinsey & University of Oxford (5,400 IT projects with budgets above $15M): large IT projects run on average 45% over budget and 7% over time, and deliver 56% less value than predicted. 17% go badly enough to threaten the company's existence. Software projects carry the highest risk of cost and schedule overrun. (2012) — [McKinsey PDF](https://www.mckinsey.com/~/media/McKinsey/Business%20Functions/McKinsey%20Digital/Our%20Insights/Delivering%20large%20scale%20IT%20projects%20on%20time%20on%20budget%20and%20on%20value/Delivering%20large%20scale%20IT%20projects%20on%20time%20on%20budget%20and%20on%20value.pdf)
- Flyvbjerg & Gardner, *How Big Things Get Done* (2023): 18% of IT projects exceed budget by more than 50%, and those average a 447% overrun (fat-tail risk). — [BudgetOverrun.com – IT projects](https://budgetoverrun.com/it-projects)
- Overrun causes specific to IT: requirements volatility ("the most common IT overrun cause"; small changes add up until scope doubles); integration with legacy systems and third-party APIs "consistently 3–5x harder than estimated"; informal scope additions that leave systems about 40% larger than specified by go-live; offshore and vendor communication gaps; and the "90% syndrome". This is a secondary compilation, and the 3–5x and 40% figures have no primary source there. — [BudgetOverrun.com – IT projects](https://budgetoverrun.com/it-projects)
- Agency-side failure example: a contractor who forgets to include social-media integration in the estimate ends up off schedule and over budget. Omitted categories (QA, PM, code review, integrations, initiation) are a recurring error. — [Purrweb](https://www.purrweb.com/blog/presales-and-project-estimation-process-how-to-avoid-mistakes/)
- Under fixed price, an incomplete spec turns directly into vendor loss (1,300 actual hours vs 1,000 estimated in MONA's example) unless the work can be billed as a change request. Under T&M the client bears the risk, and there is "no built-in ceiling". — [MONA](https://themona.global/blog/fixed-price-vs-time-and-material/)
- ScopeMaster (vendor) claims its tool finds 30–60% of all requirements issues, and says software failure costs "hundreds of billions of dollars per year, common causes are poor requirements and unreliable estimates". — [ScopeMaster](https://www.scopemaster.com/)

### Inferences
- For agencies the main pain is margin erosion on fixed-price work and slow turnaround that loses deals. Large-programme failure is less relevant. The product should be positioned on "win faster + protect margin". Generic CHAOS statistics play a smaller role.
- Detecting ambiguity in the brief and generating clarification questions directly targets the top cause, requirements volatility and unclear specs. It also produces the assumption list needed to enforce change requests later.
- A Monte Carlo range that is honest about fat tails, based on Flyvbjerg's evidence, works as a risk-communication device for clients. Agencies also need a single committed number for fixed-price bids, e.g. P80 + buffer.

### Gaps
- I found no recent (2022–2026) primary survey on estimation accuracy in agencies or outsourcing. PMI Pulse and State of Agile figures on scope creep could not be retrieved because of search rate limits.
- No Vietnam-specific data on overruns or fixed-price losses.

## 3. Existing tools, pricing and gaps

### Takeaway
The market splits into four groups. (a) Heavyweight parametric enterprise tools (SEER/Galorath, QSM SLIM, ScopeMaster) with opaque, sales-led pricing, aimed at defence, government and enterprise. (b) A fast-growing group of AI "brief → scope → proposal" tools for agencies (devtimate, Apropo, ScopeDesk, e2spec, CostGPT, Simple Estimate) at roughly $0–$500 per month. (c) PSA/resource tools for agencies (Forecast, Productive, Runn, Harvest Forecast) that track budget vs actuals but do not estimate from briefs. (d) Generic AI-in-Jira plugins. Gaps that recur across the field: no calibrated probabilistic ranges, weak links from evidence to source text, little closed-loop learning from actuals, and almost no Vietnamese-language support or on-prem option outside enterprise tiers.

### Cited Findings
**Enterprise / parametric**
- Galorath SEER (SEER-SEM for software) now has "SEERai": "Documents to WBS in minutes", agentic workflows, marketed as "secure and auditable", "not a chatbot or an AI black box", with "traceability". It draws on "1,000s of validated data points from hundreds of thousands of projects". Galorath runs an "Estimation-Centric AI Center" focused on "secure, explainable AI". Target industries: aerospace and defence, government, automotive, telecom. Pricing is not public (sales-led). — [Galorath](https://galorath.com/); [SEER-SEM](https://galorath.com/seer/solution/software-development/)
- QSM SLIM suite (SLIM-Estimate, SLIM-Collaborate, SLIM-MasterPlan, SLIM-Control) offers data-driven cost/schedule estimates "when very little is known about the scope", portfolio feasibility, and tracking. No public pricing was found. — [QSM](https://www.qsm.com/)
- ScopeMaster: automated functional sizing (COSMIC/IFPUG-certified) and requirements-quality analysis from user stories. Pricing is consumption-based (credits; one credit per user story analysed, with edits free for 30 days) or a subscription. No amounts are shown publicly; third-party sites treat it as sales-only. — [ScopeMaster pricing](https://www.scopemaster.com/pricing/); [xpay.sh](https://www.xpay.sh/saas-pricing/scopemaster/)

**AI estimators for agencies (brief → WBS → proposal)**
- devtimate: upload brief/PDF/Word → modules, tasks, roles (FE/BE/QA/DevOps), min–max hour ranges, assumptions and risks, with an AI agent for conversational refinement. Exports to Jira, Asana, Linear, Excel and branded PDF; uses rate cards and templates. **Pricing:** 14-day trial; **Pro $180/month** (up to 10 users, unlimited estimates); **Enterprise from $500/month** (unlimited users, **self-hosted deployment**). — [devtimate](https://devtimate.com/)
- Apropo: estimate editor (phases/modules/features/tasks), interactive web proposals where clients toggle modules and see live price and timeline, client behaviour tracking including mouse recordings, comments, Excel import, a reusable WBS component library, buffers, profitability analysis, Jira export, estimate comparisons, API, and an MCP connector for local AI agents. Marketed with "real-time estimate vs. reality reporting". **Pricing:** Free $0; Starter from $49/mo; Business tier (adds buffers, profitability, Jira; price not captured); Pro from $149/mo (timeline, custom proposal domain +$20, API). 30-day trial. Claims "500+ agencies". — [Apropo pricing](https://apropo.io/pricing); [Apropo presales](https://apropo.io/software-agency-presales)
- Apropo's own comparison (vendor-biased, 23 Jul 2026) says AI scope generation (steps 1–3: input, pattern matching, scope generation) is "rapidly becoming commodities". In their view the difference lies in human review, client collaboration and handoff to delivery: "A tool that… hands you a static PDF is solving 30% of the problem." The same piece concedes that accuracy "improves over time as you build a library of past estimates and actual hours" and that "No AI estimate should reach a client without human review". — [Apropo comparison](https://apropo.io/blog/best-ai-software-estimation-tools-compared/)
- devtimate's own comparison (vendor-biased, 10 Mar 2026) on competitors: CostGPT gives fast ballpark cost ranges with no task breakdown, roles, document upload or PM export. Simple Estimate has a free tier, hour ranges and no integrations. FlowHunt is a general AI workflow platform where estimation is a side feature. devtimate lists six buyer criteria: accuracy as ranges, not points ("32–52 hours with these assumptions" beats "40 hours"); document parsing; full editability; export/proposals; integrations (Jira/Asana/Linear/Excel); and pricing model (per estimate vs per seat vs flat). — [devtimate comparison](https://devtimate.com/blog/best-ai-software-estimation-tools-compared/)
- ScopeDesk.ai: paste a brief or upload files (Slack messages, Google Docs, PDFs) → PRD, feature breakdown, cost, timeline, team plan. Integrations: Notion, Linear, Jira, Trello, Monday, Lovable/v0 prototyping; HubSpot, Zoho and Salesforce CRM listed as "coming soon". Free tier plus monthly/annual plans (amounts not captured). It positions itself against spreadsheets, PandaDoc, Proposify and ChatPRD. — [ScopeDesk.ai](https://scopedesk.ai/)
- e2spec markets "AI-powered specs, team rate cards, and client-ready proposals" for agencies (snippet; the site would not connect). — [e2spec](https://e2spec.com/for/agencies.html)
- Screendragon sells agency estimates/scope software aimed at creative and marketing agencies: "move faster from brief to sign-off" (snippet). — [Screendragon](https://www.screendragon.com/products/agency-estimates-scopes/)

**PSA / resource and actuals tools**
- Forecast (forecast.app) has a single custom-priced subscription tier with no public price. Typical agency PSA alternatives listed with prices: Productive from $10/user/mo ("best for agency projects and budgeting"), Runn from $7/user/mo, Wrike from $10, Smartsheet from $9. (DPM, updated 6 Oct 2026) — [The Digital Project Manager](https://thedigitalprojectmanager.com/tools/forecast-pricing/); [ITQlick](https://www.itqlick.com/forecast/pricing)
- Harvest Forecast is Harvest's sister app; scheduled hours flow into Harvest so planned and tracked time can be compared (snippet). — [GetApp](https://www.getapp.com/operations-management-software/a/forecast/)

**Jira ecosystem**
- The Atlassian Marketplace has "EstiMate AI" ("data-driven time estimates for your tasks within Jira, with detailed reasoning… historical data"). Most other AI apps are general-purpose: document → tickets, summaries, release notes, and "Private AI mode" options such as Issue AI Analytics with Azure OpenAI/private models. Install counts and prices were not captured. — [Atlassian Marketplace API query](https://marketplace.atlassian.com/rest/2/addons?text=estimation%20AI&limit=15)

**Academic signal on LLM estimation**
- "Story Point Estimation Using LLMs" (arXiv 2603.06276, Mar/Apr 2026): across 4 LLMs and 16 projects, zero-shot LLMs predicted story points *better than supervised deep-learning models trained on 80% of the data*, and few-shot examples improved results further. This supports LLM priors plus calibration from a small amount of company data. — [arXiv](https://arxiv.org/abs/2603.06276)

### Inferences
- The price band for agency AI estimators is roughly $49–$180/month for SMB teams, with self-hosting starting around $500/month at devtimate. Enterprise parametric tools are custom-priced and out of reach for small and mid-sized Vietnamese agencies.
- Competitors already offer brief → WBS → hour ranges → branded proposal → Jira/Excel export. A new product cannot win on those features alone. The defensible features are:
  1. Evidence quotes linking each WBS item back to the brief (traceability; Galorath markets this for enterprise, but agency tools do not visibly offer it).
  2. Generated clarification questions as a first-class output.
  3. True Monte Carlo P-ranges instead of a simple min/max.
  4. Closed-loop calibration from actual hours. Apropo markets "estimate vs reality", but none of the tools shows learning that feeds back into future estimates.
  5. Vietnamese-language briefs and VND/USD/JPY outputs. No competitor found mentions Vietnamese.
- The arXiv result suggests a "learns from actuals" feature works even with a small calibration set. That fits agencies with few historical projects.

### Gaps
- SEER-SEM, SLIM and ScopeMaster prices are not public. Industry lore says five-figure annual licences, but I could not verify it.
- ScopeDesk and Apropo Business tier prices were not captured. e2spec could not be reached.
- I could not retrieve current details on Forecast.app's AI features or on "Foxly" and other Jira estimation apps.
- No Vietnamese-built estimation tools were found, possibly because of search limits. That should be checked before claiming there is none.
- No independent (non-vendor) benchmark of these tools' accuracy exists in the sources found.

## 4. Integrations that matter in practice

### Takeaway
To be used beyond the pilot, a tool must fit into tools teams already use: Excel/Google Sheets (still the agency default), Jira/Linear/Asana for handoff, and time-tracking systems (Jira worklogs via Tempo, Harvest, Toggl, Productive) for actuals. Every competitor lists Excel and Jira export. The missing link is the reverse flow: importing actuals and mapping them back to WBS items.

### Cited Findings
- Excel matters: Apropo's comparison lists "Excel import (real-world agencies use Excel)" as a differentiator and says "manual re-entry defeats the purpose of automation". All four tools in each vendor comparison offer Excel export. — [Apropo comparison](https://apropo.io/blog/best-ai-software-estimation-tools-compared/); [devtimate comparison](https://devtimate.com/blog/best-ai-software-estimation-tools-compared/)
- Delivery handoff: devtimate exports to Jira, Asana, Linear and Excel ("Push selected tasks to delivery tools… without copy-paste"). Apropo moves "the approved structure toward Jira with its commercial context intact, then compare the estimate with delivery". ScopeDesk pushes to Linear, Jira, Notion, Trello and Monday. — [devtimate](https://devtimate.com/); [Apropo presales](https://apropo.io/software-agency-presales); [ScopeDesk](https://scopedesk.ai/)
- Rate cards and roles: devtimate uses "templates and rate cards" and role-based tasks. e2spec markets "team rate cards". — [devtimate](https://devtimate.com/); [e2spec snippet](https://e2spec.com/for/agencies.html)
- Actuals sources:
  - Tempo Timesheets (Jira) groups worklogs by customer, contract or cost centre and classifies billable vs non-billable and CapEx vs OpEx "at logging", with "finance-ready hours". — [Tempo](https://www.tempo.io/products/timesheets)
  - Harvest integrates with Jira, GitHub, Asana, Trello and Slack (tracking time from issues and PRs, budget alerts), and its Forecast app feeds scheduled hours into Harvest. — [Harvest integrations](https://www.getharvest.com/integrations); [GetApp](https://www.getapp.com/operations-management-software/a/forecast/)
  - Toggl Track integrates with Jira, Asana and calendars. — [Toggl](https://toggl.com/track/integrations/)
- CRM linkage is starting to appear: ScopeDesk lists HubSpot, Zoho and Salesforce as "coming soon". — [ScopeDesk](https://scopedesk.ai/)
- Agent/API integration: Apropo offers a REST API and an MCP connector so "local AI agents" can create estimates. — [Apropo pricing](https://apropo.io/pricing)
- Proposal output: branded PDF (devtimate, Apropo), shareable web links, interactive proposals with scope toggles, and "Your own proposal domain (+$20)" at Apropo. — [Apropo pricing](https://apropo.io/pricing); [devtimate](https://devtimate.com/)

### Inferences
- Integration priorities for The Estimator, highest first:
  1. Excel/Google Sheets import and export that round-trips. The current CSV export is a start, but the export should match common agency template columns: module, task, role, min/likely/max, assumptions, evidence.
  2. Jira/Linear task push with stable IDs, so actuals can later be matched to WBS items.
  3. Actuals import from Jira worklogs/Tempo, Harvest, Toggl, ClickUp, or plain CSV timesheet upload. CSV upload is the lowest-friction option in Vietnam, where many firms use in-house timesheet systems (inference).
  4. Role rate cards with multi-currency (USD/JPY/EUR/AUD/VND), since Vietnamese vendors bill foreign clients.
  5. Proposal templates in Word/PDF with the company's branding.
- Without stable task IDs that survive the trip into Jira, "learn from actuals" will break in practice. Mapping actuals to estimate lines is the operational crux.
- MS Project export was not mentioned by any agency-focused tool found. It probably matters mainly for enterprise or government clients and for Japanese-style waterfall reporting (inference, unverified).

### Gaps
- No data on which time trackers Vietnamese outsourcing firms use: Jira/Tempo vs in-house tools vs Redmine/Backlog (Backlog is popular with Japanese clients). This needs a direct survey.
- Demand for multi-currency and MS Project export was not evidenced by any source found.

## 5. Trust and adoption factors (explainability, evidence, calibration, privacy, on-prem)

### Takeaway
Practitioners do not trust AI output by default. More developers distrust AI accuracy than trust it, and 81% have data security/privacy concerns about AI agents. Organisations restrict GenAI over data leakage. Adoption therefore depends on human-in-the-loop review, visible reasoning and evidence, ranges rather than single points, accuracy that measurably improves against actuals, and deployment options (self-hosted or private models) for confidential client briefs.

### Cited Findings
- Stack Overflow Developer Survey 2025:
  - 46% of developers actively distrust the accuracy of AI tools vs 33% who trust it. Only 3.1% "highly trust".
  - Experienced developers (10+ years) are the most sceptical: 2.6% highly trust, 20% highly distrust.
  - 87% are concerned about the accuracy of AI agents, and 81% about the security and privacy of data.
  - Favourable sentiment toward AI tools fell from 70%+ (2023/2024) to 60% (2025).
  — [Stack Overflow Survey 2025 – AI](https://survey.stackoverflow.co/2025/ai)
- Cisco 2024 Data Privacy Benchmark (25 Jan 2024): 27% of organisations had banned GenAI at least temporarily. 48% admit entering non-public company information into GenAI tools. 91% say they need to do more to reassure customers about how their data is used in AI. Over 90% believe GenAI needs new data and risk management techniques. Top concerns include threats to legal and IP rights. — [Cisco Newsroom](https://newsroom.cisco.com/c/r/newsroom/en/us/a/y2024/m01/organizations-ban-use-of-generative-ai-over-data-privacy-security-cisco-study.html)
- Enterprise estimation vendors market trust features explicitly. Galorath: SEERai is "not a chatbot or an AI black box", is "secure and auditable", uses "validated references" and offers "traceability". — [Galorath](https://galorath.com/)
- The Jira marketplace estimator "EstiMate AI" sells "time estimates… with detailed reasoning" based on historical data. Other apps offer a "Private AI mode" (Azure OpenAI or private models). — [Atlassian Marketplace](https://marketplace.atlassian.com/rest/2/addons?text=estimation%20AI&limit=15)
- Self-hosted deployment is offered at devtimate Enterprise (from $500/month). — [devtimate](https://devtimate.com/)
- Agency vendors agree on human review: "No AI estimate should reach a client without human review". Tools "can't account for team-specific velocity, technical debt… client relationship dynamics". Accuracy improves "as you build a library of past estimates and actual hours". — [Apropo comparison](https://apropo.io/blog/best-ai-software-estimation-tools-compared/)
- Ranges with assumptions are preferred over points ("32–52 hours with these assumptions"). Users want to edit everything: "If the tool locks you into its output, it is not ready for production use." — [devtimate comparison](https://devtimate.com/blog/best-ai-software-estimation-tools-compared/)
- Recent academic work points to explainability as the gap in ML estimators: "recent machine learning-based methods show promising accuracy, [but] they cannot explain or justify their estimates and lack the capability to interact with" practitioners. This is from an arXiv listing on an LLM multi-agent framework for agile effort estimation (2026). Note: the arXiv API returned this title and abstract for ID 2603.06276, while the abs page for that ID shows "Story Point Estimation Using LLMs", so the ID-to-title mapping is uncertain. — [arXiv 2603.06276](https://arxiv.org/abs/2603.06276)

### Inferences
- The trust features The Estimator already plans (evidence quotes, clarification questions, Monte Carlo ranges) match what sceptical senior engineers and enterprise buyers ask for. They should be shown prominently, e.g. a click-through from each WBS line to the source sentence in the brief.
- Calibration has to be visible to be trusted. A "your estimates vs actuals" dashboard (hit rate of P80, bias per module or role) is probably the strongest driver of continued use. It also gives the tool lock-in through accumulated data.
- Client briefs at outsourcing firms are usually under NDA. Japanese and European clients and the GDPR put a premium on processing guarantees: no training on data, region choice, PII redaction, and a self-hosted or local-LLM option for larger firms such as FPT, NashTech and KMS. The tiering could be SaaS for small agencies and a private deployment for large outsourcers, similar to devtimate's split.
- The Cisco statistic that 48% of organisations put non-public data into GenAI suggests staff already paste briefs into ChatGPT. A sanctioned, auditable tool can replace that "shadow AI" use, which is a selling angle toward IT and security leads.

### Gaps
- No 2022–2026 source specifically measures trust in AI-generated estimates among presales or BA staff, or client acceptance of AI-assisted proposals.
- No Vietnam-specific data on AI policies at outsourcing firms (e.g. whether FPT or NashTech ban external LLMs on client data), or on Vietnam's Personal Data Protection Decree 13/2023 as it applies to briefs. Not researched because of search limits.
- I found no evidence on whether clients accept probabilistic (Monte Carlo) ranges in proposals versus single fixed numbers.
