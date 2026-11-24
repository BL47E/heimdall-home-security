# Heimdall development diary

## 2026-11-25 — Terminal app refinement, honest monitor startup and post-reset lab recovery

The owner's laptop was reset after November 17, removing Peekaboo and renaming the lab accounts. Peekaboo 4.9.10 was reinstalled through Homebrew, its Screen Recording/Accessibility permissions granted by the owner, and it is connected again as the OpenCode MCP server. The current model cannot read screenshot pixels and no local vision model is installed, so VM access proceeded over SSH with the owner's password supplied through a private prompt; the credential stayed out of chat, commands and Git.

Lab identity after the reset (observed over SSH from the Mac): UbuntuBlue is hostname `blueblue`, user `blazeblue`, Shared `10.211.55.9`, Host-Only `10.37.129.8`; UbuntuRed is hostname `blazered`, user `blazered`, Shared `10.211.55.10`, Host-Only `10.37.129.9`. The pre-reset Host-Only addresses in older records no longer respond. Blue's Heimdall tree moved with the account rename to `/home/blazeblue/heimdall` and holds releases `0.1.0-ecaec12` and `0.1.0-vt`; `heimdall-monitor.service` is enabled and active, the cleanup and Discord sender timers are active, and `heimdall status` reported the monitor running from `journalctl -u ssh` with no last error. The active unit's release path and the HTTP dashboard were not re-verified this session. Red has no deployment, as intended for the test source. One failed SSH attempt against the deleted `bl47eheim` account was recorded by blue's monitor as a real event from the Mac; it stayed below alert threshold.

Per the owner's request, both VMs now disable idle screen locking: session `idle-delay` is 0 and idle suspend is `nothing` (AC and battery), so the screen asks for a password only at explicit logout/login or a manual lock. This owner-requested lab configuration was applied with gsettings over SSH without sudo; no other VM change, service or credential accompanied it.

The terminal app refinement from the handoff is implemented in source. Bare `heimdall` in an interactive terminal opens the app while noninteractive calls keep plain help; first use runs guided onboarding whose completion is saved atomically per state directory, adopting existing state unchanged with local or offline finish; later launches open an Overview workspace with monitor state and start/stop, each alert's investigation with review/reopen, recent events, rule settings through a confirmed `/config` command, providers and Setup/Demo access. A persistent status line shows monitor state, coverage and alert counts, and a slash-command bar offers `/help`, `/refresh` and page commands. Leaving requires the exact `/exit` command: `q` and top-level Escape never exit, Escape cancels the command bar or backs out of dialogs and onboarding, and Ctrl+C still interrupts and restores the terminal. The palette uses a genuine black background, a quiet gray secondary tone and one cyan accent, with a dotted rune wordmark on the welcome step. macOS's bundled ncurses delivers arrow keys byte-by-byte, so the app reassembles escape sequences itself; on Ubuntu ncurses this path is unused.

Eleven new pseudo-terminal checks in `tests/test_tui.py` run the real launcher against disposable state: onboarding cancellation without a record, completion with record reuse and second-launch skip, adoption of existing state without reset, offline completion, exact-`/exit` enforcement with `q` and Escape staying in-app, command-bar navigation with a confirmed `/config` change, narrow-screen guidance, record privacy/atomicity and noninteractive launcher behavior. The harness keeps the pty drained continuously (the small macOS pty buffer otherwise blocks the application mid-session) and reconstructs the rendered screen from the ANSI stream, because old ncurses fragments updates into cursor-hopped pieces that defeat byte matching.

`heimdall monitor start` previously returned status after a fixed 0.3-second sleep, and a pre-existing write race could drop the `coverage: available` flag when a restarted monitor's first journal record was a duplicate ingested concurrently. Under load this produced a false `unavailable` report. Start now polls for the new reader's own state — a changed pid with coverage, a reported error, or a bounded timeout — and `monitor_run` marks coverage before spawning the journal reader so the first ingest cannot clobber it. The runtime contract documents the readiness rule. The crashed-monitor restart check passed three consecutive local runs after the fix.

The local suite is now 82 Python tests (19 monitor, 20 Discord, 5 VirusTotal, 10 HTTP, 13 service, 4 retention, 11 terminal): 81 pass on this Mac with one Ubuntu-only systemd parser skip, plus shell state/configuration checks and 19 monitor scenarios.

