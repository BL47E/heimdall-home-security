# Heimdall checklist handoff

The [checklist](checklist.md) reflects the work on `main`. Tailscale address handling and the monitoring pause control are implemented in source. Linux deployment and live verification remain open.

1. **Deploy and check the dashboard and pause controls.** Install the updated services on Linux, verify startup after boot, test access from the personal computer over Tailscale, and check localhost fallback and address changes. Confirm that pausing skips SSH activity while Heimdall and the dashboard keep running.
2. **Finish live lab verification.** Test the Connections page with real SSH activity, check the dashboard from the Mac, and capture the remaining expired-window, concurrent-source and successful-login scenarios. Recheck the current VM network and observe the Discord sender after a reboot.
3. **Rehearse the demonstration.** Walk through an alert, investigation, restart and Discord notification recovery. Core detection and earlier Discord delivery have already been demonstrated, with further scenarios still open.
4. **Settle project decisions.** The SSH event format, exact rolling-window and replay behavior, durable recovery, and automated GitHub checks still have open decision issues. Replay means how Heimdall handles records it encounters again after a restart.
5. **Prepare the college submission.** Draft the proposal, Gantt chart and comparison with existing tools, gather evidence, record both students' contributions, and rehearse the presentation. The final report format, deadline, presentation duration and faculty acceptance of the dashboard technology remain unconfirmed.
6. **Decide how much SSH blocking to pursue.** Real blocking remains planned and is the last implementation priority. Its design review and console recovery test are still open. A live VirusTotal lookup is also optional and unverified.

See [implementation status](docs/status.md) for current evidence and limitations, and [evaluation alignment](docs/evaluation-alignment.md) for the unresolved faculty questions.
