# Proposed SSH connection response design

Status: draft for owner review. No firewall or account changes are implemented by this document. The owner requested a connection detail view with a permanent block, a time-limited block measured in minutes, hours or days, a countdown, and a green/yellow/red assessment. The existing college milestone requires a separate response design review and tested VM-console recovery before real enforcement is activated.

## Scope and decisions

The current connection list observes established TCP connections to local port 22 and previously recorded successful password logins. Current connections do not reliably identify a username. A source IP can represent multiple users or devices. The proposed action target is the source IP. The owner asked to interrupt an existing SSH session and to base the assessment colors on VirusTotal reputation. The dashboard maps zero flags to green, 1–6 to yellow, and 7 or more to red; unknown remains gray. These colors summarize the existing vendor-count labels and do not prove safety or maliciousness. No classification should claim a connection is safe when evidence is missing.

A permanent block should remain active until the owner explicitly removes it. A timed block should expire at its recorded deadline. The countdown should use that deadline and show the actual enforcement result; reaching zero alone does not establish that a firewall rule was removed. The new timed expiry is an owner-requested extension to the milestone's indefinite-block behavior.

## Proposed source-IP approach, subject to the owner decision

Use a dedicated, narrowly scoped firewall component that targets inbound SSH only, supports both IPv4 and IPv6, and does not modify unrelated rules. Validate and canonicalize addresses before handing them to a privileged component. Keep the dashboard and terminal unprivileged; use a narrowly authorized helper with fixed operations and arguments. No shell command should be constructed from browser input.

Persist the source, action, start time, optional expiry, requested state, observed enforcement state, result and audit history. Serialize updates and recover from crashes or interrupted operations. Do not mark an action successful until the firewall confirms it. Reconcile persisted intent and actual firewall state at startup, including expired timed blocks and any downtime. Retention must preserve active blocks and their evidence. A failed block, removal or restoration must be visible and generate the urgent notification required by the milestone.

The interface should show the selected IP, explain that all SSH users from that IP are affected, and require an explicit action. Provide unblock with confirmation. Explain whether existing connections are affected after the firewall behavior is verified. New failures after an unblock must be counted separately from earlier failures, while preserving the earlier evidence. Review status must not change enforcement.

## Review and verification gates

1. Confirm the source-IP approach and review the VirusTotal color mapping. Verify a method for interrupting existing SSH sessions.
2. Choose the firewall backend and define ownership, ordering with existing rules, supported SSH ports, helper authorization and upgrade/removal behavior for the target Linux distribution.
3. Verify a fresh VM-console login and recovery path before enabling enforcement. Review the resolved configuration and obtain explicit owner approval before device or network changes.
4. Test IPv4 and IPv6 in isolated VMs, including unrelated traffic, retry and concurrent actions, crashes between state and firewall updates, reboot restoration, timed expiry during downtime, failed removal and manual unblock.
5. Test the real selected-session behavior and demonstrate that a blocked source cannot make the scoped SSH connection. Preserve honest status if enforcement cannot be verified.

For the Ubuntu VM, nftables timed sets are a candidate for enforcing expirations. A dedicated input chain could target only the configured SSH port and source IP, with IPv4 and IPv6 sets. The helper would separately attempt to terminate matching established SSH sockets and report its result. Chain priority, existing firewall compatibility, socket termination permissions, and recovery must be verified before approval. The final backend and ownership remain open. [nftables element timeouts](https://wiki.nftables.org/wiki-nftables/index.php/Element_timeouts)
