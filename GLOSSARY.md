# Heimdall

Heimdall helps an owner understand which security events merit attention. The current college milestone focuses on SSH login activity on a Linux system; the broader direction covers personal home systems.

## Security events

**Event**:
A timestamped observation emitted by a device or service, such as a failed login or configuration change.
_Avoid_: Alert, when referring to an individual source observation.

**Alert**:
A Heimdall finding that groups one or more events with a rule match and an explanation for the owner.
_Avoid_: Event, incident, case.

**Alert review status**:
Whether an alert needs review or has been reviewed by the owner. Reviewing an alert does not itself restore access to a blocked source.

**Indicator**:
A technical value that may help identify suspicious activity, such as an IP address, domain, URL, or file hash.
_Avoid_: IOC in user-facing copy; expand “indicator of compromise” when needed in technical documents.

**Rule**:
A named, versioned condition that matches event facts and explains why Heimdall raised an alert.
_Avoid_: Detection, when referring to the configured condition itself.

**Enrichment**:
Optional context looked up for a selected indicator from a local or external source.
_Avoid_: Verification; an external reputation result is one signal, not proof that an event is safe or malicious.

**Reputation label**:
A description of the available external reputation evidence for an indicator. It is distinct from an alert's severity and does not establish whether activity is safe or malicious.

**SSH source block**:
A restriction on further SSH connection attempts from a particular source address to the monitored system. It remains in place until explicitly removed and is separate from an alert's review status.

**Recommendation**:
A suggested next step that the owner can review and carry out.
_Avoid_: Response action, when Heimdall has not actually changed a device.
