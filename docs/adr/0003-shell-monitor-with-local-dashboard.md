# Shell monitor with a local browser dashboard

On 2026-11-04 the owner requested implementing the SSH monitor in shell and adding a browser dashboard for local alert review, monitoring control and configuration, extending ADR 0002's terminal-only management scope. Keep SSH message parsing, rule decisions and durable state changes in shell/jq, with a small Python standard-library helper for canonical IP validation and stable content fingerprints and an authenticated HTTP bridge to the shell commands; this avoids implementing IP parsing or an HTTP protocol in shell while preserving the course's shell implementation focus. Store records in private local files, keep offline sample processing useful without credentials, and require explicit local-address binding for trusted-LAN access; this decision authorizes no firewall changes, automatic deployment or port forwarding, and faculty acceptance of the expanded technology remains unconfirmed.


## Monitoring pause and dashboard lifecycle — 2026-11-26

The owner requested that stopping monitoring pause event processing while the service and dashboard remain running. Resuming begins a new coverage window and skips activity from the pause. The dashboard runs as a separate unprivileged systemd unit started with the monitor and stopped when that service is stopped. Source changes and unit templates require installation and live verification. Binding remains an explicit host choice.
