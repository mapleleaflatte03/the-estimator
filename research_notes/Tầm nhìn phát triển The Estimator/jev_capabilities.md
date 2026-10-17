# Jev (TypeSafe "System One" decision model) and the JevStation reseller: technical reference for a software-estimation product

Research date: 2026-10-17. Primary sources: docs.typesafe.ai (vendor), typesafe.ai blog (vendor), jevstation.com (independent reseller, not affiliated with TypeSafe), Vercel AI SDK / AI Gateway pages, and independent evaluations (GitHub jev-benchmarks, a LessWrong pilot as summarized by JevStation). Field names in `code` are quoted exactly from the docs. Anything labelled **[inferred]** is my own reasoning, not documented.

---

## 1. Which question types exist besides `choice` and `noul`? Exact request/response formats

### Takeaway
There are **four** question types in total. **Choice**, **Score** and **Noul** are production types. **Box** (image bounding box) is experimental: it needs jev-1.14 and an opt-in header. There is **no** numeric, ranking, extraction, multi-label or free-text type. The docs build those from Choice, Score and Noul in code. The product currently doesn't use **Score**, which is the obvious missing type for estimation (an ordered rubric that returns a probability-weighted position plus a distribution).

### Cited Findings

**Overall request shape (TypeSafe direct)**
- Endpoint: `POST https://api.typesafe.ai/v1/systemone`, headers `Authorization: Bearer <API_KEY>`, `Content-Type: application/json`. Body fields: `state` (string | object | array, required), `model` (string, required; e.g. `"jev-latest"`), `questions` (map<string, Question>, required) — [API reference](https://docs.typesafe.ai/api.md)
- The question key "is not sent to the underlying model and is not used in inference". The docs say: "Write the complete question in `instructions`, even when the ID seems self-explanatory." — [API reference](https://docs.typesafe.ai/api.md); [Primitives](https://docs.typesafe.ai/primitives.md)
- Every question has `type` and `instructions`. `instructions` can be a string, an object or an array. In an object, put the question in one field and the data in the others, and refer to data fields by name in backticks (e.g. `"question": "Is the resume for the same person as \`potential_duplicate\`?"`) — [API reference](https://docs.typesafe.ai/api.md)
- Response: `{ "model": "jev-1.13.0", "answers": { "<id>": {...} }, "usage": { "input_tokens": int, "output_tokens": int } }` — [API reference](https://docs.typesafe.ai/api.md)

**Noul** (yes/no → probability)
- Request: `{"type": "noul", "instructions": ..., "criteria": {"true": ..., "false": ...}}`. `criteria` is optional, and `true`/`false` can each be a string, object or array — [API reference](https://docs.typesafe.ai/api.md)
- Answer: `{"type": "noul", "noul": 0.95}`. There is **no `confidence` field**. The docs say "the single `noul` value describes it completely". If you want a confidence-style number, compute `|2p − 1|` yourself — [Noul](https://docs.typesafe.ai/primitives/noul.md); [Confidence](https://docs.typesafe.ai/confidence.md)

**Choice** (one option from an unordered set)
- Request: `{"type": "choice", "instructions": ..., "criteria": {"<option>": "<description>" | object | array | null}}`. At most **255 options** per Choice. Use `null` when the option name is self-explanatory. Option names **and** descriptions are sent to the model — [API reference](https://docs.typesafe.ai/api.md); [Choice](https://docs.typesafe.ai/primitives/choice.md)
- Answer: `{"type": "choice", "choice": "billing", "probabilities": {"billing": 0.88, "technical": 0.12, "sales": 0.0}, "confidence": 0.81}`. Probabilities sum to 1 — [API reference](https://docs.typesafe.ai/api.md)
- Confidence formula: `(p_max − 1/n) / (1 − 1/n)`. Only the top probability counts. The docs also suggest two alternatives: the top probability itself, or the top-to-second ratio `p_max / p_second` — [Confidence](https://docs.typesafe.ai/confidence.md)

**Score** (ordered rubric → position)
- Request: `{"type": "score", "instructions": ..., "criteria": ["level 0 desc", "level 1 desc", ...]}`. This is an ordered array: at least 2 levels, and the API accepts up to **10**. Each entry can be a string, object or array — [API reference](https://docs.typesafe.ai/api.md); [Score](https://docs.typesafe.ai/primitives/score.md)
- Answer: `{"type": "score", "score": 1.05, "legend": {"0": "Calm", "1": "Frustrated", "2": "Very angry"}, "probabilities": {"0": 0.0, "1": 0.95, "2": 0.05}, "confidence": 0.92}`. `score` = Σ level × probability, so it can fall between levels — [API reference](https://docs.typesafe.ai/api.md)
- Score confidence uses an ordinal formula: `max(0, 1 − Σ p_i·|i−m| / MAD_unif)`. Probability on an adjacent level reduces confidence less than probability on a distant level — [Confidence](https://docs.typesafe.ai/confidence.md)
- "The model doesn't see a level's number or its neighbours". Levels made only of numbers (`["0","1","2"]`) performed badly (score 0.55, confidence 0.33) compared with descriptive levels (0.0, confidence 1.0) on the same input — [Score](https://docs.typesafe.ai/primitives/score.md)

**Box** (experimental; images)
- Request: `{"type": "box", "instructions": "the coffee mug in \`photo\`"}`, with no criteria. It requires the header `TypeSafe-Danger-Zone-Images: true` and model `jev-preview`/`jev-1.14.0`. Answer: `{"type": "box", "box": {"top","bottom","left","right"} (0–1 fractions), "confidence": 0.92}`. There is no "not found" answer, so pair it with a Noul — [Box](https://docs.typesafe.ai/primitives/box.md)
- Images go in a top-level `assets` map (`{"<ref>": {"type": "image", "format": "png|jpg|jpeg", "data_base64": ...}}`, or multipart `part`). A reference string can be placed in `state`, `instructions` or `criteria`. TypeSafe labels this "Dreamer-ready", not production-ready — [Images](https://docs.typesafe.ai/images.md)

**Types that do not exist (and the documented workarounds)**
- Docs list only Choice/Score/Noul (+Box): "`type`. One of `choice`, `score`, or `noul`" — [Primitives](https://docs.typesafe.ai/primitives.md)
- **Extraction**: "it is better to extract possible options using regex or a generative model and let `jev-1.13` pick the correct extraction" — [Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md). The worked recipe: a regex over-finds candidates, a Choice picks one (with a `none` escape), and code copies the value verbatim, so Jev "cannot invent a value or transpose a digit" — [Pre-parsed value extraction](https://docs.typesafe.ai/cookbooks/pre_parsed_value_extraction_cookbook.md)
- **Dates/numbers**: split them into closed-set Choices (month, day, year 1900–2050 + `none`/`out_of_range`) and do the arithmetic in code — [Date extraction cookbook](https://docs.typesafe.ai/cookbooks/date_extraction_cookbook.md)
- **Ranking**: one Noul per query–candidate pair, then sort by the value. On CLERC legal re-ranking this raised top‑1 from 5%→18% and top‑10 from 38%→62% — [Re-ranking cookbook](https://docs.typesafe.ai/cookbooks/rerank_typesafe.md); [Noul](https://docs.typesafe.ai/primitives/noul.md)
- **Multi-label**: one Noul per label ("For a checklist of conditions, ask many Noul questions in one request") — [Noul](https://docs.typesafe.ai/primitives/noul.md)
- **Counting**: iterate in code, ask one Noul per item, and sum — [Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md)
- **Deep taxonomies**: chain Choices level by level. Criteria values can be nested subtrees, and you can run a beam search over Choice probabilities — [Advanced: structure](https://docs.typesafe.ai/primitives/advanced.md)
- In the Vercel AI SDK the Noul equivalent is called `boolean`. The SDK question types are `choice`, `score`, `boolean`, `box` — [AI SDK experimental_decide](https://ai-sdk.dev/docs/reference/ai-sdk-core/decide)

**JevStation wrapper format (what the product calls today)**
- `POST https://jevstation.com/api/v1/systemone`, `Authorization: Bearer sk_…`. Same `state`/`questions` contract. It also accepts `question_set_id` (a saved set) instead of `questions` — [JevStation docs](https://jevstation.com/docs)
- The response is wrapped in an envelope: `{"code": 0, "message": "ok", "data": {"model", "answers", "usage", "credits": {"charged", "remaining"}, "latency_ms"}}`. `code` is −1 on error — [JevStation: How to get Jev](https://jevstation.com/get-jev)
- JevStation requires "Choice needs at least two options, Score at least two ordered levels" — [JevStation docs](https://jevstation.com/docs)

### Inferences
- **[inferred]** Score fits estimation very well: an ordered size scale (XS…XL, or Fibonacci buckets described by reference tasks) returns a full distribution and an ordinal confidence. The docs warn the levels must be **descriptive situations**, not bare numbers.
- **[inferred]** Because question IDs are never seen by the model, the product's answer-key naming has no effect on quality. All meaning has to sit in `instructions`, option names and descriptions.

### Gaps
- I found no documentation of the observed **answer-key normalisation (double underscores collapsed)**. TypeSafe says keys come back "under the same keys", so this is probably JevStation-side behaviour. Avoid `__` in keys, or map keys back defensively.
- No published JSON schema for `GET /api/v1/systemone` on JevStation beyond "returns your plan, remaining credits and rate limits".

---

## 2. Limits: questions per call, state size, latency, rate limits, pricing tiers, model versions and changelog

### Takeaway
On **TypeSafe direct** the number of questions is unlimited. What limits a call is context: **64k tokens per request / 32k per question**, or 262k with a long-context header, plus a 32 MiB body cap. Price is **$0.042 per million input tokens, output free**. On **JevStation** a call allows **≤12 questions** and **≤24,000 characters of state**, billed **1 credit** (≤5 questions and ≤8,000 chars) or **3 credits** (larger). The pinned model is jev-1.13.0, and jev-1.14.0 shipped on 2026‑10‑14.

### Cited Findings

**TypeSafe direct limits**
- "There is no limit on the number of questions in a request. What limits a request is its size" — [Primitives](https://docs.typesafe.ai/primitives.md)
- Context: per-request (`state` + all questions) is 64k, and per-question (`state` + any one question) is 32k, for both Jev 1.14 and 1.13. The header `TypeSafe-Danger-Zone-Long-Context: true` raises both to 262k at the same price, but it is "slower and less accurate" — [Models](https://docs.typesafe.ai/models.md)
- Request rules: body ≤ 32 MiB (413 above that); UTF‑8 without BOM; ≤ 64 nesting levels in each of `state`/`instructions`/`criteria`; finite numbers only. "Send identifiers and exact large quantities as strings." gzip/zstd compression is supported — [API reference](https://docs.typesafe.ai/api.md)
- Errors: 400 (rule broken, or `max_tokens_exceeded`), 401, 413, 415, 422 (validation), 429 (rate limit), 529 (overloaded). Retry 429/529 with exponential backoff — [API reference](https://docs.typesafe.ai/api.md)
- Rate limits are per organization, in tokens/s and requests/s, shown in the console. Higher limits require custom/enterprise plans — [Models](https://docs.typesafe.ai/models.md). JevStation says TypeSafe states "1,200 requests a minute and 250,000 tokens a second" and that limits "can change without notice" — [JevStation: How to get Jev](https://jevstation.com/get-jev) (secondhand; I did not find this figure on TypeSafe's own pages)
- Access to TypeSafe direct is via a waitlist, with no self-serve plans or free usage (per JevStation) — [JevStation pricing](https://jevstation.com/pricing)

**Pricing**
- $42 per billion tokens / $0.042 per million tokens, input only. "Output tokens are free" — [Models](https://docs.typesafe.ai/models.md)
- Measured token model (JevStation, 11 live calls): `input_tokens ≈ 260 + 0.163 × state_chars + 0.20 × question_chars`. That is 260 tokens of fixed overhead per call, about 6 chars/token for English state, and about 5 chars/token for question JSON. Measured costs range from $0.000012 (1 Noul, 1‑char state) to $0.000377 (12 full questions + 24k‑char state) — [What one Jev evaluation costs](https://jevstation.com/blog/what-a-jev-evaluation-costs)
- Vercel AI Gateway lists Jev at $0.04/M input, 32K context, with providers TypeSafe AI and DigitalOcean. Model slugs: `typesafe-ai/jev`, `typesafe-ai/jev-1.14.0`, `typesafe-ai/jev-1.13.0` — [Vercel AI Gateway: Jev](https://vercel.com/ai-gateway/models/jev)

**JevStation tiers**
- 1 credit = "state up to 8,000 characters and up to 5 questions". 3 credits = "up to 24,000 characters and up to 12 questions". Failed runs cost 0 and are refunded automatically. Max 12 questions per evaluation — [JevStation FAQ](https://jevstation.com/faq); [JevStation home](https://jevstation.com)
- Packs: 5,000 credits for $9.90 ($1.98 per 1k standard evaluations), or 12,000 for $15.90 ($1.33 per 1k). Credits are valid for 24 months. Sign-up gives 50 free credits valid for 30 days. No subscription — [JevStation pricing](https://jevstation.com/pricing)
- Error statuses: 401, 400/413, **402 out of credits**, 429, **502 evaluation failed (refunded)** — [JevStation: How to get Jev](https://jevstation.com/get-jev)
- Throughput is capped per account, and the cap rises with the pack you buy. `GET /api/v1/systemone` returns your limits for free — [JevStation: How to get Jev](https://jevstation.com/get-jev)
- Conflicting statements about the `model` field: the get-jev page says "The deployment pins the model version, so the model field in your request is ignored" — [How to get Jev](https://jevstation.com/get-jev). The docs page says `model` selects `jev` (default), `clef-flash` or `clef` (Cloudflare, 2× credits), and that other values such as `jev-latest` run Jev — [JevStation docs](https://jevstation.com/docs)
- Privacy-policy figures: the playground stores state "up to 8,000 characters" plus context "up to 2,000 characters" — [JevStation privacy](https://jevstation.com/privacy-policy)

**Latency**
- Vendor: "End-to-end response time is 70ms-500ms", measured from TypeSafe's West Coast laptops, with the service based on the US West Coast — [Introducing System One Models & Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev)
- Independent: p50 of 236–256 ms called from France (4–6 labels) and 246 ms for 72 labels — [jev-benchmarks](https://github.com/AbdelStark/jev-benchmarks). Pilot median 0.34 s — [Jev as a Judge](https://jevstation.com/blog/jev-as-a-judge). JevStation captured run: 0.89 s — [JevStation home](https://jevstation.com)
- Batching: 13 questions in one call is "12.2x cheaper and 10.0x faster" than 13 separate calls, "with no change in answers". The primitives page gives 11.5x/9.6x for the same comparison, so the docs are slightly inconsistent — [llms.txt index](https://docs.typesafe.ai/llms.txt); [Primitives](https://docs.typesafe.ai/primitives.md)

**Versions / changelog**
- Current models: `jev-1.14.0` (from 2026‑10‑14) and `jev-1.13.0`. Aliases: `jev-latest` → `jev-1.13.0`, `jev-preview` → `jev-1.14.0`. "If you have tuned confidence thresholds against one version, send that version's ID instead of the alias" — [Models](https://docs.typesafe.ai/models.md)
- The 1.14 release notes: "small, subtle improvements to everything… we expect the largest gain in multi-lingual support". `jev-latest` moves to 1.14 "in a week". The plan is 60 days' notice before 1.13 is deprecated (30 days for 1.14). It also announced images (1.13 "was multimodal all along"), the Box type (1.14 only), the long-context flag, and an opt-in to share queries for debugging — [Jev 1.14 blog](https://typesafe.ai/blog/jev-1-14)
- Public launch was 2026‑09‑15 — [Introducing System One Models & Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev). Older cookbooks reference `jev-1.12` — [Date extraction cookbook](https://docs.typesafe.ai/cookbooks/date_extraction_cookbook.md)
- `GET /v1/models` lists aliases with `name`, `description`, `release_date` — [Models](https://docs.typesafe.ai/models.md)
- Python SDK `typesafe-sdk` v0.7.5 (2026‑10‑14) adds Box, Image, and zstd by default. v0.7.0 added a `response_model` (pydantic). v0.6.0 changed `Score.criteria` to an ordered sequence — [Python SDK changelog](https://docs.typesafe.ai/sdk/python/changelog.md)

### Inferences
- **[inferred] Cost optimisation on JevStation:** the credit jump is non-linear. Two calls of ≤5 questions (2 credits) are cheaper than one call of 6–10 questions (3 credits), and latency is about the same if the calls run in parallel. One call of 11–12 questions (3 credits) costs the same as three 4-question calls. This is the opposite of TypeSafe direct, where batching is always cheaper. Batch to multiples of 5.
- **[inferred]** Since the observed model is `jev-1.13.0` and `jev-latest` should move to 1.14 around 2026‑10‑21, answers through JevStation may shift without notice. Log `data.model` per call and re-check thresholds after the switch.
- **[inferred]** For the product's scale (thousands of estimates), the cost is negligible either way. JevStation costs about $0.0013–0.002 per call versus about $0.00002 direct, roughly 70–100×, but in absolute terms this only matters at high volume.

### Gaps
- No published TypeSafe SLA or uptime figures. JevStation's terms explicitly give no uptime commitment.
- I could not verify JevStation's exact per-account rate limits (only "returns your current limits").
- TypeSafe's internal intelligence chart in the 1.14 blog could not be read as text.

---

## 3. Documented best practices: phrasing, state references, calibration claims, multilingual input, what not to use Jev for

### Takeaway
Ask **one atomic "snap judgment" per question**. Put all meaning in `instructions` and criteria, and describe Score levels as concrete situations. Reference parts of the state with backticked dot/index paths. Keep math, dates and counting in code. Filter the state down to what is relevant. Pin the model version, and tune thresholds on your own labelled data. English works best. Jev cannot generate text, and it is weak at numeric precision and indirection.

### Cited Findings

**Phrasing**
- "Ask for a judgment a knowledgeable person makes in a second given the right context." If a judgment depends on several factors, split it into separate questions and weight them in code ("Composite scoring") — [Primitives](https://docs.typesafe.ai/primitives.md)
- Noul: ask one condition per question, and phrase it so that high = yes. Avoid inverted phrasing such as "free of personal data". A statement works as well as a question. Add `true`/`false` criteria when the boundary is subtle — [Noul](https://docs.typesafe.ai/primitives/noul.md)
- Don't use a Noul for degree. "A Noul value of 0.5 means the model gives yes and no equal probability. It does not mean… a medium skill level." Use Score for degree — [Primitives](https://docs.typesafe.ai/primitives.md); [Noul](https://docs.typesafe.ai/primitives/noul.md)
- Score: "Describe situations, not degrees". Use as many levels as you can describe distinctly (≤10). Keep one dimension per Score. Give a rare extreme its own level. Structured levels (`what` + `examples`) can sharpen boundaries: a relevant example moved confidence from 0.35→0.96, while an unrelated example changed nothing. "Higher confidence does not establish which answer is correct" — [Score](https://docs.typesafe.ai/primitives/score.md)
- Choice: give the full option list (up to 255; "adding options costs a few tokens each") and add `other` / `none of the above`. When options get confused, use structured descriptions with `what` / `not_for` / `examples`. These field names are free-form, not reserved — [Choice](https://docs.typesafe.ai/primitives/choice.md); [Advanced: structure](https://docs.typesafe.ai/primitives/advanced.md)
- Speculative fan-out: ask every question you *might* need in one request and ignore the irrelevant answers. Make a second request only when the second question truly depends on the first answer — [Primitives](https://docs.typesafe.ai/primitives.md)

**State and references**
- State can be a string, object or array. "Use an object for most requests so each part of the state has a descriptive name" — [State](https://docs.typesafe.ai/concepts/state.md)
- Reference fields with dot/index paths in backticks, e.g. ``"Does `ticket.messages[0].text` request a refund?"`` — [Primitives](https://docs.typesafe.ai/primitives.md)
- Put per-question data inside the `instructions` object (e.g. a `potential_duplicate` record) rather than in the state. This lets one request compare a state against many records, one Noul per record — [Noul](https://docs.typesafe.ai/primitives/noul.md)
- "Accuracy falls as the state grows with content unrelated to the decision… Jev suffers from context rot." Filter first — [Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md). This sits alongside the claim that questions are isolated: "adding more questions does not create context-rot" — [Introduction](https://docs.typesafe.ai)

**Known failure modes (jev‑1.13)**, from [Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md):
1. Literal reading: "answers the question you wrote, not the one you meant".
2. Math and numbers: "Jev is not a calculator". It doesn't count reliably, and it handles numeric representations worse than semantic ones. **"Please do not use score outputs… to compute the exact magnitude of a number between two levels… score levels are weak in numerical calibration."**
3. Date and time comparison: extract the parts, then compare in code.
4. Indirection or multi-hop questions.
5. Large state full of irrelevant detail.
6. Adversarial content in the state "can move the answer".
7. Contradictory instructions and criteria.
8. **Choice option order**: "leans toward the option that comes first". Reorder to check consistency.
9. Generation: don't use Jev to produce text.
- A summary cites the jaggedness notes as showing "a Noul and its negation answering 0.72 and 0.47, and the same refund question getting 0.22 as a Noul but 0.01 as a Choice 'yes'", so thresholds don't transfer between wordings or types — [Jev as a Judge](https://jevstation.com/blog/jev-as-a-judge). I did not see these exact figures on the current jaggedness page, so treat them as secondhand.

**Calibration claims**
- RLCD = "Reinforcement learning for calibrated decisions". "Outcomes assigned a probability of 0.8 should occur about 80% of the time". "These rates describe groups of predictions, not a guarantee about any single answer" — [AI primer](https://docs.typesafe.ai/introduction/machine-learning-primer.md)
- Confidence "describes the model's answer, not a guarantee that the answer is correct" — [Score](https://docs.typesafe.ai/primitives/score.md). Thresholds should scale with risk. Start conservative and tune on your own data — [Confidence](https://docs.typesafe.ai/confidence.md)
- Jev is not fine-tuned per customer and the same weights serve everyone. You customise it through state, instructions and criteria, or by training a downstream classical model on Jev probabilities ("AutoResearch" cookbook) — [Models](https://docs.typesafe.ai/models.md)

**Multilingual**
- "English is the primary training language and where accuracy is currently best. Other languages, including CJK scripts, are handled but not equally well; test on your own content… pay close attention to Confidence" — [Models](https://docs.typesafe.ai/models.md)
- 1.14: "we expect the largest gain in multi-lingual support" — [Jev 1.14 blog](https://typesafe.ai/blog/jev-1-14)

**What not to use it for**
- Jev is not a chat or code LLM, and it can't power a coding agent — [Jev with coding agents](https://docs.typesafe.ai/introduction/coding-agents.md)
- "It is also a poor fit when you cannot enumerate the answer space in advance" — [JevStation FAQ](https://jevstation.com/faq)
- "Avoid… asking the model something code can compute exactly; hiding several judgments inside one question; System Two tasks; giving it more context in `state` than the question needs" — [Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md)

### Inferences
- **[inferred]** For an estimation product: never ask Jev for "how many hours". Ask it for the *drivers* (Scores and Nouls on complexity, uncertainty, integration count bucket and so on) and compute hours in code from historical data. This follows the composite-scoring pattern and the "keep math in code" rule.
- **[inferred]** If the product's inputs are Vietnamese (the project folder suggests a Vietnamese team), it should either test accuracy on Vietnamese input specifically, or keep instructions and criteria in English while the state stays in the original language. Moving to `jev-1.14.0` may help. Both need checking against labelled data.

### Gaps
- TypeSafe publishes no official calibration curve or ECE numbers. Its own "workflow evals" compare against reference models, not ground truth.
- No documented guidance on mixing languages between instructions and state.

---

## 4. Official API vs Vercel AI Gateway vs OpenRouter vs JevStation: differences, terms, data handling

### Takeaway
All four routes reach the same model. **TypeSafe direct** is cheapest and gives version control, but it's behind a waitlist. It offers a DPA, no training on customer data, and zero data retention (ZDR) for enterprise customers. **Vercel AI Gateway** and **OpenRouter** expose TypeSafe-compatible endpoints at list price. **JevStation** is an independent reseller with credit packs, a 12-question/24k-char cap and a response envelope. It stores evaluations until you delete them, forwards content to the provider, and has a weaker legal posture.

### Cited Findings
- TypeSafe data handling: "Jev is not trained on customer requests or responses". The legal page links a Data Processing Agreement, a Master Customer Agreement and a Privacy Policy. "We also offer zero data retention (ZDR) for enterprise customers" — [Models](https://docs.typesafe.ai/models.md); [Legal](https://docs.typesafe.ai/legal.md)
- 1.14 added an *opt-in* for TypeSafe to see queries for debugging: "We will still not train on your queries" — [Jev 1.14 blog](https://typesafe.ai/blog/jev-1-14)
- Vercel AI Gateway: the Python SDK can point `base_url="https://ai-gateway.vercel.sh/typesafe"` with `model="typesafe-ai/jev"` and an `AI_GATEWAY_API_KEY` — [Python SDK basic usage](https://docs.typesafe.ai/sdk/python/usage/basic.md). The AI SDK's `experimental_decide({ model: 'typesafe-ai/jev', state, questions })` uses question types `choice | score | boolean | box`. "TypeSafe AI accepts text and JSON state only" through it, and partial results aren't supported — [AI SDK Decisions](https://ai-sdk.dev/docs/ai-sdk-core/decisions); [experimental_decide reference](https://ai-sdk.dev/docs/reference/ai-sdk-core/decide). "Your use is subject to TypeSafe AI's Terms & Privacy Policies" — [Vercel AI Gateway: Jev](https://vercel.com/ai-gateway/models/jev)
- OpenRouter: `base_url="https://openrouter.ai/api"`, `model="~typesafe/jev-latest"` — [Python SDK basic usage](https://docs.typesafe.ai/sdk/python/usage/basic.md). OpenRouter charges the same list price plus a fee when you buy credits — [JevStation pricing](https://jevstation.com/pricing)
- JevStation describes itself this way: "JevStation is independent… we are not affiliated with" TypeSafe or Cloudflare. One key covers Jev, Cloudflare Clef/Clef-flash, Perplexity Decider and OpenAI Luna Decisions — [JevStation home](https://jevstation.com)
- JevStation privacy: evaluation content (state ≤8k chars, context ≤2k, questions, answers) is stored against your account "until you delete it". It is transmitted to "TypeSafe's Jev API, or a self-hosted or OpenAI-compatible gateway the operator has set up". "We do not use your evaluation content to train models, and we do not sell it." Optional analytics, ads and chat tools (GA, AdSense, Crisp…) may load on the site — [JevStation privacy](https://jevstation.com/privacy-policy)
- JevStation terms: users must not "submit regulated, confidential, or personal data you are not permitted to send to such a provider". No reselling without permission. No automated decisions about people in regulated areas (credit, employment…) without legal safeguards. "Model versions and provider endpoints can change, and the same state and questions may produce different answers". No uptime commitment. Liability is capped at the greater of 12 months' fees or USD 100. Credits have no cash value and are non-refundable — [JevStation terms](https://jevstation.com/terms-of-service)
- JevStation extras: MCP server at `https://jevstation.com/api/mcp` (tools `jev_decide`, `jev_run_question_set`, …), saved question sets (`question_set_id`), agent skills, batch and spreadsheet tools — [JevStation docs](https://jevstation.com/docs)
- LangChain integrations `langchain-typesafe` / `@langchain/typesafe` exist for TypeSafe direct — [JevStation: How to get Jev](https://jevstation.com/get-jev)

### Inferences
- **[inferred]** For a commercial estimation product handling client specs, which may be confidential: JevStation's terms ("do not submit confidential… data you are not permitted to send", storage until deletion, possibly an operator-configured gateway, no DPA, resale prohibited without permission) are a real risk. Moving to TypeSafe direct (DPA, ZDR on enterprise) or Vercel AI Gateway (same request contract and `typesafe-sdk` compatibility, so migration is mostly a base-URL swap) is the safer path to production. The JevStation `data` envelope must be unwrapped differently.
- **[inferred]** If the product resells estimation built on JevStation, check the "resell, sublicense, or provide the Service to third parties" clause.

### Gaps
- I didn't fetch the full text of TypeSafe's DPA, MCA or Privacy Policy (typesafe.ai/legal/*), so retention periods for non-ZDR customers are unconfirmed.
- Vercel's own TypeSafe-compatible API page (`vercel.com/docs/ai-gateway/sdks-and-apis/typesafe`) wasn't fetched. One guessed Vercel docs URL returned 404.

---

## 5. Published evaluations and benchmarks of Jev's calibration and accuracy

### Takeaway
The evidence is thin and mixed. The vendor's own evals are reference-model comparisons, not ground truth. Independent pilots show strong discrimination: AUROC around 0.97 as a backdoor monitor, and +13–29 accuracy points over GLiNER2.5 on 2 of 3 classification sets. They also show high run-to-run stability (SD ≈ 0.01). But calibration is inconsistent: Jev is under-confident on one task and badly over-confident on emotion classification. There is no software-estimation benchmark.

### Cited Findings
- **jev-benchmarks** (independent, pre-registered, 300 examples, jev-1.13.0, zero-shot single-label vs GLiNER2.5):
  - AG News (4 labels): accuracy 0.910 vs 0.700. Coverage at ≤5% error: 0.830 vs 0.240.
  - Banking77 (72 labels): 0.870 vs 0.610, coverage 0.860 vs 0.270.
  - DAIR Emotion (6 labels): 0.480 vs 0.440, which is unresolved. Jev is "substantially worse calibrated: Brier 0.846 versus 0.668, NLL 5.588 versus 1.381, and zero probability on the true label for 16% of examples".
  - The authors caution "300-example pilot, not a leaderboard" — [jev-benchmarks README](https://github.com/AbdelStark/jev-benchmarks)
- **Backdoor-monitor pilot** (Venkat T, LessWrong, 2026‑09‑19, as summarised by JevStation): one Noul, jev-1.13.0, 600 backdoors vs 600+600 honest solutions.
  - AUROC 0.976 (LLM-written honest code) / 0.970 (human-written). It caught 89.5% / 87.8% of backdoors at 2% FPR. A length-only baseline scored AUROC 0.674.
  - Repeat-call SD was 0.008 (p90 0.019).
  - Prompt-injection comments let ≤3.7% of backdoors evade, but they pushed honest code from 1.3%→29% flagged.
  - With best-of-N attacker probing, about a third got through.
  - Edits to existing logic were caught only 71.9% of the time, versus 97.3% for added branches.
  - "markedly under-confident": the raw number "is a ranking, not a probability".
  - A Choice over line numbers put the trigger line in the top 3 picks 96.7% of the time — [Jev as a Judge](https://jevstation.com/blog/jev-as-a-judge); original: [LessWrong post](https://www.lesswrong.com/posts/d7pQicW8EhpPBDRqz/a-non-generative-model-as-a-trusted-monitor-for-ai-control)
- **Vendor self-consistency cookbook**: 14 Nouls × 15 runs on an insurance claim. Jev's mean per-question probability SD was 0.0102, "below all LLM probability conditions here" (claude-haiku-4-5, gpt-5.4-mini, gpt-5.5, claude-opus-4-8). One borderline answer still ranged 0.43–0.53 across runs, crossing a 0.5 threshold — [Self-consistency: nouls](https://docs.typesafe.ai/cookbooks/consistency_noul_cookbook.md)
- **Vendor launch claims**: "similar levels of intelligence on System One tasks compared to existing LLMs, while being two orders of magnitude faster". The "workflow evals" use the largest external models (Astra, Fable) as reference probabilities, not ground truth. The headline is "193.6x Faster, 444.6x Cheaper… based on workflows for System One tasks" — [Introducing System One Models & Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev); [typesafe.ai](https://typesafe.ai)
- **Vendor 1.14 blog**: "we dislike public benchmarks". The internal chart compares only open-weight models and is "likely biased towards our models" — [Jev 1.14 blog](https://typesafe.ai/blog/jev-1-14)
- **Re-ranking cookbook** (vendor): CLERC legal, 40 queries, top-1 5%→18% and top-10 38%→62% over BM25 — [Re-ranking](https://docs.typesafe.ai/cookbooks/rerank_typesafe.md)

### Inferences
- **[inferred]** Jev's probabilities look reliable as **rankings and stable signals** (high AUROC, low run-to-run variance), but not as calibrated absolute probabilities on every task. The estimation product should calibrate thresholds, or fit a simple isotonic/Platt mapping, on its own labelled history before treating `noul`/`confidence` as probabilities.
- **[inferred]** The emotion-classification failure (fuzzy, overlapping categories) is the relevant warning for estimation. Labels like "medium vs large" overlap similarly, so Score levels need very distinct, example-anchored descriptions.

### Gaps
- No independent evaluation of Jev on estimation, requirements analysis or effort prediction.
- No independent evaluation of jev-1.14.0, and none on non-English input.
- I didn't read the full LessWrong post directly; its figures are taken from JevStation's summary, which links to it.

---

## 6. Ideas: pairwise comparisons (relative sizing), ambiguity detection, quantity extraction, ranking clarification questions

### Takeaway
Each idea maps onto documented patterns: structured `instructions` objects for pairs, Noul-per-candidate for ranking, regex + Choice for extraction, and confidence/self-consistency for ambiguity. Everything in this section is **[inferred]** design advice built on cited mechanics. None of it is a documented TypeSafe recipe for estimation.

### Cited Findings (mechanics the ideas rely on)
- Per-question data can live in the `instructions` object, and many such questions fit in one request (one Noul per candidate record) — [Noul](https://docs.typesafe.ai/primitives/noul.md); [API reference](https://docs.typesafe.ai/api.md)
- Noul-per-pair, sorted by value, is the documented re-ranking method — [Re-ranking](https://docs.typesafe.ai/cookbooks/rerank_typesafe.md)
- Choice option-order bias exists. The docs say to reorder options and check consistency — [Jev 1.13 jaggedness](https://docs.typesafe.ai/model-jaggedness/jev-1.13.md)
- Low Score confidence "usually means… the levels overlap for this state, the question is measuring more than one thing, or the state doesn't say enough to place it" — [Score](https://docs.typesafe.ai/primitives/score.md)
- A two-request flow is legitimate when the second request needs the first answer, e.g. to change the state — [Primitives](https://docs.typesafe.ai/primitives.md)
- Regex candidates + Choice `pick` + `none` escape for verbatim values. Date parts as closed-set Choices — [Pre-parsed extraction](https://docs.typesafe.ai/cookbooks/pre_parsed_value_extraction_cookbook.md); [Date extraction](https://docs.typesafe.ai/cookbooks/date_extraction_cookbook.md)
- The AutoResearch cookbook turns free text into numeric features (Jev questions) that feed a supervised CatBoost regressor — [llms.txt index](https://docs.typesafe.ai/llms.txt)

### Inferences (design ideas)
1. **Pairwise relative sizing.** State = `{"task_a": {...}, "task_b": {...}}`, or put the pair in an `instructions` object. Use a Choice: "Which task needs more engineering effort to complete?" with options `task_a`, `task_b`, `about_equal`, each described as a situation. Run it in **both orders**, (A,B) and (B,A), to cancel the first-option bias, and average. Feed the pairwise probabilities into a Bradley–Terry / Elo fit in code to get a relative size ordering, then anchor it to the team's historical hours. Alternative: compare one new task against *k* reference tasks with known actuals, one Noul per reference ("Does `new_task` need more effort than `reference`?"), all in one request. The crossover point gives a size bracket. That's the documented "one Noul per record" pattern.
2. **Anchored Score instead of bare numbers.** A Score with 5–7 levels, each a structured object `{"what": "...", "examples": ["<real past task, actual 3 days>", ...]}` drawn from the team's history. Don't interpolate hours from `score` (documented weakness). Use the distribution as an uncertainty band, e.g. P10/P90 levels mapped to historical hour ranges in code.
3. **Composite complexity drivers.** In one request, use separate Scores for technical novelty, integration surface, data migration, UI breadth and test burden, plus Nouls for specific risk flags ("mentions a third-party API", "requires auth changes"). Weight them in code or train a regressor on them (AutoResearch pattern). Per the JevStation pricing note above, pack them in groups of ≤5 questions per call to stay at 1 credit each.
4. **Ambiguity detection.** (a) Explicit Nouls per ambiguity type: "Does `requirement` state acceptance criteria?", "Does `requirement` specify expected data volume or users?", "Does `requirement` name the systems it integrates with?" (b) Implicit: low `confidence` on the sizing Score or Choice is itself a signal that the state "doesn't say enough to place it". (c) Disagreement: flag tasks where pairwise A/B and B/A results disagree, or where the Score splits across non-adjacent levels (Score confidence near 0).
5. **Extracting quantities** (screens, endpoints, user counts, deadlines). Regex or LLM over-finds candidate spans. A Choice picks the one matching "number of distinct screens" with a `none` option. Code parses the number. For magnitudes with no exact span, use a Score of buckets ("<10 users", "10–1,000", …), treated only as a bucket. Dates: use the date-extraction cookbook's part-wise Choices and do the calendar math in code.
6. **Ranking clarification questions by value.** (a) Cheap version: one Noul per candidate question, in a structured `instructions` object `{"candidate_question": "...", "question": "Would the answer to \`candidate_question\` substantially change the effort needed for \`task\`?"}`. Sort by `noul`, as in the re-ranking pattern. (b) Value-of-information version (two rounds): for each candidate question and each plausible answer, add the hypothetical answer to the state and re-ask the sizing Score. Rank questions by how much they move or narrow the size distribution (expected variance reduction, computed in code). This costs more calls but uses Jev's distributions directly.
7. **Reliability hygiene.** Pin `jev-1.13.0` or `jev-1.14.0` when calling direct, and log `model` on every response. Add a throwaway unique field if you want repeat samples that bypass any caching (the independent pilot used this trick). Keep states narrowly filtered per question group. Calibrate thresholds on the product's own labelled estimates.

### Gaps
- None of these estimation patterns has been validated publicly. Each needs an offline evaluation against the product's historical actuals before release.
- It's unknown whether JevStation caches identical requests. The vendor cookbook adds a `uid` field "to defeat caching", which suggests caching may exist somewhere in the stack, but this isn't documented.
