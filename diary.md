# Heimdall development diary

## 2026-11-05 — Sidebar and lab handoff

- Commit `4d2b389` removes the persistent sidebar underline and the animated hover line. The active link uses brighter, medium-weight text, hover brightens the label, and keyboard focus shows an outline. Blue served the updated stylesheet, and browser checks verified these states at 390, 768 and 1360 pixels.
- At this documentation checkpoint, Parallels reported both Ubuntu VMs stopped and the dashboard request timed out. Resume by starting blue and following the manual startup steps in the [runbook](docs/runbook.md). Start red for the controlled SSH alert demonstration. Boot startup and crash recovery still need verification.

## 2026-11-05 — Dashboard deployed and verified on blue

- Compared blue's ED25519 SSH fingerprint from the Parallels console with the Host-Only SSH endpoint at `10.37.129.3`. The prepared archive passed SHA-256 verification on the Mac and blue before extraction into `~/heimdall/releases/0.1.0.lzc7GK/heimdall-0.1.0`. The previous release and live state were retained.
- Tested the dashboard on blue at `127.0.0.1:8765` and confirmed it was unreachable from the Mac in that mode. Then bound it explicitly to the Host-Only address and verified all four page routes, owner login, anonymous request denial, live status, existing alert details, report export and sign-out over HTTP from the Mac. The owner token file was private (mode 600).
- Blue's monitor initially reported stopped with 24 events and one alert awaiting review. Started it through the dashboard, then verified a dashboard stop/start cycle preserved the alert history. The monitor resumed reading the SSH journal and reported available coverage. After the deployment SSH connection closed, authenticated HTTP still reported running with 34 events and one alert awaiting review. The count includes SSH activity during the deployment window.
- The previous CLI launcher checked for a monitor process under its own release path and therefore reported an error for the healthy new process. Saved it as `~/heimdall/heimdall.before-dashboard` and pointed `~/heimdall/heimdall` at the dashboard's release. The updated CLI and dashboard agreed on status.
- On blue, all 28 Python tests and shell configuration checks passed. The dashboard is running manually at `http://10.37.129.3:8765`. HTTP checks exercised the live deployment, and the earlier synthetic browser checks cover rendering and interactions. Boot/crash recovery and the controlled red-to-blue alert demonstration remain open.

## 2026-11-05 — Pre-deployment handoff

This entry records the state before deployment. The entries above record the deployment and subsequent sidebar update. [The checklist](checklist.md) has been reconciled with the actual implementation and remaining evidence.

### Saved work and current Git state

- `a64d19e` saved the shell SSH monitor, authenticated browser dashboard, tests and implementation documentation and was pushed to `main`.
- Subsequent commit `82b5bd0` saves the historical-archive cleanup, source formatting, panel design guide, `AGENTS.md` pointer and owner-provided dotted design reference. At handoff inspection, `main` and the locally recorded `origin/main` both pointed to this commit, and the working tree was clean before this checklist/diary update. These two documentation edits are subsequent local changes; no new commit or push is part of this update.
- The standing panel design source is [docs/control-panel-design.md](docs/control-panel-design.md): black/off-white, locally bundled JetBrains Mono, distinct pages, dark dotted graphics, TUI art and purposeful animation. Follow it before future panel work. Historical artifacts live in [docs/archive](docs/archive/README.md); faculty originals, evidence, fixtures and fonts/license were retained.

### 2026-11-05 live VM and dashboard deployment checkpoint

