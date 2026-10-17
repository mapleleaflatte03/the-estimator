# Public datasets pairing software-work text with effort outcomes (for validating The Estimator)

Research date: 2026-10-17. Method: direct fetches of GitHub/Zenodo/figshare APIs, dataset READMEs, the arXiv/ACM papers, and Derek Jones' blog (WordPress API). The general web-search tool was down for this whole session, so the search for regional (Vietnam/Asia) data and for less-known datasets was limited. "UNVERIFIED" marks anything I could not confirm from a primary source.

**Quick ranking for the stated need (requirement text + estimate + actual, with dates):**
1. **SiP**: summary text + estimated hours + actual hours + dates. The product already uses it. **Its licence is non-commercial (NC) and no-derivatives (ND)**, as shown below.
2. **TAWOS v1.1**: title + description + story points + Jira `Timespent` (actual time logged) + changelog-derived time proxies + an "SP estimation date". Apache-2.0. Few issues have **both** story points and logged time.
3. **Public Jira Dataset (Montgomery et al.)**: raw Jira JSON with summary/description/`timeestimate`/`timespent`/dates for 2.7M issues. CC BY 4.0. You have to filter it yourself, and coverage of time-tracking fields is unknown.
4. **Itemlet (2026)**: 727k Jira issues, CC BY 4.0. Has summary (title only), logged hours, workratio (which lets you derive the original estimate), story points and dates. New and unreviewed.
5. **Deep-SE (Choetkiertikul)**: title + description + story points only (no actuals, no dates). Useful only for story-point prediction.
6. **CESAW / SEA Data Warehouse / Renzo / Project-22**: task-level estimate vs actual, but **no usable free text**.
7. **PROMISE classics** (NASA93, China, Maxwell, Kitchenham, Desharnais, COCOMO81, Albrecht): numbers only, at project level. No text.
8. **ISBSG**: commercial, paid, project-level metrics. No requirement text.

---

## Q1. TAWOS and the Choetkiertikul/Deep-SE story-point dataset: contents, size, licence, URLs

### Takeaway
TAWOS v1.1 is the richest open-licensed (Apache-2.0) source of Jira issue text with effort signals. It has 458,232 issues from 39 projects, with summary, description (split into text and code), story points, `Timespent`, sprints, changelogs and UTC dates. But only about 9.8k issues across 15 projects (v1.0) had logged time, and only 697 had both story points and `Timespent`. Several of the time-logging projects (Talendforge) were removed in v1.1. Deep-SE has 23,313 issues with title, description and story points only. It has no actual effort and no explicit dates (only creation order), and no licence is stated.

