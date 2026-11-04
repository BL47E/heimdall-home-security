# Heimdall agent guide

Read `README.md` and the relevant section of `HEIMDALL_BLUEPRINT.md` before changing product behavior. Treat the blueprint as the source of truth for current scope; mark behavior as implemented, simulated, or planned. Keep local processing useful without credentials or internet access. Do not add automatic device or network changes without a reviewed design and explicit owner approval.

For the current college milestone, read `docs/college-milestone-plan.md`, `checklist.md` and `docs/evaluation-alignment.md` before implementation or academic deliverables. ADR 0002 scopes the shell-first milestone; preserve unresolved faculty questions until answered.

Use the terms in `GLOSSARY.md`. Read applicable decisions in `docs/adr/` before changing product boundaries or deployment choices.

## Learning and collaboration

The owner is building this kind of project for the first time and is learning the tools and concepts as the project progresses. Assume no prior knowledge of Linux administration, SSH monitoring, GitHub workflows, CI/CD or software architecture. Explain new terms in plain language when they first appear, use small examples from Heimdall, and connect each step to its purpose. When asking for a decision, explain the practical choices and recommend one with a reason. For commands the owner runs, explain where to run them, what they do and what the result means. Teach in manageable steps so the owner can understand and explain the project themselves.

## Agent skills

### Issue tracker

Project work is tracked in GitHub Issues. Use `gh` from this repository. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the default labels `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, and `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context project with a root glossary and shared ADRs under `docs/adr/`. See `docs/agents/domain.md`.