- The owner booted both Ubuntu VMs. `prlctl list` reported `UbuntuServMain` (blue) and `UbuntuServTest` (red) running; `prlctl list -i` reported Host-Only addresses `10.37.129.3` and `10.37.129.4` respectively. Kali was stopped. Parallels guest tools are not installed, so `prlctl exec` could not run guest commands.
- Peekaboo inspected blue's existing console without changing VM state. Its visible `heimdall status` reported monitor `running`, source `journalctl -u ssh`, coverage `available`, no last error, 24 events, 1 alert and 1 needing review. This is a live observation at this checkpoint, not proof of boot recovery.
- TCP port 22 accepted connections from the Mac on both Host-Only addresses. This confirms host-to-guest SSH reachability; red-to-blue attempt flow was not tested in this checkpoint.
- Built the current source archive outside the repository at `/tmp/heimdall-current-release/heimdall-0.1.0.tar.gz`, SHA-256 `bfb500fd31f9f00e52947ea8dab6ba85dfc1cc82c2f111037d424fcd5be42666`. Its file list includes the HTTP bridge, current dashboard assets/fonts, CLI and service template. The older `dist/` archive was left untouched.
- No VM files or services were changed and the dashboard was not deployed. `ssh-add -l` reported no identities, so verified SSH transfer is not yet available from the Mac. Peekaboo was available for background observation; this session did not perform terminal input. The next operational step is to make the owner's authorized SSH identity available, then verify the host key and deploy the prepared archive. Keep the existing monitor state and release intact.

### Implemented and verified

