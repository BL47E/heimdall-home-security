# College evaluation alignment

Source: the owner-provided [“Mini-Project Evaluation Rubrics (30 Marks).docx”](reference/evaluation-rubric.docx), received 2026-11-01. The criteria and performance descriptors below were checked against the document's tables. The original file's SHA-256 is `ebeaa4c2bcaa5e54d4f9a30c4e060611d6a668fcb3bd0455b4f2780c600f6caf`.

The rubric confirms evaluation criteria, not a feature specification, report template, deadline or permitted technology list. The owner subsequently supplied an idea template, documented below; its applicability to the final report remains unconfirmed. Other requirements remain subject to faculty instructions. Evidence suggestions here are our planning recommendations, not additional faculty requirements. No marks are guaranteed.

## Evidence for the submission

Use the [implementation status matrix](status.md) to distinguish live results, simulations and open checks for each claim. Cite the dated observation, including the injected sender failure in the Discord recovery demonstration. Record what each student actually contributed. The [acceptance checklist](../checklist.md) tracks the remaining submission work.

## Criteria and evidence plan

Each sub-criterion carries 3 marks, for 30 total. Each has performance levels from 0 to 3. The summary calls the one-mark level Average, while the descriptor table calls it Acceptable; use the actual descriptors when preparing evidence.

| Category | Sub-criterion | Excellent descriptor from the rubric | Proposed Heimdall evidence |
|---|---|---|---|
| Problem Analysis | Problem Domain Identification & Analysis | Clearly identified with in-depth analysis and strong justifications | Explain the difficulty of noticing repeated SSH failures in raw logs, the intended owner, controlled VM environment, and detection limitations. |
| Problem Analysis | Review of Existing Systems & Project Feasibility | Comprehensive review with clear feasibility analysis | Review built-in SSH logs, Fail2ban and a broader monitoring tool against this project's learning goals. Assess two-VM hardware needs, ten-day scope and integration dependencies; verify factual comparisons against primary sources when writing the report. |
| Project Design | Objectives & Methodology of Proposed Work | Clear, measurable objectives with well-defined methodology | State observable outcomes: fourth failure triggers within five minutes, evidence is inspectable, history survives restart, and failed Discord delivery is queued. Explain the input-to-alert-to-review flow. |
| Project Design | Relevance of Algorithms / Techniques | Highly relevant and well-justified | Explain parsing, rolling time windows, source grouping, review state, file persistence and notification retries. Justify shell and supporting tools for the course. |
| Project Implementation | Synchronization of Design & Implementation | Fully aligned and consistent | Maintain a feature-to-code-to-test mapping and update the submitted design to the delivered scope. Label simulated actions and optional unfinished work. |
| Project Implementation | Implementation & Demonstration of Modules | All modules correctly implemented and demonstrated | Rehearse the working log pipeline, rule, management interface, history and notification recovery. Include VirusTotal and real blocking only according to their actual delivered status. |
| Project Report | Organization & Structure of Project Report | Well-organized, logical, easy to follow | Follow the supplied idea template for the proposal; maintain design, implementation, test and result evidence for the final report. Confirm its prescribed structure before submission. |
| Project Report | Compliance with Prescribed Report Format | Fully compliant | Apply the supplied idea template's section limits and formatting to the proposal. Confirm whether the same template governs the final report; final compliance cannot yet be verified. |
| Communication | Clarity & Organization of Presentation | Clear, confident, and well-structured | Rehearse a concise problem explanation, controlled scenario, evidence review, limitations and questions. Both students should understand the complete flow. |
| Communication | Contribution by Each Team Member | All members contributed equally and effectively | Agree meaningful ownership for both students; retain honest evidence of implementation, test, setup, documentation and presentation work. Do not claim equal contribution without evidence. |

## Changes to the delivery approach

- Keep the agreed software priorities, including real blocking last. Feature quantity is not a separate criterion.
- Write report material and capture test evidence as development proceeds, rather than starting the report on the last day.
- Use a small implementation checklist linking objectives, modules, tests and demonstration steps. Keep it synchronized when features move to future work.
- Give the second student an owned workstream. Suggested division, subject to team agreement: the primary developer owns parsing, rules and service behavior; the second student owns test VM setup, test fixtures and end-to-end verification, and jointly develops the report and presentation. Adjust workloads toward meaningful, balanced contribution.
- Preserve Day 10 for rehearsal and final submission checks. Use earlier days to produce the report draft and gather evidence.
- The guided demonstration can include labelled simulations, but simulated blocking or reputation results do not establish that a real integration has been implemented.

## Supplied idea template

Source: owner-provided [“Idea Template.docx”](reference/idea-template.docx), received 2026-11-01, checked against its document XML. SHA-256: `53991ae546aad2d277d6afd09c70fc32410c506f8f53c2e7b68582daa1c59a80`.

This establishes a proposal/idea document structure; do not assume it is also the final implementation-report template.

| Required section | Stated limit |
|---|---|
| Introduction | At most one page |
| Project Scope | At most one paragraph |
| Addressed the Problem: Targeted Applications | At most two paragraphs |
| Project Objectives | At most three realistic, quantified objectives |
| Novelty/Innovation in the existing work | One or two paragraphs |
| Required Tools | No explicit limit |
| Gant Chart (template spelling; Gantt chart) | No explicit limit |
| References | No explicit limit |

The template also has a title page and contents table. Its stated formatting is Times New Roman; headings are 14-point bold, body text is 12-point justified, and subheadings are 12-point bold and justified. Number every table and figure, with a descriptive, centered caption, and use the same formatting across topics.

Planning implications:

- Compress the feature list into three measurable objectives: (1) detect and explain the four-failure/five-minute SSH pattern in controlled tests, (2) manage and preserve investigations with the agreed 60-day retention and restart behavior, and (3) deliver live and queued Discord alerts in controlled availability tests. These are proposed document groupings of the agreed scope, not implementation results.
- Keep VirusTotal as optional context and live blocking as the last implementation priority. Avoid making their completion a required quantified objective before feasibility and response design are established.
- Describe the novelty as the project's combination of explainable evidence, shell-based management and an outage-aware demonstration. Do not claim that SSH failure detection itself is new or better than existing tools without evidence.
- Include the agreed ten-day sequence in the proposal's Gantt chart, using relative days until actual dates are confirmed.
- Confirm title-page details before producing a submission copy. The template says “Academic Year: 2025-26 (Odd Semester)” and “September 2026”; preserve these as template values pending confirmation, not as verified submission dates. Include only actual team members.

## Remaining faculty inputs

1. Whether this idea template also governs the final report, any final-report template, and required submission files.
2. Exact deadline, evaluation date and presentation duration.
3. Any separate project brief or course-specific constraints, including allowed languages/tools and expectations for live versus simulated modules.

The existing repository's full-marks guide is supplementary material. This supplied rubric is the source for the criteria above; actual outcomes depend on the evaluator and delivered evidence.
