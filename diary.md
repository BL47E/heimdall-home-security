# Heimdall development diary

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
