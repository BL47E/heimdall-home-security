# Issue tracker: GitHub

Issues and implementation work live in this repository's GitHub Issues. Use `gh` for issue operations and confirm the repository with `gh repo view` before writing. Scope current implementation issues to the shell-first Ubuntu college milestone in `docs/college-milestone-plan.md`; track broader NAS/router features separately as future work. Do not treat pull requests as a request queue.

## Wayfinding operations

The decision map is [Chart the shell-first college milestone and CI decisions](https://github.com/BL47E/heimdall-home-security/issues/8). Its destination includes CI and manual deployment. Build issues remain separate implementation work.

- Find maps with `gh issue list --label wayfinder:map`. Read the selected map's Destination and Notes first.
- List children with `gh api repos/BL47E/heimdall-home-security/issues/MAP_NUMBER/sub_issues --paginate`. Open tickets live in this native relationship, not a copied list in the map body.
- For each open, unassigned child, query `gh api repos/BL47E/heimdall-home-security/issues/TICKET_NUMBER/dependencies/blocked_by --paginate`. The frontier contains children whose blockers are all closed. Preserve the returned child order when choosing the first frontier ticket.
- Claim before work with `gh issue edit TICKET_NUMBER --add-assignee @me`, assigning the developer driving the map. Recheck the issue and blockers before starting; skip tickets claimed by another session.
- Create tickets first, then attach them using `gh api --method POST repos/BL47E/heimdall-home-security/issues/MAP_NUMBER/sub_issues -F sub_issue_id=CHILD_DATABASE_ID`. The database ID comes from the issue's REST `id`, not its issue number.
- Wire native blocking with `gh api --method POST repos/BL47E/heimdall-home-security/issues/DEPENDENT_NUMBER/dependencies/blocked_by -F issue_id=BLOCKER_DATABASE_ID`.
- Resolve with an answer comment, close the ticket, then add a linked one-line gist to the map's Decisions so far. Use linked titles in narration. Human discussion tickets require actual owner answers; resolve at most one non-research ticket per session.

Use only `wayfinder:map` on maps and `wayfinder:research`, `wayfinder:prototype`, `wayfinder:grilling`, or `wayfinder:task` on decision tickets. These issues do not receive implementation triage labels. The map is planning; it does not authorize automatic deployment or network changes.
