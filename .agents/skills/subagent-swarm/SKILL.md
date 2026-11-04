---
name: subagent-swarm
description: Coordinate a user-requested swarm of subagents with a dedicated handler who integrates worker results and reports to the main agent. Use when the user invokes Subagent swarm or explicitly requests this handler-led swarm workflow.
---

# Subagent swarm

Coordinate a task through an orchestrator, a dedicated handler, and a user-selected number of workers. The orchestrator is the main agent in the user's conversation; it retains responsibility for the task and the final response.

## Choose the swarm size

1. Before starting any swarm agent, ask how many **workers** to use: **2, 4, 6, or Custom**. Use the available interactive question tool when appropriate; otherwise ask in conversation. If the user already specified a valid worker count for this invocation, use it without asking again.
2. For Custom, obtain a positive whole-number worker count before launching. If the question interface accepts a free-text number, treat it as Custom. Reject zero, negative, fractional, or nonnumeric values and ask again.
3. The handler is one additional subagent and is not included in the worker count. Explain this when asking. The orchestrator is not a subagent and is not counted.
4. Wait for the user's selection; do not assume a default or launch a partial swarm while the choice is pending.

## Choose models

Before launching the handler or workers, ask the user how to allocate models across the chosen workers. Offer two paths:

- **Automatic (recommended):** select available models based on the task's complexity, required capabilities, and any stated cost or speed preferences. Briefly explain that this matches models to the work. Discover available models and provider capabilities using the current runtime's supported tools; do not invent availability, pricing, or capabilities. Tell the user the planned allocation and use it when they have chosen automatic selection.
- **Custom allocation:** let the user describe model names or IDs and the number of workers for each, for example, “2 on model A and 3 on model B.” Ask for a provider when a name is ambiguous. The allocation must use positive whole-number counts that add up to the chosen worker total. Ask the user to correct an incomplete or inconsistent allocation before launching.

If the user has already supplied a complete allocation or explicitly chosen automatic selection for this invocation, do not ask them to repeat it. Ask about the handler model only if the user wants to specify it; otherwise the handler inherits the orchestrator's model and is not counted in the worker allocation. Include the handler's model or inherited setting in the plan shown to the user.

Honor explicit model and provider choices and pass each assignment through the appropriate runtime mechanism. If a requested model or provider is unavailable, disallowed, or cannot be verified, explain the limitation and ask the user for an alternative; do not silently replace it. Follow the runtime's rules for capabilities discovery, model selection, and delegation. If automatic selection cannot use the discovered models under those rules, explain the limitation and request a workable allocation. Do not start any swarm agent until both the worker count and model allocation are resolved.

## Establish the team

- Read applicable project instructions and identify the task's deliverables, constraints, existing changes, and acceptance checks. Decompose the task into useful, bounded worker assignments, with clear interfaces and preferably distinct file ownership. More workers do not justify inventing unrelated work.
- Use the subagent tools and coordination rules supplied by the current runtime. Follow its restrictions on provider, model, isolation, agent creation, waiting, cancellation, and side effects. This skill grants no extra permissions and does not override higher-priority instructions.
- Appoint one subagent as the **handler** before dispatching worker work. The handler gathers worker results, integrates their contributions, checks their fit, and reports the combined result to the orchestrator. Give the handler the task scope, ownership map, integration authority, expected verification, and a list of workers and assigned models. Instruct it not to spawn additional agents unless the runtime and task explicitly allow that.
- When nested delegation is unavailable or prohibited, the orchestrator launches the handler and workers as siblings and coordinates their communication. Have workers send their results to the handler where supported; otherwise relay their results. Do not claim that the handler integrated work if it could not actually do so.
- Use the requested number of worker assignments. If the concurrency limit is lower, retain the handler when possible and run workers in waves. If the runtime cannot keep a handler active alongside workers, sequence the handler after workers with their complete handoffs, provided it can inspect and integrate their actual artifacts. Explain the limit and execution plan. If even that is impossible, tell the user what is blocked and ask how to proceed; do not silently substitute the orchestrator for the handler or reduce the requested count.

## Dispatch and integrate

1. Give each worker a concrete objective, scope, relevant context and constraints, assigned files or artifacts where applicable, and verification expectations. Tell workers about other active changes and the workspace model. Require a handoff listing changes or findings, paths or commits, checks and results, assumptions, unresolved issues, and any overlap.
2. In a shared workspace, assign non-overlapping edits where practical and communicate interface changes promptly. A worker must not overwrite or revert another worker's or the user's work. Avoid multiple concurrent edits to the same file; assign shared-file edits to the handler or sequence them.
3. For isolated workspaces, use only the runtime's supported isolation and integration mechanisms. Give the handler enough information and access to inspect each result and incorporate authorized changes. Preserve pre-existing user changes; never use destructive cleanup or overwrite them to resolve conflicts.
4. The handler reviews each handoff and actual changes, resolves compatible overlaps, integrates the complete set, and runs appropriate integration checks. It escalates conflicting requirements, inaccessible artifacts, failed checks, or decisions outside its authority to the orchestrator; it must not claim unverified work passed.
5. The handler reports to the orchestrator: completed work and artifact paths, how contributions were integrated, checks run and results, conflicts or incomplete assignments, and remaining risks or decisions. If integration is blocked, report what was and was not integrated and why.
6. The orchestrator waits for the handler and required workers, reviews the combined result and relevant verification, addresses remaining authorized work, and reports the actual outcome to the user. If an agent fails or the task changes, follow runtime cancellation and replacement rules, preserve completed work, and disclose any incomplete portion.

For research or review tasks with no code changes, the handler consolidates findings and reconciles contradictions with evidence; it reports uncertainty and sources instead of inventing file changes. External publishing, messaging, or other consequential actions still require the authorization and approvals applicable to the underlying task.
