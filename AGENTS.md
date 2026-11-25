# Heimdall agent guide

Read `README.md` and the relevant section of `HEIMDALL_BLUEPRINT.md` before changing product behavior. Treat the blueprint as the source of truth for current scope; mark behavior as implemented, simulated, or planned. Keep local processing useful without credentials or internet access. Do not add automatic device or network changes without a reviewed design and explicit owner approval.

For the current college milestone, read `docs/college-milestone-plan.md`, `checklist.md` and `docs/evaluation-alignment.md` before implementation or academic deliverables. ADR 0002 scopes the shell-first milestone; preserve unresolved faculty questions until answered.

Use the shared terms in `GLOSSARY.md` and read applicable decisions in `docs/adr/` before changing domain language, product boundaries or deployment choices.

Before adding or changing control-panel pages, components, styling, artwork or interactions under `web/`, read and follow [docs/control-panel-design.md](docs/control-panel-design.md).

When updating `diary.md`, summarize entries more than four calendar days old relative to the update date. Keep dated outcomes, decisions, unresolved questions and links to original evidence. Keep newer entries detailed.

## Learning and collaboration

The owner is building this kind of project for the first time and is learning the tools and concepts as the project progresses. Assume no prior knowledge of Linux administration, SSH monitoring, GitHub workflows, CI/CD or software architecture. Explain new terms in plain language when they first appear, use small examples from Heimdall, and connect each step to its purpose. When asking for a decision, explain the practical choices and recommend one with a reason. For commands the owner runs, explain where to run them, what they do and what the result means. Teach in manageable steps so the owner can understand and explain the project themselves.

## Agent skills

### Issue tracker

Project work is tracked in GitHub Issues. Use `gh` from this repository. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the default labels `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, and `wontfix`. See `docs/agents/triage-labels.md`.