At the owner's request the updated CLI was then deployed to blue as `~/heimdall/releases/0.1.0-342daa1/heimdall-0.1.0` from commit `342daa1`, checksum-verified with a cross-checked host key. All 82 tests pass on the VM — including the Ubuntu-only systemd parser check — plus shell scenarios and noninteractive CLI checks. A first package exposed seven terminal-test failures that were the harness's own screen reconstruction (byte-level parsing of UTF-8 output and missing `CSI d` handling on Ubuntu's ncurses); the fix changed only the test file. The terminal app was not driven interactively in the VM's graphical console this session. See [full evidence](docs/verification/2026-11-25-release-verification.md).

The owner then asked why the new release could not control the installed service and requested the fix. The refusal was the designed release-identity check: inspection showed the monitor, cleanup and Discord units plus the launcher still referenced the `0.1.0-vt` preview release, not `0.1.0-ecaec12` as earlier recorded here — this entry's earlier wording was corrected accordingly. After backing up the three units, the launcher and the live state to `~/heimdall/evidence/2026-11-25-service-switch/`, the units were prepared with only the release path changed, accepted by `systemd-analyze verify`, installed root-owned mode 644 and reloaded; the launcher now executes the new release. The monitor restarted active on `0.1.0-342daa1`, and `~/heimdall/heimdall status` from the new CLI reports running coverage with the manager correctly identified as systemd. Live state was preserved with cursor continuity: 59 events and zero alerts after the switch, the growth being this session's own real SSH journal activity. A first switch attempt aborted safely at unit verification without changing anything. See [switch evidence](docs/verification/2026-11-25-service-switch.md).

No live VirusTotal lookup, blocking, firewall or account change accompanies this work. Faculty questions and student contribution records remain open; the work is committed on the `TUI-implementation` branch and pushed for owner review without merging to `main`.

## 2026-11-17 — Documentation reconciliation and pull-request preparation

Checked GitHub: no existing pull requests; `main` still points to the earlier dashboard handoff while the pushed `codex/service-cleanup-deployment` branch contains the service/retention/Discord work. A recent-push banner is not a pull request or merge. Prepared the branch for a draft PR; no merge or new VM deployment accompanies this documentation work.

Audited current documentation against recorded implementation and evidence. Corrected stale Discord/service-control claims, old VM prerequisites, fixture provenance, standalone-versus-systemd instructions and dated checklist counts. Added the [implementation matrix](docs/status.md) and [verification index](docs/verification/README.md), linked them from the overview, plan, backlog, runtime contract, academic evidence map and HTML index. Retained faculty originals, ADR decisions, archived artifacts and dated test records without changing their historical results. Owner decisions, faculty questions and unfinished academic work remain open.

Reran the current Python suite on the Mac: 66 tests in 53.490 seconds, 65 passed and one Ubuntu-only systemd unit-parser test skipped. This does not replace the previously recorded all-66 Ubuntu run or claim a new live VM observation. Documentation validation and PR metadata are checked separately.

## 2026-11-17 — Real Discord alerts and scheduled delivery

The owner approved creating Heimdall's webhook in the new Blaze's TEST server's #general channel, private storage on blue and transmission of controlled SSH summary metadata. Computer Use created/named the webhook and later observed three delivered messages. The URL stayed out of code, evidence and command output. Configuration was passed through hidden input to the shell CLI; the credential remained mode 0600 on blue.

Red generated seven deliberate failed-password attempts with strict host checking. Three produced no alert; the fourth created a new alert and Discord accepted its notice. Review/fifth-failure reopening queued another notice. A disposable sender-only socket fault retained that notice, recorded ambiguity/backoff and left the monitor healthy. A fresh CLI process respected the saved retry time; a sixth failure after another review queued a second reopening notice. Recovery delivered both together. This was controlled transport fault injection, not a real Discord outage or network change.

Installed and enabled the reviewed unprivileged Discord service/timer after Ubuntu unit verification. The seventh failure reopened the reviewed alert and the timer delivered it without a manual flush at 16:10:09 IST. Final state: four delivered notices in three messages, zero pending; monitor still healthy under PID 21431, with 136 events and three alerts. Existing earlier evidence and alerts were preserved. [Verification and limits](docs/verification/2026-11-17-discord.md) distinguish real delivery from injected failure and source/mock coverage. No runtime code change, firewall change, new account permission, VirusTotal or blocking accompanied this connection.

## 2026-11-17 — Saved source checkpoint and deployed service controls/cleanup

Verified the existing local service, retention and optional Discord implementation. Fixed the Discord flush concurrency failure by keeping each run bounded to its initial queue snapshot; the existing regression now passes. Updated the shell smoke test's obsolete provider expectation. Saved the source and earlier VM evidence in commit `ecaec12` on `codex/service-cleanup-deployment`. Mac tests: 65 passed, one Ubuntu-only skip; blue's checksum-verified package: all 66 passed, plus shell/configuration and 19 monitor scenarios. Ubuntu accepted the resolved units.

Deployed a fresh `/home/bl47eheim/heimdall/releases/0.1.0-ecaec12/heimdall-0.1.0` release with the same owner and private state. Saved state/unit/launcher backups on blue, kept the old release, and switched the fixed monitor unit and owner launcher together. A first overly strict duplicate-reader verification assertion triggered a successful automatic code rollback; corrected the harness and repeated deployment. All 93 baseline events and both alerts/review histories were preserved.

Verified real service identity and healthy coverage, denied CLI/API start/stop without process fallback, administrator console stop/start, truthful stopped status and refusal of a manual reader outside the service. Enabled daily cleanup and observed its timer trigger plus successful service execution; next observed run was November 18 at 00:05:11 IST. The dashboard was started manually on the existing Host-Only address. Browser start/stop still requires administrator console action under existing Ubuntu policy; no broader authorization was added.

Used Computer Use for the blue/red consoles. The owner supplied console unlocks and administrator authentication. A temporary Python HTTP transfer on the existing Host-Only network avoided new packages, access credentials and network changes. Red sent one deliberate invalid-user password attempt with verified host checking; blue recorded the matching failure exactly once. Final state: 99 stored events, two unchanged alerts and healthy systemd coverage, with cleanup enabled and successful. See [full evidence](docs/verification/2026-11-17-deployment.md) for results and limits. This work does not establish either student's academic contribution, resolve faculty questions, enable real providers or implement blocking. No push or external message was sent.

## 2026-11-07 — Monitor boot startup and bounded automatic recovery

Following the owner's administrator authorization, installed the reviewed resolved service on blue as a root-owned mode-644 unit, running the monitor as `bl47eheim`. Stopped the manual process before starting the service. Used existing journal permissions without adding a group or running Heimdall as root.

Verified automatic replacement after SIGKILL: PID 5797 became 5909, restart count 1, with the same 73 events and two alerts. Repeated crashes reached the configured three-starts-per-minute limit; the journal reported start requests repeated too quickly, and Heimdall showed error/unavailable coverage. Reset the failure counter and restored the service.

Rebooted blue and completed a fresh console login. A changed boot ID and current-boot journal established automatic startup at 21:48:18 IST, PID 1101, before any manual monitor launch. Heimdall had available coverage, 77 events and two retained alerts. A fresh red-source failure was ingested after reboot, while the prior five-failure alert and review history remained intact. Restarted the separate dashboard manually and verified HTTP 200 from the Mac. Both VMs remain running; the monitor is enabled at boot, dashboard startup remains manual.

[Service verification](docs/verification/2026-11-07-systemd.md) records evidence and limitations. Current CLI/browser controls act directly on the monitor process rather than managing the service; use systemctl on blue until those controls are integrated. Updated the checklist, README, milestone status and runbook. No runtime source change, firewall/network change, student-contribution claim, Git commit or push accompanies this work. Credentials were not embedded in commands or saved evidence.

## 2026-11-07 — Real red-to-blue alerting and console recovery

The owner supplied both running VMs and authorized a live verification work package. Confirmed blue at `10.37.129.3` and red at `10.37.129.4`. Blue initially had a stopped monitor, unavailable coverage, 44 events and one preserved alert. Started the monitor and dashboard manually using the deployed 0.1.0 release.

Real controlled failures from red produced no alert at three and a new Medium alert at four. Reviewing that alert then sending a fifth failure reopened it with both review transitions retained. The previous Mac-source alert remained separate. Verified the monitor process identity, forced its crash and observed honest error/unavailable status. Restarted it from blue's console: 73 events, two alerts and the red count of five were preserved. Authenticated dashboard HTTP status and alert data agreed with the CLI. The monitor and dashboard were left running manually.

Prepared the service file with blue's actual paths and account; Ubuntu's `systemd-analyze verify` returned 0. Omitted an extra journal group because the account already has journal access. The unit remains uninstalled, and noninteractive sudo was unavailable. Administrator authentication, installation, automatic crash restart and reboot verification remain next. Manual console recovery does not establish recovery from a source block or fresh console login. No firewall, network, account-access or boot-service changes were made.

[Sanitized verification record](docs/verification/2026-11-07-red-blue-recovery.md) documents commands, results, limitations and private evidence paths on blue. No runtime source change, commit or push accompanies this work. The assistant executed the checks; student contributions and faculty questions remain unresolved.

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