### Cited Findings
**TAWOS**
- Full name: "The Tawosi Agile Web-hosted Open-Source Issues dataset". Repo: https://github.com/SOLAR-group/TAWOS. Paper: Tawosi, Al-Subaihin, Moussa, Sarro, "A Versatile Dataset of Agile Open Source Software Projects", MSR 2022, doi 10.1145/3524842.3528029 — [TAWOS README](https://raw.githubusercontent.com/SOLAR-group/TAWOS/main/README.md)
- Download: figshare DOI 10.5522/04/21308124. Files are `TAWOS.sql.zip` (637,550,449 bytes, direct link https://ndownloader.figshare.com/files/37806375) and README.md. Licence on figshare: Apache 2.0. Published 2022-10-11 — [figshare API record 21308124](https://api.figshare.com/v2/articles/21308124)
- Format: MySQL 8.0.22 dump. Import with `mysql -u user -p db < file.sql` — [TAWOS README](https://raw.githubusercontent.com/SOLAR-group/TAWOS/main/README.md)
- Terms of use: "published to be used by researchers for research purposes only", and usage that may harm contributors or project owners is prohibited. Yet the README also states the dataset is shared under Apache License 2.0. This research-only wording conflicts with the permissive licence. PII is replaced by `<USER>`/`<EMAIL>` tags — [TAWOS README](https://raw.githubusercontent.com/SOLAR-group/TAWOS/main/README.md)
- Size: 458,232 issues from 39 projects across 12 public Jira repositories (Apache, Appcelerator, Atlassian, DNN, Hyperledger, Lsstcorp, Lyrasis, MongoDB, Moodle, Mulesoft, Sonatype, Spring). v1.0 had one more repository with 5 projects, removed in v1.1 because it left the public domain. The commented-out list shows these were the Talendforge projects TBD, TMDM, TDP, TDQ, TESB — [TAWOS README](https://raw.githubusercontent.com/SOLAR-group/TAWOS/main/README.md)
- Fields and tables:
  - Issue table: `Description`, `Description_Text`, `Description_Code`, `Story_Point`, `Resolution`, `Type`, `Resolution_Time_Minutes`, `In_Progress_Time`, `Total_Effort_Time`, an "SP Estimation Date" (when the story point was populated), `Title_Changed_After_Estimation`, `Description_Changed_After_Estimation`, and `Story_Point_Changed_After_Estimation`.
  - Other tables: Comment, Change_Log (with ChangeType), Issue_Link, Component, Version, Sprint (Start/End/Completion dates), User, Project, Repository.
  - All dates are converted to UTC.
  - Source: [TAWOS README](https://raw.githubusercontent.com/SOLAR-group/TAWOS/main/README.md)
- Jira `Timespent` (actual logged time): Tawosi et al. kept issues that were resolved and had `Timespent` ≥ 2 minutes, in projects with ≥100 such issues. This left **9,806 issues from 15 projects** (out of 184,534 total issues in those projects; 9,453 after further filtering). The projects were CWD, JSWCLOUD, JSWSERVER, JRASERVER, BAM, CLOV, FE, TIDOC, DM, NEXUS, TDQ, TDP, TMDM, TBD and TESB — [Tawosi et al. ESEM 2022, Table 1a](https://solar.cs.ucl.ac.uk/pdf/tawosi2022esem.pdf)
- Only **697 issues across 4 projects** (DM 128, TDQ 303, TMDM 104, MDL 162) had **both** story points and `Timespent` — [Tawosi et al. ESEM 2022, §4.2](https://solar.cs.ucl.ac.uk/pdf/tawosi2022esem.pdf)
- Developers rarely use Jira's time-logging fields: "usually the developers do not use this feature to log their work". The "In-Progress time" proxy tracked `Timespent` most closely, but all proxies have large absolute errors — [Tawosi et al. ESEM 2022](https://solar.cs.ucl.ac.uk/pdf/tawosi2022esem.pdf)
- Story points versus In-Progress time: mean Spearman ρ = 0.40 across 32 projects. Correlation was strong for only 7% of projects. 21 of 32 projects show underestimation of larger items — [Tawosi et al. ESEM 2022](https://solar.cs.ucl.ac.uk/pdf/tawosi2022esem.pdf)
- Replication data and scripts for the ESEM study: https://github.com/SOLAR-group/SPvsDevelopmentEffort — [README](https://raw.githubusercontent.com/SOLAR-group/SPvsDevelopmentEffort/main/README.md)

**Deep-SE (Choetkiertikul et al.)**
- Paper: "A deep learning model for estimating story points" (IEEE TSE 2018; arXiv 1609.00489). The dataset "contains 23,313 issues from 16 open source projects" — [arXiv abstract](http://arxiv.org/abs/1609.00489)
- Location: https://github.com/morakotch/datasets/tree/master/storypoint/IEEE%20TSE2018/dataset (per-project CSVs such as `bamboo.csv`, `mesos.csv`, `appceleratorstudio.csv`) — [GitHub contents API](https://api.github.com/repos/morakotch/datasets/contents/storypoint/IEEE%20TSE2018/dataset)
- Columns: `issuekey, title, description, storypoint` (4 columns only). Issues are sorted by creation time, but no timestamp column is included. Projects come from Apache, Appcelerator, Duraspace, Atlassian, Moodle, Lsstcorp, Mulesoft, Spring and Talendforge. The README says 16 CSV files but its table lists 15 — [dataset README](https://raw.githubusercontent.com/morakotch/datasets/master/storypoint/IEEE%20TSE2018/dataset/README.md)
- Some descriptions are `NULL` (e.g., BAM-932) — [bamboo.csv](https://raw.githubusercontent.com/morakotch/datasets/master/storypoint/IEEE%20TSE2018/dataset/bamboo.csv)
- Licence: the GitHub repo (a fork of `emaadmanzoor/datasets`) has **no licence declared** (`license: null`) — [GitHub API](https://api.github.com/repos/morakotch/datasets)
- Tawosi et al. performed a replication and extension of Deep-SE on a larger dataset — [arXiv 2201.05401](http://arxiv.org/abs/2201.05401v2)

### Inferences
- TAWOS is the best source for **text → story points**, with a clean temporal key (the SP estimation date) and flags for "description edited after estimation", which matter for avoiding leakage. For **text → actual hours**, its usable subset is small. For **estimate vs actual hours** on the same issue, almost nothing is usable, because Jira's `timeoriginalestimate` is not documented in the TAWOS README.
- v1.1 removed Talendforge. That repository supplied about 4.3k of the ~9.5k filtered `Timespent` issues in Table 1a (TDQ, TDP, TMDM, TBD, TESB). So the v1.1 `Timespent` subset is probably about half the v1.0 figure. Run `SELECT COUNT(*) ... WHERE Timespent IS NOT NULL` after import to confirm.
- Deep-SE's 23k issues largely overlap TAWOS projects (Mesos, Usergrid, Appcelerator, Atlassian, Moodle, DM, Mule, Spring XD). Treat it as a subset or older snapshot rather than independent validation data. Its missing licence makes commercial redistribution risky.
- Neither dataset is suitable for "overrun" labels unless you use TAWOS issues that have both an original estimate and `Timespent` (count unverified).

### Gaps
- I could not confirm that TAWOS has a `Timespent` column under exactly that name, or an `Original_Estimate`/`timeoriginalestimate` column. The README excerpt did not list all Issue columns, but the ESEM paper confirms `Timespent` values were obtained "from the TAWOS dataset". Check the ER diagram (`Entity_Relationship_Diagram_V1.png` in the repo) or the SQL schema.
- I could not find an exact count of v1.1 issues that have `Timespent`.

---

## Q2. Public Jira datasets (Montgomery et al. 2022 and others): do they include `timeoriginalestimate`/`timespent`? How many issues have both?

### Takeaway
The Public Jira Dataset (Montgomery, Lüders, Maalej, MSR 2022) is a CC BY 4.0 MongoDB dump of raw Jira API v2 issue JSON. It covers 16 repositories, 1,822 projects and 2.7M issues, including Apache (1.0M), RedHat, MongoDB, Qt, Spring and Hyperledger. Its documented fields include summary, description, `timeestimate`, `timespent`, created, resolutiondate and duedate. No published count exists of issues with both an original estimate and time spent; you have to compute it after import. Itemlet (2026) is a new CC BY 4.0 alternative in flat CSV/Parquet with logged hours and workratio, but it has summary only and no description.

### Cited Findings
**Public Jira Dataset (Montgomery et al.)**
- Zenodo record: "The Public Jira Dataset", latest version 2025-06-23 (record 15719919; concept DOI 10.5281/zenodo.5882881). Licence CC-BY-4.0. 16 public Jira repositories, 1,822 projects, 2.7M issues, 32M changes, 9M comments, 1M links. The data is anonymised with UUID4 masks for assignee, creator, reporter and comment authors — [Zenodo API](https://zenodo.org/api/records/15719919)
- Single file: `2025-06-23 ThePublicJiraDataset.zip`, 5,813,135,238 bytes (~5.8 GB) — [Zenodo API](https://zenodo.org/api/records/15719919)
- Per-repository issue counts: Apache 1,014,926; Hyperledger 28,146; IntelDAOS 9,474; JFrog 15,535; JIRA (Atlassian) 274,545; JiraEcosystem 41,866; MariaDB 31,229; Mindville 2,134; Mojang 420,819; MongoDB 137,172; Qt 148,579; RedHat 353,000; Sakai 50,550; SecondLife 1,867; Sonatype 87,284; Spring 69,156 — [Montgomery et al., Table 1](https://arxiv.org/abs/2201.08368)
- Documented issue fields: summary, description, comments, issuetype, project, components, labels, issuelinks, subtasks, fixVersions, status, priority, resolution, **timeestimate** ("Estimated amount of time required to resolve the issue"), **timespent** ("Amount of time spent working on this issue"), creator, reporter, assignee, votes, watches, created, updated, resolutiondate, duedate. The full changelog is included — [Montgomery et al., Fig. 1 and Table 2](https://arxiv.org/abs/2201.08368)
- Data was first downloaded in May 2021 and updated in January 2022 in the original paper. MariaDB and Mindville were frozen at May 2021. The dump is "whole unfiltered data" — [Montgomery et al.](https://arxiv.org/abs/2201.08368)
- The paper maps issue types to themes: Requirements 30%, Development 18%, Maintenance 51%, User Support 1%. This helps you select requirement-like issues (epics, stories, feature requests) — [Montgomery et al., §3.1](https://arxiv.org/abs/2201.08368)

**Itemlet dataset (2026)**
- Zenodo record 19411554, published 2026-04-04, CC BY 4.0. 727,282 Jira issues from 204 open-source projects in 19 domains, with 108 variables (60 raw from the Jira REST API, 48 derived). Sprint metadata covers 267,203 issues — [Zenodo API](https://zenodo.org/api/records/19411554)
- Files: `itemlet_dataset.csv` (438 MB), `itemlet_dataset.parquet` (108 MB), `data_dictionary.csv`, `project_summary.csv`, `project_domain.csv`, extraction notebook and config — [Zenodo API](https://zenodo.org/api/records/19411554)
- Effort-relevant columns:
  - `issue_summary` (title text)
  - `created` (42.6% null) and `resolutiondate`
  - `workratio`: "Ratio of time logged to original estimate; -1 = no estimate"
  - `worklog_total` (seconds) and `Total Time Logged (hours)`
  - `Worklog Count`
  - `story_points` (66.5% null)
  - `Cycle Time (hours)`
  - **No description field** in the data dictionary
  - Source: [Itemlet data_dictionary.csv](https://zenodo.org/api/records/19411554/files/data_dictionary.csv/content)
- Known issue: `Completion Time (hours)` was "identical to Cycle Time (hours) due to derivation error" in v1.0, corrected in v2.0. Many derived "effort" scores are hand-weighted composites, such as `effort_predictor_score` = weighted SP + cycle time + …, so they can leak the target — [Itemlet data_dictionary.csv](https://zenodo.org/api/records/19411554/files/data_dictionary.csv/content)

**Other**
- Ortu et al. (2015) released an earlier dataset of four Jira repositories ("The JIRA repository dataset: understanding social aspects of software development", PROMISE 2015) — [Montgomery et al., ref 16](https://arxiv.org/abs/2201.08368). UNVERIFIED: whether it includes time fields, and its download location.

### Inferences
- In Jira's API, `timeestimate` is the *remaining* estimate. `timeoriginalestimate` is a separate field. The paper documents `timeestimate` and `timespent`. Because the dump stores raw API JSON, `timeoriginalestimate` and `aggregatetimespent` are probably present wherever projects used time tracking, but this is UNVERIFIED and you need to check it with a MongoDB query, e.g. `{ "fields.timeoriginalestimate": {$gt:0}, "fields.timespent": {$gt:0} }`.
- From Tawosi's TAWOS findings, expect "both fields filled" to be a small minority concentrated in a few projects. In TAWOS these were Atlassian's own projects (JRASERVER, JSWSERVER, FE, BAM, CWD), Sonatype NEXUS, Appcelerator TIDOC and Talend. The Montgomery dump covers the JIRA (Atlassian), Sonatype and Spring repositories, so it is a reasonable place to look.
- Itemlet's `workratio` = timespent/originalestimate×100. So for issues with workratio > 0, original estimate ≈ `Total Time Logged` / (workratio/100). That gives estimate-vs-actual "overrun" labels with dates and title text. The data is new (2026), not peer-reviewed as far as I found, and descriptions are missing.

### Gaps
- I found no published count of issues with both `timeoriginalestimate` and `timespent` in the Montgomery dataset, Apache Jira, Spring Jira or Hyperledger Jira. This needs a local query. I could not search for papers reporting such counts because web search was unavailable.
- I did not verify whether the 2025 Zenodo version re-crawled the data after January 2022.

---

## Q3. CESAW, ISBSG, NASA93, Desharnais, China, Maxwell, Kitchenham, COCOMO81: text or numbers only? Licences and URLs

### Takeaway
None of these classic or industrial datasets contains requirement text usable by an NLP model.
- **CESAW** (61,817 TSP tasks from 45 projects) and its 2026 superset, the **SEA Data Warehouse** (679,904 tasks from 1,211 projects), have task-level estimates and actuals with timestamps, but no free-text descriptions.
- The PROMISE classics are small project-level numeric tables on Zenodo under CC BY 4.0.
- ISBSG is a paid, licensed commercial repository of project-level metrics.

### Cited Findings
**CESAW**
- Jones & Nichols, "The CESAW dataset: a conversation" (arXiv 2106.03679, 2021). 61,817 tasks performed on 45 projects using the Team Software Process (TSP). Five projects were safety-critical (28,899 tasks). The data includes WBS hierarchy, kind of task, anonymous developer id, start/end date and time, and interruption and break times, for a total of 203,621 time facts. "All data available" — [arXiv abstract](https://arxiv.org/abs/2106.03679)
- Mirrored as `CESAW.tgz` in Derek Jones' "Software-estimation-datasets" repo, described as "Estimate/actual in person hours for small tasks", 203,621 rows — [README](https://raw.githubusercontent.com/Derek-Jones/Software-estimation-datasets/main/README.MD)

**SEA Data Warehouse (new in 2026)**
- Released by the Software Excellence Alliance about April 2026. It contains "development-phase/estimates/actuals/start-time/end-time/person/team/etc information for the 679,904 tasks involved in implementing 1,211 software projects" built with TSP. CESAW is about a 10% subset. Projects are probably US DoD-related (WBS usage). Derek's processed code and data: https://www.shape-of-code.com/code-data/Warehouse-basic.tgz — [shape-of-code, 2026-07-05](https://shape-of-code.com/2026/07/05/detailed-management-data-on-1211-software-projects/)
- The official page https://softwareexcellencealliance.org/the-sea-data-warehouse/ returned a bot-check (HTTP 401), so I could not read its licence or access terms — fetch attempt.

**PROMISE / Zenodo classics (all numeric)**
- Derek Jones' repo https://github.com/Derek-Jones/Software-estimation-datasets lists rows and units, with no licence declared on the repo — [README](https://raw.githubusercontent.com/Derek-Jones/Software-estimation-datasets/main/README.MD), [GitHub API](https://api.github.com/repos/Derek-Jones/Software-estimation-datasets):
  - China: 499 rows, function points (FP) and person-hours
  - Kitchenham: 145 rows, FP/hours estimates and actual person-hours
  - NASA93: 93 rows, KLOC and person-months
  - Desharnais: 80 rows, FP and person-hours
  - UCP_Dataset: 71 rows, use-case points and hours
  - COCOMO-81: 63 rows, LOC and person-months
  - Maxwell: 62 rows, FP and hours
  - Miyazaki94: 48 rows
  - Finnish: 38 rows
  - Albrecht: 24 rows
  - Huijgens492: 492 rows, FP and euros/hours
  - Valdés-Souto: 57 rows, COSMIC function points and hours
  - Subbiah: 72 rows
- Zenodo copies, all licensed CC BY 4.0:
  - nasa93: record 268419 (files `nasa93.arff`, `nasa93-dem.arff`)
  - China: 268446
  - Maxwell: 268461
  - Kitchenham: 268457
  - Albrecht: 268467
  - openeffort: 268455
  - Cosmic: 268482
  - Source: [Zenodo API search](https://zenodo.org/api/records/?q=china%20effort%20estimation), [Zenodo nasa93](https://zenodo.org/api/records/268419)
- I did not find a Zenodo record for COCOMO81 or Desharnais under those names. Use Derek's repo CSVs: `COCOMO-81.csv`, `Desharnais.csv` — [GitHub contents](https://api.github.com/repos/Derek-Jones/Software-estimation-datasets/contents/)
- Derek Jones considers most of these tiny datasets inadequate. He uses Albrecht (24 rows) as the minimum size included, and calls software estimation "mostly fake research" when it relies on them — [shape-of-code, 2025-03-02](https://shape-of-code.com/2025/03/02/repo-of-software-estimation-datasets/)
- A 2026 benchmark reproducibility package covers 26 effort/work estimation datasets with a "leakage audit". It does not relicense third-party data but gives provenance and re-acquisition instructions. Zenodo 22015066, CC BY 4.0 — [Zenodo API](https://zenodo.org/api/records/22015066)

**ISBSG**
- Commercial. "All items in the Data Subscription are subject to a 12-month, single-user license." The website lists a Corporate Subscription "From: 7,500 for 1 year", a Productivity Data Query Tool "From: 15 for 1 month" and Reports "250". The currency is not shown in the scraped text; it is probably AUD, since ISBSG is based in Melbourne (UNVERIFIED) — [ISBSG project-data page](https://www.isbsg.org/project-data/)
- ISBSG states it "has provided valuable resources to 80+ universities". No academic price was found (the academic page returned 404) — [ISBSG home](https://www.isbsg.org/)

### Inferences
- CESAW and SEA are the largest task-level estimate-vs-actual sources with timestamps, and are good for calibrating overrun distributions such as round-number estimates, per-person bias and phase effects. They cannot test text understanding.
- PROMISE datasets are useful only as sanity baselines for a project-level, size-driven model. They do not suit an LLM that reads requirements.
- ISBSG's single-user, 12-month licence almost certainly forbids redistribution and embedding into a product. Check its terms before commercial use.

### Gaps
- Licences for CESAW (the Derek Jones mirror has no licence file; the SEI original terms are unknown) and for the SEA Data Warehouse are UNVERIFIED.
- I could not confirm whether SEA task records include task names or free text.
- ISBSG academic pricing and currency are UNVERIFIED.

---

## Q4. Derek M. Jones' other datasets (ESEUR, Renzo, Project-22, SiP details)

### Takeaway
Derek Jones maintains the most complete index of public estimate-vs-actual data (github.com/Derek-Jones/Software-estimation-datasets). Besides SiP, his datasets with task-level estimates and actuals are CESAW, Renzo Pomodoro (17,764 rows, dates 2009 onward) and Project-22 (630 stories, story points + hours). But **only SiP has real task text**: Renzo's descriptions are anonymised to word counts plus @tags, and Project-22 has no text. The SiP licence is CC BY-NC-ND 4.0, which **prohibits commercial use and distributing derivatives**.

### Cited Findings
**SiP**
- https://github.com/Derek-Jones/SiP_dataset. Files: `Sip-task-info.csv` (1.7 MB) and `est-act-dates.csv` (409 KB) — [GitHub contents API](https://api.github.com/repos/Derek-Jones/SiP_dataset/contents/)
- Columns of `Sip-task-info.csv`: TaskNumber, **Summary**, Priority, RaisedByID, AssignedToID, AuthorisedByID, StatusCode, ProjectCode, ProjectBreakdownCode, Category, SubCategory, **HoursEstimate**, **HoursActual**, DeveloperID, DeveloperHoursActual, TaskPerformance, DeveloperPerformance — [CSV header](https://raw.githubusercontent.com/Derek-Jones/SiP_dataset/master/Sip-task-info.csv)
- 10,100 rows of estimates and actuals in person-hours for small tasks — [Software-estimation-datasets README](https://raw.githubusercontent.com/Derek-Jones/Software-estimation-datasets/main/README.MD)
- Licence: **CC BY-NC-ND 4.0**. "Commercial use of the dataset" and "Redistributing a modified or transformed version" are not permitted. Contact for commercial use: Dr Stephen Cullum, contact@sipl.co.uk. Required attribution: "SiP Task Effort Estimation, 2019, Dr Stephen Cullum / Software in Partnership Limited" — [SiP LICENSE.md](https://raw.githubusercontent.com/Derek-Jones/SiP_dataset/master/LICENSE.md)

**Renzo Pomodoro**
- https://github.com/Derek-Jones/renzo-pomodoro (`all-tasks.csv`, 927 KB; also in Software-estimation-datasets as `renzo-pomodoro.csv`). 17,764 rows of estimates and actuals in Pomodoros for small tasks. Blog post: https://shape-of-code.com/2019/12/15/the-renzo-pomodoro-dataset/ — [README](https://raw.githubusercontent.com/Derek-Jones/Software-estimation-datasets/main/README.MD), [repo contents](https://api.github.com/repos/Derek-Jones/renzo-pomodoro/contents/)
- Columns: `X.words` (@tags such as `@planning`, `@metrics`, `@rorsetup`), `word_cnt` (per-word counts, e.g. "1,1,1,1"), `description` (a numeric id), DONE, date (from 2009-04-09), estimate, actual. **The task text is not present**; only tags and word-count structure remain — [renzo-pomodoro.csv](https://raw.githubusercontent.com/Derek-Jones/Software-estimation-datasets/main/renzo-pomodoro.csv)
- The repo has no licence declared — [GitHub API](https://api.github.com/repos/Derek-Jones/renzo-pomodoro)

**Project-22**
- https://github.com/Derek-Jones/Small-teams/tree/main/Project-22. 630 rows (325 implementation stories) from an anonymous company. Three people worked over eight months using Jira. The story table has `D1, D2, D3, Total` (hours per developer), `StoryPoints`, `Branch` (the Jira number), IsMCO, Is.Programming and Phase. **No story text.** There are also sprint-info.csv and review-info.csv — [README](https://raw.githubusercontent.com/Derek-Jones/Small-teams/main/Project-22/README.md), [story-info.csv](https://raw.githubusercontent.com/Derek-Jones/Small-teams/main/Project-22/story-info.csv)
- The Small-teams repo has no licence declared — [GitHub API](https://api.github.com/repos/Derek-Jones/Small-teams)

**ESEUR code and data**
- https://github.com/Derek-Jones/ESEUR-code-data (no licence declared on the repo) — [GitHub API](https://api.github.com/repos/Derek-Jones/ESEUR-code-data)
- Its `projects/` directory holds many small estimation datasets, including:
  - `est-act-dates.csv.xz`, `Sip-task-info.csv.xz`, `renzo-all-tasks.csv.xz`
  - `E100.D_2016-TaskLog.csv.xz`
  - `23003405-est_agile.csv.xz`, `akerele-agile.csv.xz`
  - `JorgeAranda-MSc.csv.xz`, `Little06.csv.xz`, `inconsistency_est.csv.xz`, `est_embedded.csv.xz`
  - `DeBiasExptData.csv.xz`, `EstimationStudy.csv.xz`
  - `proj-bidding.csv.xz`, `978052-fixed-price.csv.xz`
  - `82507128-kitchenham.arff`, `kitchenham1985.csv.xz`
  - a `requirements` folder
  - Source: [GitHub contents API](https://api.github.com/repos/Derek-Jones/ESEUR-code-data/contents/projects)
- Jones' summary: before April 2026 "there were only two non-trivial publicly available software project datasets (i.e., SiP and CESAW) containing software project data relating to human effort" — [shape-of-code, 2026-07-05](https://shape-of-code.com/2026/07/05/detailed-management-data-on-1211-software-projects/)
- Jones says about two-thirds of estimates are within a factor of four of the actuals. He also calls studies that use LLMs to estimate human task implementation time "fake research" — [shape-of-code, 2026-09-06](https://shape-of-code.com/2026/09/06/software-effort-estimation-in-2026/), [shape-of-code, 2026-05-10](https://shape-of-code.com/2026/05/10/software-task-estimation-using-llms-is-fake-research/)

### Inferences
- **Licence risk:** if The Estimator is (or will be) a commercial product, then shipping a model trained or calibrated on SiP, or using SiP in commercial validation reports, conflicts with CC BY-NC-ND. You need written permission from SiP (contact@sipl.co.uk) or must limit SiP to non-commercial research use.
- Renzo and Project-22 are good **calibration and overrun-distribution** datasets, with personal estimation bias over 10 years and story points versus hours. They cannot validate text understanding.
- The ESEUR files without a declared licence should be treated as "all rights reserved / research use" until you get confirmation from Jones or the original authors.

### Gaps
- I did not check the contents of the ESEUR `projects/requirements` folder or the individual small files (e.g., `E100.D_2016-TaskLog`, `23003405-est_agile`) for text columns.
- Renzo and CESAW licences are UNVERIFIED.

---

## Q5. Vietnamese or Asian outsourcing effort datasets

### Takeaway
I found **no public dataset** of Vietnamese or Asian outsourcing tasks that pairs task text with estimated and actual effort. The only Asian-origin public effort datasets I found are project-level numeric tables: China (499 projects, FP and hours) and Miyazaki94 (48 Japanese projects, LOC and man-months).

### Cited Findings
- China: Effort Estimation Dataset, 499 rows, function points versus person-hours. Zenodo 268446, CC BY 4.0 — [Software-estimation-datasets README](https://raw.githubusercontent.com/Derek-Jones/Software-estimation-datasets/main/README.MD), [Zenodo search](https://zenodo.org/api/records/?q=china%20effort%20estimation)
- Miyazaki et al. 1994 (J. Systems & Software 27(1)): 48 rows, LOC versus man-months — [Software-estimation-datasets README](https://raw.githubusercontent.com/Derek-Jones/Software-estimation-datasets/main/README.MD)
- An arXiv API search for "effort estimation" AND Vietnam returned no results. A Zenodo search for "software effort estimation Vietnam" returned only generic or unrelated effort-estimation papers — [arXiv API query](http://export.arxiv.org/api/query?search_query=all:%22effort%20estimation%22%20AND%20all:Vietnam), [Zenodo API](https://zenodo.org/api/records/?q=software%20effort%20estimation%20Vietnam)

### Inferences
- For Vietnam-specific validation, the realistic route is partner data, e.g. Jira or Redmine exports from Vietnamese outsourcing firms under NDA, or the team's own historical tickets. Public data will not cover this market.

### Gaps
- Web search was unavailable, so I could not check Vietnamese university repositories, VNU/HUST/FPT theses, Kaggle, or Asian conference replication packages. This should be retried with a working search engine.

---

## Q6. Summary catalogue (size, fields, licence, link, known issues)

### Takeaway
Only SiP (non-commercial), TAWOS (small logged-time subset), the Public Jira Dataset (needs filtering) and Itemlet (title-only, new) offer text plus actual effort. Everything else is either text plus story points (Deep-SE) or estimate plus actual without text.

### Cited Findings
| Dataset | Size | Text | Estimate | Actual | Dates | Licence | Download | Known issues |
|---|---|---|---|---|---|---|---|---|
| SiP | 10,100 tasks | Summary | HoursEstimate | HoursActual | yes (`est-act-dates.csv`) | CC BY-NC-ND 4.0 | github.com/Derek-Jones/SiP_dataset | No commercial use or derivatives — [LICENSE](https://raw.githubusercontent.com/Derek-Jones/SiP_dataset/master/LICENSE.md) |
| TAWOS v1.1 | 458,232 issues, 39 projects | title, description (text/code split), comments | Story_Point (+ estimation date) | Timespent on few issues; time proxies | UTC, sprints | Apache-2.0 (README also says "research purposes only") | doi.org/10.5522/04/21308124 (637 MB SQL zip) | Only 697 issues with both SP and Timespent (v1.0); Talend removed — [README](https://raw.githubusercontent.com/SOLAR-group/TAWOS/main/README.md), [ESEM'22](https://solar.cs.ucl.ac.uk/pdf/tawosi2022esem.pdf) |
| Deep-SE | 23,313 issues, 16 projects | title, description | storypoint | none | order only | none declared | github.com/morakotch/datasets (storypoint/IEEE TSE2018) | No actuals; NULL descriptions — [README](https://raw.githubusercontent.com/morakotch/datasets/master/storypoint/IEEE%20TSE2018/dataset/README.md) |
| Public Jira Dataset | 2.7M issues, 1,822 projects | summary, description, comments | timeestimate (and probably timeoriginalestimate, UNVERIFIED) | timespent | created/resolved/due | CC BY 4.0 | zenodo.org/records/15719919 (5.8 GB) | Unfiltered MongoDB dump; field coverage unknown — [paper](https://arxiv.org/abs/2201.08368) |
| Itemlet | 727,282 issues, 204 projects | summary only | workratio-derived original estimate; story_points (66.5% null) | Total Time Logged (h) | created (42.6% null), resolved | CC BY 4.0 | zenodo.org/records/19411554 | 2026, derived-field errors in v1.0; leakage-prone composites — [dictionary](https://zenodo.org/api/records/19411554/files/data_dictionary.csv/content) |
| CESAW | 61,817 tasks, 45 projects | none (task kind) | yes (hours) | yes | start/end | UNVERIFIED | CESAW.tgz in Derek-Jones/Software-estimation-datasets | No text — [arXiv](https://arxiv.org/abs/2106.03679) |
| SEA Data Warehouse | 679,904 tasks, 1,211 projects | UNVERIFIED | yes | yes | yes | UNVERIFIED | softwareexcellencealliance.org (bot-walled); Warehouse-basic.tgz | New 2026 — [blog](https://shape-of-code.com/2026/07/05/detailed-management-data-on-1211-software-projects/) |
| Renzo Pomodoro | 17,764 rows | anonymised (tags, word counts) | pomodoros | pomodoros | 2009 onward | none declared | github.com/Derek-Jones/renzo-pomodoro | One person; no text — [CSV](https://raw.githubusercontent.com/Derek-Jones/Software-estimation-datasets/main/renzo-pomodoro.csv) |
| Project-22 | 630 stories | none | story points | hours per developer | sprint info | none declared | github.com/Derek-Jones/Small-teams/Project-22 | One small team — [README](https://raw.githubusercontent.com/Derek-Jones/Small-teams/main/Project-22/README.md) |
| China / Maxwell / Kitchenham / NASA93 / Albrecht | 499 / 62 / 145 / 93 / 24 projects | none | size (FP/LOC) | person-hours/months | none | CC BY 4.0 (Zenodo) | zenodo.org/records/268446, /268461, /268457, /268419, /268467 | Tiny, old, project-level |
| Desharnais / COCOMO81 | 80 / 63 projects | none | FP / LOC | hours / person-months | none | none declared on repo | Derek-Jones/Software-estimation-datasets | Tiny, old |
| ISBSG | thousands of projects (count not verified) | none | size | effort | yes | paid 12-month single-user licence | isbsg.org/project-data | Cost; no redistribution — [ISBSG](https://www.isbsg.org/project-data/) |

### Inferences
- A practical validation plan:
  - (a) A **text → actual hours** held-out test on SiP (if the licence allows) plus the TAWOS `Timespent` subset, plus Public Jira Dataset issues with `timespent > 0`, split by project and by time.
  - (b) A **text → story points** test on TAWOS, using the SP estimation date for temporal splits and excluding issues whose description changed after estimation.
  - (c) An **overrun-ratio calibration** check on CESAW/SEA/Renzo/Project-22 (no text).
- Cross-check for duplicate projects across TAWOS, Deep-SE and the Public Jira Dataset (Atlassian, MongoDB, Spring, Hyperledger, Sonatype overlap) so that "external" validation is not contaminated by the same issues.

### Gaps
- Exact counts of issues with both an estimate and an actual in the Public Jira Dataset and in Itemlet need local computation.
- GitLab and Redmine public trackers also support time tracking (GitLab `time_estimate`/`total_time_spent`), but I could not verify any packaged public dataset of them (web search was unavailable).