- Shell/jq owns password-result parsing, per-IP rolling-window alerts, durable restricted JSON state, deduplication/cursors, review/reopen history, configuration/history, text reports, explicit cleanup, monitor lifecycle and a separate synthetic demo. Python provides narrow lock/normalization helpers and the local HTTP bridge. Blocking, Discord and VirusTotal are still planned.
- The panel has distinct Overview, Investigations, Activity and Settings URLs, owner-token login, guarded mutations, evidence/review/report workflows, dirty-setting protection and session/history clearing. Browser checks used labelled synthetic Mac state; [dashboard evidence](docs/verification/2026-11-05-dashboard.md) does not establish VM deployment.
- Latest completed source suite: **19 monitor tests plus shell configuration checks and 9 HTTP integration tests passed** after cleanup. Additional checks covered syntax/structure equivalence, CSS order, panel HTML/art, source permissions, 82 then-current documentation links, formatter checks, unchanged protected files and package contents. No runtime suite was rerun solely for this documentation update.
- [Cleanup issue 14](https://github.com/BL47E/heimdall-home-security/issues/14) is closed. [Implementation issue 13](https://github.com/BL47E/heimdall-home-security/issues/13) remains open for unfinished milestone work. Cleanup was organizational/readability work; no runtime speed improvement was established.

### Runtime and deployment checkpoint

- The local Mac preview command using `/tmp/heimdall-dashboard-demo` stopped with exit 143, indicating termination. No listener on port 8765 was found during this handoff. Reuse the runbook's isolated synthetic-state instructions to restart it; keep demo and live records separate and keep owner tokens out of chat/screenshots/Git.
- The last verified blue deployment is the earlier CLI 0.1.0 release described in [VM evidence](docs/verification/2026-11-04-cli-blue.md), with launcher `~/heimdall/heimdall`. The monitor was left running manually then; its current power/network/process state was not rechecked in this update. The latest dashboard, formatting and design-guide changes have not been deployed to blue.
- The original `dist/` archive was preserved and still matched SHA-256 `43a1313de56e4eec56cbf8342dfb433658d9bd5fc5926aa06f86109aa9e0d490` at cleanup verification. A newer cleanup package was built only in temporary output; do not mistake either version-labelled archive for an automatically updated VM release.

### Where to resume

1. Read `AGENTS.md`, README, the checklist and this checkpoint; inspect Git status before changing files. Preserve existing work, including these documentation updates.
2. The recommended next architecture candidate is configuration-policy consistency: limits currently repeat in CLI/HTTP/HTML, and CLI/HTTP differ on empty patches. The survey is complete, but this refactor has not been designed or implemented. Browser lifecycle deepening and ingestion optimization remain separate candidates.
3. The live VM checkpoint above supersedes the earlier note that blue's current state needed rechecking. Make an authorized SSH identity available, then deploy/verify the prepared dashboard at loopback and a reachable trusted local IP. Console recovery, systemd boot/crash recovery, daily retention scheduling and further end-to-end evidence remain open. No automatic firewall/network change is authorized.
4. Keep issues 9–12's owner decisions, CI gates, Discord/outage delivery, optional reputation, the SSH enforcement design/recovery gate, faculty requirements and actual student contributions open until resolved. Existing tests or agent work do not settle faculty or contribution questions.

## 2026-11-05 — Directory cleanup and source formatting

The owner approved the architecture survey's directory-cleanup pass. Historical proposal artifacts, the supplementary rubric guide and one browser simulation now live in [docs/archive](docs/archive/README.md). Hash checks established that the two earlier DOCX copies were identical and the two PDFs were identical; one copy of each was retained, removing 267,009 duplicate bytes. The second historical HTML simulation differed only in its notice and relative links and was removed after comparison. `docs/index.html` is now a small documentation entry point. Current faculty originals, plans, ADRs, evidence, fixtures, fonts/license and the pending panel design guide/reference were preserved.

Formatted current Bash, Python, JavaScript, CSS and panel HTML using temporary development tools: shfmt 3.12.0, Black 25.1.0 and Prettier 3.6.2. No runtime dependency was added. Syntax-tree comparisons checked shell/Python/JavaScript/CSS structure, CSS declaration order and the package script's embedded Python. Panel element attributes/text and the original gate artwork were preserved; a formatter-ignore comment protects the artwork. This was a source-formatting check, not a new browser visual test.

Verification passed: 19 monitor scenarios plus shell configuration checks, 9 real HTTP integration tests, source syntax and executable permissions, 82 local documentation links, formatter checks and diff whitespace checks. A fresh package in a temporary output directory contained the expected runtime, fixtures and local fonts and excluded the historical archive, caches and private state. The earlier release archive still matches its recorded checksum. This cleanup improves navigation and readability; no runtime speed improvement is claimed. [Issue 14](https://github.com/BL47E/heimdall-home-security/issues/14) tracks the work. No commit, push, VM deployment or state/network change accompanies this pass.

## 2026-11-05 — Separate dashboard pages and local terminal styling

The owner requested distinct Overview, Investigations, Activity and Settings pages and an off-white/black terminal appearance, then chose JetBrains Mono. Implemented exact public page routes (`/`, `/overview`, `/investigations`, `/activity`, `/settings`) with one visible page per URL, real navigation links and preserved sign-in destination. Regular and Medium font files and their SIL Open Font License are bundled locally. The layout uses a black navigation rail, off-white workspace, larger navigation/evidence text, a skip-to-content link and restrained hover/focus lines that respect reduced-motion preferences.

Integration hardened exact request-target guards, including fragments and absolute-form targets. The HTTP suite passes 9 real CLI-backed tests, including direct page loads, precise font assets, protected evidence endpoints and existing authentication/configuration behavior. Python compilation, JavaScript syntax, unique DOM IDs, local font signatures/license, absence of runtime remote URLs and whitespace checks pass. These checks do not establish dashboard deployment on blue.

The parent agent's local browser checks used labelled synthetic records: direct Investigations login retained its path, the actual JetBrains font loaded, alert review/reopen and report download worked, saved settings changed from 4 to 5 and back to 4, unsaved edits triggered the leave-page warning, and Back/Forward selected the correct page. Selected alert details now refresh when their stored facts change while focused owner actions remain undisturbed. A delayed alert fetch released after actual API logout did not restore private content; sign-out on Settings cleared its form, and Back to Investigations remained signed out with no alerts. The final 390px Overview layout had no horizontal overflow, retained the active navigation marker and loaded JetBrains Mono with 14px navigation. See [dashboard verification](docs/verification/2026-11-05-dashboard.md) for the final browser evidence and responsive screenshots.

Two Terra workers implemented the frontend and route/font serving updates; the Sol handler integrated them, strengthened session/history clearing and stale-response handling, refined accessibility/typography/motion, and ran integration checks. The parent performed browser verification and captures. These are agent contributions, not evidence of either student's individual academic contribution. No new VM deployment, Git commit/push, provider integration, firewall/network change or service activation accompanies this UI work. Faculty questions and the existing response/recovery gate remain open.

## 2026-11-04 — CLI 0.1.0 packaged and tested on blue

The owner asked to finish the CLI before deploying it to the VM for checks. Added help/default command, version, configuration history, a labelled isolated CLI demo and an allowlisted archive builder. Replaced directory locks with Python standard-library OS advisory locks, which release after crashes; added interrupted-monitor and concurrent-configuration tests. Parsing and rules remain shell/jq.

Local source now passes 19 monitor tests plus configuration checks and 6 real HTTP integration tests. The packaged build passed 18 monitor and 6 HTTP tests on Ubuntu ARM64; the extra local test covers the real sanitized samples exported after deployment. Version 0.1.0 was copied into a fresh blue release directory and its SHA-256 checked there. Existing dependencies and journal access worked without installing packages or using sudo. `~/heimdall/heimdall` is the owner launcher.

Actual controlled Mac-to-blue checks: three failed password logins produced no alert; the fourth within five minutes produced one MEDIUM alert with four failures. Reviewing it then making one existing-account wrong-password attempt reopened it with five failures and preserved review history. A live stop/start resumed from the saved journal cursor without changing the 24-event total or five-failure count. The monitor was left running manually. Captured actual accepted/invalid-user/existing-account messages as sanitized structured fixtures with explicit cursor pseudonyms and provenance notes.

Blue's observed Host-Only address is `10.37.129.3`; the test source was the Mac at `10.37.129.2`, not red. Peekaboo reopened the console after the Mac was unlocked. The blue SSH fingerprint was compared with the console before using a private temporary known-hosts file for deployment. [Full evidence](docs/verification/2026-11-04-cli-blue.md) records the archive checksum, paths, commands and limitations. No firewall, network topology, account-access or system service changes were made. Boot/recovery, daily retention scheduling, red-to-blue checks, browser deployment on blue and optional integrations remain future verification/work; faculty questions remain open.

The owner authorized the sequencing and restored desktop access; the assistant implemented, packaged and exercised the CLI. This does not establish either student's individual academic contribution. No Git commit or push was made.

## 2026-11-04 — First shell monitor and browser dashboard

The owner requested implementing the monitor and adding a local browser dashboard, with shadcn/OpenCode visual references. [ADR 0003](docs/adr/0003-shell-monitor-with-local-dashboard.md) records the scope expansion; faculty tool acceptance remains open.

Implemented shell/jq password parsing, rolling-window alerts, restricted atomic state, replay deduplication, review history, configurable limits, reports, explicit retention cleanup and journal monitor lifecycle. Python provides the local HTTP bridge and a small IP/fingerprint helper. The dashboard offers token login, status, evidence, review/reopen and configuration with an offline monochrome design. See [the runbook](docs/runbook.md).

Local verification: 13 monitor scenario tests plus shell configuration checks and 6 real HTTP-to-shell integration tests pass. Shell/JavaScript syntax and whitespace checks pass. The browser displayed a labelled synthetic alert and persisted an owner review. A 390px phone viewport had no horizontal overflow. Exact details and limitations are in [issue 13 evidence](https://github.com/BL47E/heimdall-home-security/issues/13#issuecomment-6633729764).

Blue was started and logged in through Peekaboo. Later `prlctl list` showed it running, while guest execution returned “Unable to open new session in this virtual machine.” No guest installation, new SSH attempts, real fixture export, live journal runtime validation or service activation was completed. The current dashboard runs on the Mac's loopback address with disposable synthetic state; this is not live blue monitoring. Daily cleanup scheduling, Discord, VirusTotal, TUI, guided demonstration and enforcement remain planned.

The owner supplied scope and design direction. Two Terra workers supplied initial state/config code and dashboard code; the Sol handler defined the contract, integrated documentation and strengthened HTTP/session tests. The parent completed the missing monitor implementation, expanded scenario tests and refined/checked the browser UI. These are agent contributions; both students' actual academic contributions still need recording. No Git commit or push was made.

## 2026-11-01 — Lab setup and first SSH tests

### What we completed

- Reviewed the shell-first college milestone: build an explainable SSH monitor with shell scripts, local records and terminal management. The broader product remains future scope.
- Chose Parallels Desktop for the two-VM lab on the MacBook Air M4 with 16 GB RAM.
- Set up two Ubuntu ARM64 VMs. Ubuntu Desktop was installed; it can support the shell-based milestone. Blue's SSH banner reports Ubuntu 26.04.1 LTS, rather than the initially suggested Ubuntu Server 24.04 LTS.
- Used red and blue desktop accents to distinguish the test machine from the monitored machine.
- Configured Shared Network and Host-Only adapters on both VMs. Shared provides outbound connectivity; Host-Only carries the controlled SSH tests. Shared networking is not full isolation from the host or LAN.

| Role | Parallels VM | Linux hostname | Shared IPv4 | Host-Only IPv4 |
|---|---|---|---|---|
| Blue: monitored system | UbuntuServMain | VirtualMainSERV | 10.211.55.9 | 10.37.129.3 |
| Red: test system | UbuntuServTest | VirtualTest | 10.211.55.10 | 10.37.129.4 |

These addresses were observed during setup; recheck them after network changes or DHCP renewals.

- Confirmed both guests report `aarch64`, have both network adapters active and route outbound traffic through Shared Network.
- Installed OpenSSH Server on both VMs and verified their SSH services were active.
- Confirmed red could ping blue's Host-Only address with three replies and no packet loss.
- Compared blue's ED25519 host fingerprint with the fingerprint presented to red, then completed a successful SSH login from red to blue.
- Verified the remote hostname and `SSH_CONNECTION`: red connected from `10.37.129.4` to blue at `10.37.129.3`, port 22.
- Checked blue's SSH journal and found the successful password login at 20:02:48. The journal also showed SSH starting again after a reboot.
- Installed Peekaboo 4.9.7 on the Mac for computer control. Enabled the required macOS permissions and verified desktop interaction. A stale background permission state initially prevented access; the local runtime subsequently reported the permissions granted.
- Used computer control to run one failed SSH password attempt from red against a deliberately invalid account, `heimdall_probe_invalid`, on blue.
- Confirmed red received `Permission denied` and blue logged `Failed password for invalid user heimdall_probe_invalid` from `10.37.129.4` at `2026-11-01T20:29:05+05:30`.

### What we learned

- `journalctl -u ssh` exposes the successful and failed authentication records needed for the first parser on this installation. No elevated command was needed to read the journal in blue's tested account.
- One failed attempt emits several related messages: invalid user, PAM authentication failure, failed password and connection closure. The parser must count the authentication attempt once, rather than count every line as another failure.
- The live records use `sshd-session` for authentication messages; the parser must handle the observed format.
- The VM lab and SSH logging are verified. These tests demonstrate the input data, not an implemented Heimdall monitor or alert.

### Next work — planned

- Save representative logs as reproducible test fixtures, including a wrong password for an existing test account.
- Build the shell parser for timestamps, source IPs, usernames and authentication outcomes.
- Implement and test the rule: four failures from one source IP in a rolling five-minute window produce an explained alert.
- Verify three failures do not alert, the fourth does, old failures expire and related log lines are not counted twice.
- Connect the parser to the live journal, then add persistent history, terminal management and background service operation.

Discord delivery, optional VirusTotal context, guided simulations and SSH source blocking are not implemented. Real blocking remains subject to design review and tested console recovery. Faculty questions recorded in the milestone documents remain unresolved.

Evidence for this entry comes from terminal output and screenshots observed during the setup session. Reusable log fixtures and repository test results have not yet been captured. Passwords are intentionally excluded from this diary.

## 2026-11-04 — Workflow audit and SSH event contract decisions

### What we completed

- Rechecked the live GitHub tracker. The seven original issues form an implementation backlog, not a Wayfinder decision map. Created [Chart the shell-first college milestone and CI decisions](https://github.com/BL47E/heimdall-home-security/issues/8) with four native child decision tickets and native blocking links. The destination is a decision-complete shell-first college milestone plan, including CI and manual deployment.
- Claimed [Settle the SSH log and event contract](https://github.com/BL47E/heimdall-home-security/issues/9) for the owner. It remains open; the time-window/replay and durable-state tickets remain blocked in sequence. CI can be discussed independently. No decision ticket was closed.
- Added the owner's learning preference to `AGENTS.md`: this is their first project of this kind, so explain unfamiliar terms, commands and practical choices in manageable steps. Added Wayfinding operations and its label exception to the tracker instructions.
- Audited the repository: documentation and the historical browser simulation exist; no shell runtime or automated runtime tests exist. GitHub reported zero Actions workflows/runs, no classic `main` protection and no repository rulesets at audit time. CI/CD remains unimplemented; deployment remains manual.
- Found no justified runtime architecture refactor because runtime modules do not exist yet. Reproduced a historical browser classification defect: `192.0.2.1` and `HTTPS://example.org` were labelled DOMAIN. This reference-artifact defect remains unfixed and is separate from the milestone parser.
- Used Peekaboo to inspect blue's running Ubuntu terminal and execute `journalctl -u ssh -n 40 --no-pager -o short-iso` without sudo. Read the historic successful-password and invalid-user failed-password records and their supporting messages. [The observation comment](https://github.com/BL47E/heimdall-home-security/issues/9#issuecomment-6623684345) contains sanitized screen transcriptions, not exact exported fixtures.
- Reconciled the checklist with [lab evidence recorded in the implementation issue](https://github.com/BL47E/heimdall-home-security/issues/1#issuecomment-6632267553). Split combined items so VM setup, controlled SSH access, route observations and log inspection can be checked while console recovery, outbound reachability and reusable fixtures remain open.

### Agreed design — planned behavior, not implementation

The canonical details live in the SSH contract ticket's progress comments:

- [Initial source and authentication scope](https://github.com/BL47E/heimdall-home-security/issues/9#issuecomment-6624219331): blue's SSH journal, explicit password successes/failures, and one count per authentication result. Other methods, including SSH keys, are unsupported until added and tested.
- [Event facts and local evidence](https://github.com/BL47E/heimdall-home-security/issues/9#issuecomment-6632177523): preserve available event time/precision, source IP, username, outcome, explicit invalid-user information, journal record identity and the original authentication message locally with restricted access. Exact serialization and journal identity representation are not settled.
- [Incomplete evidence and availability notes](https://github.com/BL47E/heimdall-home-security/issues/9#issuecomment-6632213377): show useful available information and a short explanation of anything missing, unreadable or unsupported. Missing username does not prevent counting a valid timed failure from a known IP; missing source or usable time prevents the corresponding per-IP/time-window calculation. Preserve evidence without combining unknown sources or inventing outcomes. Failed log access must not look like healthy monitoring.

### Limitations and contributions

- VM state changed between observations: an initial Parallels CLI check showed both stopped; a later Peekaboo observation showed blue running. A subsequent Peekaboo call returned `Application 'Parallels Desktop' not found`, so journal metadata inspection did not occur. None of these observations establishes the VMs' current state.
- No new live login attempts, console-recovery tests, exact fixture exports or parser tests were performed during this session. The earlier successful/failed messages establish input examples only. No automatic network or device changes were made.
- The owner made the design choices and requested beginner-friendly teaching; the assistant inspected the repository/journal, recorded decisions and updated tracking. Meaningful teammate ownership and each student's actual contributions still need recording; no claim of equal contribution is made.
- Faculty questions about report format, dates, deadline and presentation remain unresolved.

### Next work — planned

1. Inspect structured journal metadata to verify the stable record reference and timestamp precision.
2. Export and sanitize exact login examples, including wrong password for an existing test account; preserve sample provenance.
3. Finalize the SSH event contract before resolving the dependent time-window/replay decision. Prepare the remaining offline boundary fixtures as implementation work.
4. Agree and implement appropriate CI checks; keep deployment manual. Runtime parsing, alerts, persistence and integrations remain planned.

This checkpoint saves documentation and tracking progress; it does not complete the lab/fixture package or implement the agreed behavior.
